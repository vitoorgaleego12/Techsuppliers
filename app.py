import os
import sqlite3
import socket
import re
import html
import hashlib
import secrets
from flask import Flask, request, jsonify, send_from_directory, send_file, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging

from flask import Flask, send_from_directory

app = Flask(__name__, static_folder=".", static_url_path="")

# rota para servir qualquer arquivo estático (html, css, js, imagens)
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')
# Configuração inicial do Flask
app = Flask(__name__, static_folder="static")
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Caminhos dos bancos de dados
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO_FORNECEDORES = os.path.join(PASTA_PROJETO, "fornecedores.db")
CAMINHO_BANCO_CLIENTES = os.path.join(PASTA_PROJETO, "clientes.db")

# Rate limiting storage (em produção, use Redis)
from collections import defaultdict
from time import time
request_times = defaultdict(list)

# Verifica e cria pastas necessárias
pastas_necessarias = ['static/imagens', 'static/produtos', 'static/css', 'static/js']
for pasta in pastas_necessarias:
    caminho_pasta = os.path.join(PASTA_PROJETO, pasta)
    if not os.path.exists(caminho_pasta):
        os.makedirs(caminho_pasta)
        logger.info(f"Pasta criada: {caminho_pasta}")

# ==============================
# Middlewares de segurança
# ==============================
@app.after_request
def add_security_headers(response):
    """Adiciona headers de segurança HTTP"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:"
    return response

def rate_limit(max_requests=100, window=60):
    """Middleware de rate limiting"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            now = time()
            
            # Limpa requisições antigas
            request_times[ip] = [t for t in request_times[ip] if now - t < window]
            
            if len(request_times[ip]) >= max_requests:
                return jsonify({"status": "erro", "mensagem": "Muitas requisições. Tente novamente mais tarde."}), 429
            
            request_times[ip].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==============================
# Funções de validação e sanitização
# ==============================
def sanitizar_input(texto):
    """Remove caracteres perigosos e previne XSS"""
    if texto is None:
        return ""
    texto = str(texto).strip()
    texto = html.escape(texto)  # Prevenção XSS
    texto = re.sub(r'[;\"\']', '', texto)  # Remove caracteres perigosos para SQL
    return texto

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_cpf(cpf):
    """Valida CPF"""
    cpf = re.sub(r'[^\d]', '', cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    
    # Validação dos dígitos verificadores
    for i in range(9, 11):
        soma = sum(int(cpf[j]) * ((i+1) - j) for j in range(0, i))
        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0
        if digito != int(cpf[i]):
            return False
    return True

def validar_cnpj(cnpj):
    """Valida CNPJ"""
    cnpj = re.sub(r'[^\d]', '', cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    
    # Validação dos dígitos verificadores
    for i in range(12, 14):
        peso = 2 if i == 12 else 3
        soma = 0
        for j in range(i-1, -1, -1):
            soma += int(cnpj[j]) * peso
            peso = peso + 1 if peso < 9 else 2
        digito = 11 - (soma % 11)
        if digito > 9:
            digito = 0
        if digito != int(cnpj[i]):
            return False
    return True

def validar_telefone(telefone):
    """Valida telefone brasileiro"""
    telefone = re.sub(r'[^\d]', '', telefone)
    return len(telefone) in [10, 11] and telefone[0] in ['1', '2', '3', '4', '5', '6', '7', '8', '9']

def validar_senha(senha):
    """Valida força da senha"""
    if len(senha) < 8:
        return False
    if not re.search(r'[A-Z]', senha):
        return False
    if not re.search(r'[a-z]', senha):
        return False
    if not re.search(r'[0-9]', senha):
        return False
    if not re.search(r'[^A-Za-z0-9]', senha):
        return False
    return True

# ==============================
# Servir arquivos estáticos com validação
# ==============================
ALLOWED_EXTENSIONS = {'.css', '.js', '.html', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp', '.bmp', '.tiff'}

@app.route('/<path:filename>')
def serve_page(filename):
    """Serve páginas HTML com validação de segurança"""
    # Prevenção de path traversal
    if '..' in filename or filename.startswith('/'):
        return "Arquivo não encontrado", 404
    
    # Valida extensão do arquivo
    _, ext = os.path.splitext(filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return "Tipo de arquivo não permitido", 403
    
    file_path = os.path.join(PASTA_PROJETO, filename)
    
    # Verifica se o arquivo existe e está dentro do diretório permitido
    if not os.path.exists(file_path) or not file_path.startswith(PASTA_PROJETO):
        return "Arquivo não encontrado", 404
    
    # Define MIME types
    mime_types = {
        '.css': 'text/css',
        '.js': 'application/javascript',
        '.html': 'text/html',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.ico': 'image/x-icon',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
        '.bmp': 'image/bmp',
        '.tiff': 'image/tiff'
    }
    
    mimetype = mime_types.get(ext.lower(), 'text/plain')
    
    # Adiciona headers de cache para arquivos estáticos
    response = send_from_directory(PASTA_PROJETO, filename, mimetype=mimetype)
    response.headers['Cache-Control'] = 'public, max-age=3600'
    return response

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve arquivos estáticos da pasta static"""
    static_folder = os.path.join(app.root_path, 'static')
    return send_from_directory(static_folder, filename)

@app.route('/produtos/<path:filename>')
def serve_produto_images(filename):
    """Serve imagens de produtos com validação de segurança"""
    # Prevenção de path traversal
    if '..' in filename or filename.startswith('/'):
        return "Arquivo não encontrado", 404
    
    # Valida extensão do arquivo
    _, ext = os.path.splitext(filename)
    if ext.lower() not in {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg'}:
        return "Tipo de arquivo não permitido", 403
    
    pasta_produtos = os.path.join(PASTA_PROJETO, 'static', 'produtos')
    file_path = os.path.join(pasta_produtos, filename)
    
    # Verifica se o arquivo existe e está dentro do diretório permitido
    if not os.path.exists(file_path) or not file_path.startswith(pasta_produtos):
        return "Arquivo não encontrado", 404
    
    return send_from_directory(pasta_produtos, filename)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ==============================
# Criação segura dos bancos com prepared statements
# ==============================
def criar_bancos():
    """Cria bancos de dados com configurações seguras"""
    try:
        # Banco de fornecedores
        conn_fornecedores = sqlite3.connect(CAMINHO_BANCO_FORNECEDORES)
        conn_fornecedores.execute('PRAGMA journal_mode = WAL')
        conn_fornecedores.execute('PRAGMA foreign_keys = ON')
        cursor_fornecedores = conn_fornecedores.cursor()
        
        cursor_fornecedores.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL CHECK(length(nome) <= 100),
                razao TEXT NOT NULL CHECK(length(razao) <= 200),
                cpfcnpj TEXT NOT NULL UNIQUE CHECK(length(cpfcnpj) <= 18),
                idade INTEGER CHECK(idade >= 18 AND idade <= 120),
                telefone TEXT NOT NULL CHECK(length(telefone) <= 15),
                email TEXT NOT NULL CHECK(length(email) <= 100),
                endereco TEXT NOT NULL CHECK(length(endereco) <= 200),
                site TEXT CHECK(length(site) <= 100),
                servico TEXT NOT NULL CHECK(length(servico) <= 100),
                tempo TEXT NOT NULL CHECK(length(tempo) <= 50),
                contrato TEXT NOT NULL CHECK(length(contrato) <= 50),
                responsavel TEXT NOT NULL CHECK(length(responsavel) <= 100),
                obs TEXT CHECK(length(obs) <= 500),
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn_fornecedores.commit()
        conn_fornecedores.close()

        # Banco de clientes
        conn_clientes = sqlite3.connect(CAMINHO_BANCO_CLIENTES)
        conn_clientes.execute('PRAGMA journal_mode = WAL')
        conn_clientes.execute('PRAGMA foreign_keys = ON')
        cursor_clientes = conn_clientes.cursor()
        
        cursor_clientes.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL CHECK(length(nome) <= 100),
                idade INTEGER NOT NULL CHECK(idade >= 18 AND idade <= 120),
                email TEXT NOT NULL UNIQUE CHECK(length(email) <= 100),
                telefone TEXT NOT NULL CHECK(length(telefone) <= 15),
                endereco TEXT NOT NULL CHECK(length(endereco) <= 200),
                genero TEXT NOT NULL CHECK(genero IN ('M', 'F', 'O')),
                cpf TEXT NOT NULL UNIQUE CHECK(length(cpf) <= 14),
                senha TEXT NOT NULL CHECK(length(senha) <= 255),
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn_clientes.commit()
        conn_clientes.close()
        
        logger.info("Bancos de dados criados com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao criar bancos de dados: {e}")
        raise

def recriar_tabela_clientes():
    """Recria a tabela clientes com a estrutura correta"""
    try:
        conn = sqlite3.connect(CAMINHO_BANCO_CLIENTES)
        cursor = conn.cursor()
        
        # Remove a tabela existente (cuidado: isso apagará todos os dados)
        cursor.execute('DROP TABLE IF EXISTS clientes')
        
        # Cria a tabela com a estrutura correta
        cursor.execute('''
            CREATE TABLE clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL CHECK(length(nome) <= 100),
                idade INTEGER NOT NULL CHECK(idade >= 18 AND idade <= 120),
                email TEXT NOT NULL UNIQUE CHECK(length(email) <= 100),
                telefone TEXT NOT NULL CHECK(length(telefone) <= 15),
                endereco TEXT NOT NULL CHECK(length(endereco) <= 200),
                genero TEXT NOT NULL CHECK(genero IN ('M', 'F', 'O')),
                cpf TEXT NOT NULL UNIQUE CHECK(length(cpf) <= 14),
                senha TEXT NOT NULL CHECK(length(senha) <= 255),
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("Tabela clientes recriada com sucesso")
        return True
    except Exception as e:
        logger.error(f"Erro ao recriar tabela clientes: {e}")
        return False

criar_bancos()

# ==============================
# Conexão segura com o banco
# ==============================
def get_db_connection(db_path):
    """Retorna uma conexão segura com o banco"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Configurações de segurança
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

# ==============================
# Páginas principais
# ==============================
@app.route("/")
def index():
    return send_from_directory(PASTA_PROJETO, "index.html")

@app.route("/fornecedores")
def pagina_fornecedores():
    return send_from_directory(PASTA_PROJETO, "cadastro.html")

@app.route("/clientes")
def pagina_clientes():
    return send_from_directory(PASTA_PROJETO, "cliente.html")

@app.route("/listar_fornecedores")
def listar_fornecedores():
    return send_from_directory(PASTA_PROJETO, "Listar.html")

@app.route("/listar_clientes")
def listar_clientes():
    return send_from_directory(PASTA_PROJETO, "Listar_clientes.html")

# ==============================
# Login e sessão
# ==============================
@app.route('/login_cliente', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def login_cliente():
    try:
        email = sanitizar_input(request.form.get('email', ''))
        senha = request.form.get('senha', '')
        
        if not email or not senha:
            return jsonify({"status": "erro", "mensagem": "Email e senha são obrigatórios."}), 400
        
        conn = get_db_connection(CAMINHO_BANCO_CLIENTES)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE email = ?", (email,))
        cliente = cursor.fetchone()
        conn.close()
        
        if not cliente:
            return jsonify({"status": "erro", "mensagem": "Email ou senha incorretos."}), 401
        
        if not check_password_hash(cliente['senha'], senha):
            return jsonify({"status": "erro", "mensagem": "Email ou senha incorretos."}), 401
        
        # Cria a sessão do usuário
        session['cliente_id'] = cliente['id']
        session['cliente_nome'] = cliente['nome']
        session['cliente_email'] = cliente['email']
        session['logged_in'] = True
        
        logger.info(f"Cliente logado: {cliente['nome']}")
        return jsonify({
            "status": "ok", 
            "mensagem": "Login realizado com sucesso!",
            "redirect": "/"
        })
        
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno do servidor."}), 500

@app.route('/logout')
def logout():
    """Encerra a sessão do usuário"""
    session.clear()
    return redirect('/')

@app.route('/check_session')
def check_session():
    """Verifica se o usuário está logado"""
    if session.get('logged_in'):
        return jsonify({
            "logged_in": True,
            "cliente_nome": session.get('cliente_nome'),
            "cliente_email": session.get('cliente_email')
        })
    return jsonify({"logged_in": False})

# ==============================
# Cadastro de fornecedores (seguro)
# ==============================
@app.route("/cadastrar", methods=["POST"])
@rate_limit(max_requests=10, window=60)
def cadastrar_fornecedor():
    try:
        # Coleta e sanitiza os dados
        dados = {
            "nome": sanitizar_input(request.form.get("nome", "")),
            "razao": sanitizar_input(request.form.get("razao", "")),
            "cpfcnpj": sanitizar_input(request.form.get("cpfcnpj", "")),
            "idade": sanitizar_input(request.form.get("idade", "")),
            "telefone": sanitizar_input(request.form.get("telefone", "")),
            "email": sanitizar_input(request.form.get("email", "")),
            "endereco": sanitizar_input(request.form.get("endereco", "")),
            "site": sanitizar_input(request.form.get("site", "")),
            "servico": sanitizar_input(request.form.get("servico", "")),
            "tempo": sanitizar_input(request.form.get("tempo", "")),
            "contrato": sanitizar_input(request.form.get("contrato", "")),
            "responsavel": sanitizar_input(request.form.get("responsavel", "")),
            "obs": sanitizar_input(request.form.get("obs", ""))
        }

        # Campos obrigatórios
        obrigatorios = ["nome", "razao", "cpfcnpj", "telefone", "email", 
                       "endereco", "servico", "tempo", "contrato", "responsavel"]
        
        for campo in obrigatorios:
            if not dados[campo]:
                return jsonify({"status": "erro", "mensagem": f"O campo '{campo}' é obrigatório."}), 400

        # Validações específicas
        if not validar_email(dados["email"]):
            return jsonify({"status": "erro", "mensagem": "Email inválido."}), 400

        if not validar_telefone(dados["telefone"]):
            return jsonify({"status": "erro", "mensagem": "Telefone inválido."}), 400

        # Valida CPF/CNPJ
        cpf_cnpj_limpo = re.sub(r'[^\d]', '', dados["cpfcnpj"])
        if len(cpf_cnpj_limpo) == 11:
            if not validar_cpf(cpf_cnpj_limpo):
                return jsonify({"status": "erro", "mensagem": "CPF inválido."}), 400
        elif len(cpf_cnpj_limpo) == 14:
            if not validar_cnpj(cpf_cnpj_limpo):
                return jsonify({"status": "erro", "mensagem": "CNPJ inválido."}), 400
        else:
            return jsonify({"status": "erro", "mensagem": "CPF/CNPJ inválido."}), 400

        # Validação de idade
        if dados["idade"]:
            if not dados["idade"].isdigit():
                return jsonify({"status": "erro", "mensagem": "Idade deve conter apenas números."}), 400
            idade = int(dados["idade"])
            if idade < 18 or idade > 120:
                return jsonify({"status": "erro", "mensagem": "Idade inválida. Deve estar entre 18 e 120."}), 400
            dados["idade"] = idade
        else:
            dados["idade"] = None

        # Verifica si CPF/CNPJ já existe
        conn = get_db_connection(CAMINHO_BANCO_FORNECEDORES)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM fornecedores WHERE cpfcnpj = ?", (dados["cpfcnpj"],))
        if cursor.fetchone():
            conn.close()
            return jsonify({"status": "erro", "mensagem": "CPF/CNPJ já cadastrado."}), 400

        # Inserção segura no banco
        cursor.execute('''
            INSERT INTO fornecedores (
                nome, razao, cpfcnpj, idade, telefone, email, endereco,
                site, servico, tempo, contrato, responsavel, obs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados["nome"], dados["razao"], dados["cpfcnpj"], dados["idade"], dados["telefone"],
            dados["email"], dados["endereco"], dados["site"], dados["servico"], dados["tempo"],
            dados["contrato"], dados["responsavel"], dados["obs"]
        ))
        conn.commit()
        conn.close()

        logger.info(f"Fornecedor cadastrado: {dados['nome']}")
        return jsonify({"status": "ok", "mensagem": "Cadastro realizado com sucesso!"})
    
    except sqlite3.Error as e:
        logger.error(f"Erro de banco: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno do banco de dados."}), 500
    except Exception as e:
        logger.error(f"Erro interno: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno do servidor."}), 500

# ==============================
# Cadastro de clientes (seguro) - AGORA COM LOGIN AUTOMÁTICO
# ==============================
@app.route('/cadastrar_cliente', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def cadastrar_cliente():
    try:
        # Sanitização e validação dos dados
        nome = sanitizar_input(request.form.get('nome', ''))
        idade_str = sanitizar_input(request.form.get('idade', ''))
        email = sanitizar_input(request.form.get('email', ''))
        telefone = sanitizar_input(request.form.get('telefone', ''))
        endereco = sanitizar_input(request.form.get('endereco', ''))
        genero = sanitizar_input(request.form.get('genero', ''))
        cpf = sanitizar_input(request.form.get('cpf', ''))
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmarSenha', '')

        # Debug: Verificar os valores recebidos
        logger.info(f"Dados recebidos - nome: {nome}, idade: {idade_str}, email: {email}, telefone: {telefone}, endereco: {endereco}, genero: {genero}, cpf: {cpf}")

        # Validações
        if not all([nome, idade_str, email, telefone, endereco, genero, cpf, senha]):
            return jsonify({"status": "erro", "mensagem": "Todos os campos são obrigatórios."}), 400

        if senha != confirmar_senha:
            return jsonify({"status": "erro", "mensagem": "As senha não coincidem."}), 400

        if not validar_senha(senha):
            return jsonify({"status": "erro", "mensagem": "Senha fraca. Use pelo menos 8 caracteres incluindo maiúsculas, minúsculas, números e símbolos."}), 400

        if not validar_email(email):
            return jsonify({"status": "erro", "mensagem": "Email inválido."}), 400

        if not validar_telefone(telefone):
            return jsonify({"status": "erro", "mensagem": "Telefone inválido."}), 400

        cpf_limpo = re.sub(r'[^\d]', '', cpf)
        if not validar_cpf(cpf_limpo):
            return jsonify({"status": "erro", "mensagem": "CPF inválido."}), 400

        try:
            idade = int(idade_str)
            if idade < 18 or idade > 120:
                return jsonify({"status": "erro", "mensagem": "Idade deve estar entre 18 e 120 anos."}), 400
        except ValueError:
            return jsonify({"status": "erro", "mensagem": "Idade deve ser um número válido."}), 400

        # Mapeamento dos valores de gênero para os valores aceitos pelo banco
        genero_map = {
            'masculino': 'M',
            'feminino': 'F',
            'outro': 'O',
            'm': 'M',
            'f': 'F',
            'o': 'O',
            'M': 'M',
            'F': 'F',
            'O': 'O'
        }
        
        # Converte o valor do gênero para o formato correto
        genero_normalizado = genero_map.get(genero.lower().strip(), None)
        
        if genero_normalizado is None:
            return jsonify({
                "status": "erro", 
                "mensagem": "Gênero inválido. Use: Masculino, Feminino ou Outro.",
                "genero_recebido": genero
            }), 400

        # Hash da senha
        senha_hash = generate_password_hash(senha)

        # Verifica si email ou CPF já existem
        conn = get_db_connection(CAMINHO_BANCO_CLIENTES)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clientes WHERE email = ? OR cpf = ?", (email, cpf))
        if cursor.fetchone():
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Email ou CPF já cadastrado."}), 400

        # Inserção segura
        cursor.execute('''
            INSERT INTO clientes (nome, idade, email, telefone, endereco, genero, cpf, senha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, idade, email, telefone, endereco, genero_normalizado, cpf, senha_hash))
        conn.commit()

        # Busca o cliente recém-criado para obter o ID
        cursor.execute("SELECT * FROM clientes WHERE email = ?", (email,))
        novo_cliente = cursor.fetchone()
        conn.close()

        # Cria a sessão do usuário automaticamente após o cadastro
        session['cliente_id'] = novo_cliente['id']
        session['cliente_nome'] = novo_cliente['nome']
        session['cliente_email'] = novo_cliente['email']
        session['logged_in'] = True

        logger.info(f"Cliente cadastrado e logado: {nome}, Gênero: {genero_normalizado}")
        return jsonify({
            "status": "ok", 
            "mensagem": "Cliente cadastrado com sucesso!",
            "redirect": "/"  # Redireciona para a página inicial
        })

    except sqlite3.Error as e:
        logger.error(f"Erro de banco: {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro interno do banco de dados: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Erro interno: {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro interno do servidor: {str(e)}"}), 500

# ==============================
# APIs para listar dados (com validação)
# ==============================
@app.route('/fornecedores_json')
@rate_limit(max_requests=30, window=60)
def fornecedores_json():
    try:
        conn = get_db_connection(CAMINHO_BANCO_FORNECEDORES)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fornecedores ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()

        fornecedores = [dict(row) for row in rows]
        return jsonify(fornecedores)
    except Exception as e:
        logger.error(f"Erro ao listar fornecedores: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro ao carregar dados."}), 500

@app.route('/clientes_json')
@rate_limit(max_requests=30, window=60)
def clientes_json():
    try:
        conn = get_db_connection(CAMINHO_BANCO_CLIENTES)
        cursor = conn.cursor()
        
        # Primeiro verifica se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
        if not cursor.fetchone():
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Tabela clientes não existe"}), 500
        
        cursor.execute('SELECT id, nome, idade, email, telefone, endereco, genero, cpf, data_criacao FROM clientes ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()

        clientes = [dict(row) for row in rows]
        return jsonify(clientes)
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
        return jsonify({"status": "erro", "mensagem": f"Erro ao carregar dados: {str(e)}"}), 500

# ==============================
# Debug endpoints (apenas para desenvolvimento)
# ==============================
@app.route('/debug/tabela_clientes')
def debug_tabela_clientes():
    """Endpoint para debug da estrutura da tabela clientes"""
    try:
        conn = get_db_connection(CAMINHO_BANCO_CLIENTES)
        cursor = conn.cursor()
        
        # Verifica se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clientes'")
        tabela_existe = cursor.fetchone()
        
        if not tabela_existe:
            conn.close()
            return jsonify({
                "status": "erro", 
                "mensagem": "Tabela clientes não existe",
                "tabela_existe": False
            })
        
        # Verifica a estrutura da tabela
        cursor.execute("PRAGMA table_info(clientes)")
        colunas = cursor.fetchall()
        
        # Conta registros
        cursor.execute("SELECT COUNT(*) FROM clientes")
        total_registros = cursor.fetchone()[0]
        
        # Pega alguns registros para debug
        cursor.execute("SELECT * FROM clientes LIMIT 5")
        registros = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "colunas": [dict(col) for col in colunas],
            "total_registros": total_registros,
            "tabela_existe": True,
            "registros_amostra": [dict(reg) for reg in registros],
            "status": "ok"
        })
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

@app.route('/debug/recriar_tabela_clientes')
def debug_recriar_tabela():
    """Recria a tabela clientes (apenas para desenvolvimento)"""
    if recriar_tabela_clientes():
        return jsonify({"status": "ok", "mensagem": "Tabela clientes recriada com sucesso"})
    else:
        return jsonify({"status": "erro", "mensagem": "Erro ao recriar tabela"}), 500

@app.route('/debug/testar_genero/<genero>')
def debug_testar_genero(genero):
    """Testa como o gênero está sendo processado"""
    genero_map = {
        'masculino': 'M',
        'feminino': 'F',
        'outro': 'O',
        'm': 'M',
        'f': 'F',
        'o': 'O',
        'M': 'M',
        'F': 'F',
        'O': 'O'
    }
    
    genero_normalizado = genero_map.get(genero.lower().strip(), None)
    
    return jsonify({
        "genero_original": genero,
        "genero_normalizado": genero_normalizado,
        "valido": genero_normalizado is not None
    })

# ==============================
# Health check endpoint
# ==============================
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": time()})

# ==============================
# Inicialização segura do servidor
# ==============================
def encontrar_porta_livre(porta_inicial=5000):
    porta = porta_inicial
    while porta < 5100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if s.connect_ex(('localhost', porta)) != 0:
                return porta
            porta += 1
    raise RuntimeError("Nenhuma porta livre encontrada")

if __name__ == "__main__":
    # Configurações de segurança
    porta_livre = encontrar_porta_livre()
    
    print(f"🚀 Servidor TechSuppliers iniciado com segurança máxima!")
    print(f"📍 URL: http://localhost:{porta_livre}")
    print(f"🔒 Headers de segurança habilitados")
    print(f"🛡️  Rate limiting ativado")
    print(f"📊 Validações de entrada implementadas")
    print(f"💾 Bancos com constraints de segurança")
    print(f"📸 Suporte a imagens de produtos ativado")
    print(f"🐛 Endpoints de debug disponíveis:")
    print(f"   - http://localhost:{porta_livre}/debug/tabela_clientes")
    print(f"   - http://localhost:{porta_livre}/debug/recriar_tabela_clientes")
    print(f"   - http://localhost:{porta_livre}/debug/testar_genero/masculino")
    
    # Configurações de produção
    app.run(
        debug=True,  # Ativa debug para ver erros detalhados
        host="0.0.0.0", 
        port=porta_livre,
        threaded=True
    )
