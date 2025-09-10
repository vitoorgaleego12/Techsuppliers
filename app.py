import os
import psycopg2
import socket
import re
import html
import secrets
from flask import Flask, request, jsonify, send_from_directory, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do PostgreSQL para Render
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")

# Rate limiting storage
from collections import defaultdict
from time import time
request_times = defaultdict(list)

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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
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
    texto = html.escape(texto)
    texto = re.sub(r'[;\"\']', '', texto)
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
# Conexão com PostgreSQL
# ==============================
def get_db_connection():
    """Retorna uma conexão com o PostgreSQL"""
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def criar_tabelas():
    """Cria as tabelas no PostgreSQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Tabela de fornecedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                razao VARCHAR(200) NOT NULL,
                cpfcnpj VARCHAR(18) NOT NULL UNIQUE,
                idade INTEGER CHECK(idade >= 18 AND idade <= 120),
                telefone VARCHAR(15) NOT NULL,
                email VARCHAR(100) NOT NULL,
                endereco VARCHAR(200) NOT NULL,
                site VARCHAR(100),
                servico VARCHAR(100) NOT NULL,
                tempo VARCHAR(50) NOT NULL,
                contrato VARCHAR(50) NOT NULL,
                responsavel VARCHAR(100) NOT NULL,
                obs TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                idade INTEGER NOT NULL CHECK(idade >= 18 AND idade <= 120),
                email VARCHAR(100) NOT NULL UNIQUE,
                telefone VARCHAR(15) NOT NULL,
                endereco VARCHAR(200) NOT NULL,
                genero CHAR(1) NOT NULL CHECK(genero IN ('M', 'F', 'O')),
                cpf VARCHAR(14) NOT NULL UNIQUE,
                senha VARCHAR(255) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Tabelas criadas com sucesso")
        
    except Exception as e:
        logger.error(f"Erro ao criar tabelas: {e}")
        raise

# Criar tabelas ao iniciar
criar_tabelas()

# ==============================
# Servir arquivos estáticos
# ==============================
ALLOWED_EXTENSIONS = {'.css', '.js', '.html', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg'}

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve arquivos estáticos com validação"""
    if '..' in filename or filename.startswith('/'):
        return "Arquivo não encontrado", 404
    
    _, ext = os.path.splitext(filename)
    if ext.lower() not in ALLOWED_EXTENSIONS:
        return "Tipo de arquivo não permitido", 403
    
    return send_from_directory('.', filename)

# ==============================
# Páginas principais
# ==============================
@app.route("/fornecedores")
def pagina_fornecedores():
    return send_from_directory('.', "cadastro.html")

@app.route("/clientes")
def pagina_clientes():
    return send_from_directory('.', "cliente.html")

@app.route("/listar_fornecedores")
def listar_fornecedores():
    return send_from_directory('.', "Listar.html")

@app.route("/listar_clientes")
def listar_clientes():
    return send_from_directory('.', "Listar_clientes.html")

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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE email = %s", (email,))
        cliente = cursor.fetchone()
        conn.close()
        
        if not cliente:
            return jsonify({"status": "erro", "mensagem": "Email ou senha incorretos."}), 401
        
        if not check_password_hash(cliente[8], senha):  # senha está na posição 8
            return jsonify({"status": "erro", "mensagem": "Email ou senha incorretos."}), 401
        
        session['cliente_id'] = cliente[0]
        session['cliente_nome'] = cliente[1]
        session['cliente_email'] = cliente[3]
        session['logged_in'] = True
        
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
    session.clear()
    return redirect('/')

@app.route('/check_session')
def check_session():
    if session.get('logged_in'):
        return jsonify({
            "logged_in": True,
            "cliente_nome": session.get('cliente_nome'),
            "cliente_email": session.get('cliente_email')
        })
    return jsonify({"logged_in": False})

# ==============================
# Cadastro de fornecedores
# ==============================
@app.route("/cadastrar", methods=["POST"])
@rate_limit(max_requests=10, window=60)
def cadastrar_fornecedor():
    try:
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

        obrigatorios = ["nome", "razao", "cpfcnpj", "telefone", "email", 
                       "endereco", "servico", "tempo", "contrato", "responsavel"]
        
        for campo in obrigatorios:
            if not dados[campo]:
                return jsonify({"status": "erro", "mensagem": f"O campo '{campo}' é obrigatório."}), 400

        if not validar_email(dados["email"]):
            return jsonify({"status": "erro", "mensagem": "Email inválido."}), 400

        if not validar_telefone(dados["telefone"]):
            return jsonify({"status": "erro", "mensagem": "Telefone inválido."}), 400

        cpf_cnpj_limpo = re.sub(r'[^\d]', '', dados["cpfcnpj"])
        if len(cpf_cnpj_limpo) == 11:
            if not validar_cpf(cpf_cnpj_limpo):
                return jsonify({"status": "erro", "mensagem": "CPF inválido."}), 400
        elif len(cpf_cnpj_limpo) == 14:
            if not validar_cnpj(cpf_cnpj_limpo):
                return jsonify({"status": "erro", "mensagem": "CNPJ inválido."}), 400
        else:
            return jsonify({"status": "erro", "mensagem": "CPF/CNPJ inválido."}), 400

        if dados["idade"]:
            if not dados["idade"].isdigit():
                return jsonify({"status": "erro", "mensagem": "Idade deve conter apenas números."}), 400
            idade = int(dados["idade"])
            if idade < 18 or idade > 120:
                return jsonify({"status": "erro", "mensagem": "Idade inválida."}), 400
            dados["idade"] = idade
        else:
            dados["idade"] = None

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM fornecedores WHERE cpfcnpj = %s", (dados["cpfcnpj"],))
        if cursor.fetchone():
            conn.close()
            return jsonify({"status": "erro", "mensagem": "CPF/CNPJ já cadastrado."}), 400

        cursor.execute('''
            INSERT INTO fornecedores (nome, razao, cpfcnpj, idade, telefone, email, endereco,
                site, servico, tempo, contrato, responsavel, obs)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            dados["nome"], dados["razao"], dados["cpfcnpj"], dados["idade"], dados["telefone"],
            dados["email"], dados["endereco"], dados["site"], dados["servico"], dados["tempo"],
            dados["contrato"], dados["responsavel"], dados["obs"]
        ))
        conn.commit()
        conn.close()

        return jsonify({"status": "ok", "mensagem": "Cadastro realizado com sucesso!"})
    
    except Exception as e:
        logger.error(f"Erro ao cadastrar fornecedor: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno do servidor."}), 500

# ==============================
# Cadastro de clientes
# ==============================
@app.route('/cadastrar_cliente', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def cadastrar_cliente():
    try:
        nome = sanitizar_input(request.form.get('nome', ''))
        idade_str = sanitizar_input(request.form.get('idade', ''))
        email = sanitizar_input(request.form.get('email', ''))
        telefone = sanitizar_input(request.form.get('telefone', ''))
        endereco = sanitizar_input(request.form.get('endereco', ''))
        genero = sanitizar_input(request.form.get('genero', ''))
        cpf = sanitizar_input(request.form.get('cpf', ''))
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmarSenha', '')

        if not all([nome, idade_str, email, telefone, endereco, genero, cpf, senha]):
            return jsonify({"status": "erro", "mensagem": "Todos os campos são obrigatórios."}), 400

        if senha != confirmar_senha:
            return jsonify({"status": "erro", "mensagem": "As senhas não coincidem."}), 400

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

        genero_map = {'masculino': 'M', 'feminino': 'F', 'outro': 'O', 'm': 'M', 'f': 'F', 'o': 'O'}
        genero_normalizado = genero_map.get(genero.lower().strip(), None)
        
        if genero_normalizado is None:
            return jsonify({"status": "erro", "mensagem": "Gênero inválido."}), 400

        senha_hash = generate_password_hash(senha)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clientes WHERE email = %s OR cpf = %s", (email, cpf))
        if cursor.fetchone():
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Email ou CPF já cadastrado."}), 400

        cursor.execute('''
            INSERT INTO clientes (nome, idade, email, telefone, endereco, genero, cpf, senha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (nome, idade, email, telefone, endereco, genero_normalizado, cpf, senha_hash))
        conn.commit()

        cursor.execute("SELECT * FROM clientes WHERE email = %s", (email,))
        novo_cliente = cursor.fetchone()
        conn.close()

        session['cliente_id'] = novo_cliente[0]
        session['cliente_nome'] = novo_cliente[1]
        session['cliente_email'] = novo_cliente[3]
        session['logged_in'] = True

        return jsonify({
            "status": "ok", 
            "mensagem": "Cliente cadastrado com sucesso!",
            "redirect": "/"
        })

    except Exception as e:
        logger.error(f"Erro ao cadastrar cliente: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno do servidor."}), 500

# ==============================
# APIs para listar dados
# ==============================
@app.route('/fornecedores_json')
@rate_limit(max_requests=30, window=60)
def fornecedores_json():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM fornecedores ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()

        fornecedores = []
        for row in rows:
            fornecedores.append({
                'id': row[0],
                'nome': row[1],
                'razao': row[2],
                'cpfcnpj': row[3],
                'idade': row[4],
                'telefone': row[5],
                'email': row[6],
                'endereco': row[7],
                'site': row[8],
                'servico': row[9],
                'tempo': row[10],
                'contrato': row[11],
                'responsavel': row[12],
                'obs': row[13],
                'data_criacao': row[14]
            })
        return jsonify(fornecedores)
    except Exception as e:
        logger.error(f"Erro ao listar fornecedores: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro ao carregar dados."}), 500

@app.route('/clientes_json')
@rate_limit(max_requests=30, window=60)
def clientes_json():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nome, idade, email, telefone, endereco, genero, cpf, data_criacao FROM clientes ORDER BY id DESC')
        rows = cursor.fetchall()
        conn.close()

        clientes = []
        for row in rows:
            clientes.append({
                'id': row[0],
                'nome': row[1],
                'idade': row[2],
                'email': row[3],
                'telefone': row[4],
                'endereco': row[5],
                'genero': row[6],
                'cpf': row[7],
                'data_criacao': row[8]
            })
        return jsonify(clientes)
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro ao carregar dados."}), 500

# ==============================
# Health check
# ==============================
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

# ==============================
# Inicialização
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)        )
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar com o banco: {e}")
        return None

# ==============================
# Middlewares de segurança
# ==============================
@app.after_request
def add_security_headers(response):
    """Adiciona headers de segurança HTTP"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Configura cookies seguros
    if 'Set-Cookie' in response.headers:
        cookies = response.headers['Set-Cookie']
        if 'HttpOnly' not in cookies:
            cookies += '; HttpOnly'
        if 'Secure' not in cookies:
            cookies += '; Secure'
        response.headers['Set-Cookie'] = cookies
    
    return response

def rate_limit(max_requests=100, window=60):
    """Middleware de rate limiting simplificado"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            now = time()
            
            # Limpa requisições antigas
            if ip in request_times:
                request_times[ip] = [t for t in request_times[ip] if now - t < window]
            else:
                request_times[ip] = []
            
            if len(request_times[ip]) >= max_requests:
                return jsonify({"status": "erro", "mensagem": "Muitas requisições. Tente novamente mais tarde."}), 429
            
            request_times[ip].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==============================
# Funções de validação
# ==============================
def sanitizar_input(texto):
    """Remove caracteres perigosos"""
    if texto is None:
        return ""
    texto = str(texto).strip()
    texto = html.escape(texto)
    return texto

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_telefone(telefone):
    """Valida telefone brasileiro"""
    telefone = re.sub(r'[^\d]', '', telefone)
    return len(telefone) in [10, 11]

# ==============================
# Criação do banco de dados
# ==============================
def criar_bancos():
    """Cria bancos de dados"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        
        # Tabela de fornecedores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fornecedores (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                razao VARCHAR(200) NOT NULL,
                cpfcnpj VARCHAR(18) NOT NULL UNIQUE,
                telefone VARCHAR(15) NOT NULL,
                email VARCHAR(100) NOT NULL,
                endereco VARCHAR(200) NOT NULL,
                servico VARCHAR(100) NOT NULL,
                tempo VARCHAR(50) NOT NULL,
                contrato VARCHAR(50) NOT NULL,
                responsavel VARCHAR(100) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(100) NOT NULL,
                idade INTEGER NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                telefone VARCHAR(15) NOT NULL,
                endereco VARCHAR(200) NOT NULL,
                genero CHAR(1) NOT NULL,
                cpf VARCHAR(14) NOT NULL UNIQUE,
                senha VARCHAR(255) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Bancos de dados criados com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao criar bancos de dados: {e}")
        return False

# ==============================
# Servir arquivos estáticos
# ==============================
@app.route('/')
def index():
    return send_from_directory('.', "index.html")

@app.route("/fornecedores")
def pagina_fornecedores():
    return send_from_directory('.', "cadastro.html")

@app.route("/clientes")
def pagina_clientes():
    return send_from_directory('.', "cliente.html")

@app.route("/listar_fornecedores")
def listar_fornecedores():
    return send_from_directory('.', "Listar.html")

@app.route("/listar_clientes")
def listar_clientes():
    return send_from_directory('.', "Listar_clientes.html")

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve arquivos estáticos"""
    safe_path = filename.replace('..', '').replace('/', '')
    return send_from_directory('.', safe_path)

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
        
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "erro", "mensagem": "Erro de conexão com o banco."}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM clientes WHERE email = %s", (email,))
        cliente = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not cliente:
            return jsonify({"status": "erro", "mensagem": "Email ou senha incorretos."}), 401
        
        if not check_password_hash(cliente['senha'], senha):
            return jsonify({"status": "erro", "mensagem": "Email ou senha incorretos."}), 401
        
        # Cria a sessão do usuário
        session['cliente_id'] = cliente['id']
        session['cliente_nome'] = cliente['nome']
        session['logged_in'] = True
        
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
    return jsonify({"status": "ok", "redirect": "/"})

@app.route('/check_session')
def check_session():
    """Verifica se o usuário está logado"""
    if session.get('logged_in'):
        return jsonify({
            "logged_in": True,
            "cliente_nome": session.get('cliente_nome')
        })
    return jsonify({"logged_in": False})

# ==============================
# Cadastro de fornecedores
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
            "telefone": sanitizar_input(request.form.get("telefone", "")),
            "email": sanitizar_input(request.form.get("email", "")),
            "endereco": sanitizar_input(request.form.get("endereco", "")),
            "servico": sanitizar_input(request.form.get("servico", "")),
            "tempo": sanitizar_input(request.form.get("tempo", "")),
            "contrato": sanitizar_input(request.form.get("contrato", "")),
            "responsavel": sanitizar_input(request.form.get("responsavel", ""))
        }

        # Campos obrigatórios
        obrigatorios = ["nome", "razao", "cpfcnpj", "telefone", "email", 
                       "endereco", "servico", "tempo", "contrato", "responsavel"]
        
        for campo in obrigatorios:
            if not dados[campo]:
                return jsonify({"status": "erro", "mensagem": f"O campo '{campo}' é obrigatório."}), 400

        if not validar_email(dados["email"]):
            return jsonify({"status": "erro", "mensagem": "Email inválido."}), 400

        if not validar_telefone(dados["telefone"]):
            return jsonify({"status": "erro", "mensagem": "Telefone inválido."}), 400

        # Verifica se CPF/CNPJ já existe
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "erro", "mensagem": "Erro de conexão com o banco."}), 500
            
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM fornecedores WHERE cpfcnpj = %s", (dados["cpfcnpj"],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "erro", "mensagem": "CPF/CNPJ já cadastrado."}), 400

        # Inserção no banco
        cursor.execute('''
            INSERT INTO fornecedores (nome, razao, cpfcnpj, telefone, email, endereco, servico, tempo, contrato, responsavel)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (dados["nome"], dados["razao"], dados["cpfcnpj"], dados["telefone"],
              dados["email"], dados["endereco"], dados["servico"], dados["tempo"],
              dados["contrato"], dados["responsavel"]))
              
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"status": "ok", "mensagem": "Cadastro realizado com sucesso!"})
    
    except Exception as e:
        logger.error(f"Erro interno: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno do servidor."}), 500

# ==============================
# Cadastro de clientes
# ==============================
@app.route('/cadastrar_cliente', methods=['POST'])
@rate_limit(max_requests=10, window=60)
def cadastrar_cliente():
    try:
        # Sanitização dos dados
        nome = sanitizar_input(request.form.get('nome', ''))
        idade = request.form.get('idade', '')
        email = sanitizar_input(request.form.get('email', ''))
        telefone = sanitizar_input(request.form.get('telefone', ''))
        endereco = sanitizar_input(request.form.get('endereco', ''))
        genero = sanitizar_input(request.form.get('genero', ''))
        cpf = sanitizar_input(request.form.get('cpf', ''))
        senha = request.form.get('senha', '')
        confirmar_senha = request.form.get('confirmarSenha', '')

        # Validações básicas
        if not all([nome, idade, email, telefone, endereco, genero, cpf, senha]):
            return jsonify({"status": "erro", "mensagem": "Todos os campos são obrigatórios."}), 400

        if senha != confirmar_senha:
            return jsonify({"status": "erro", "mensagem": "As senhas não coincidem."}), 400

        if len(senha) < 6:
            return jsonify({"status": "erro", "mensagem": "Senha deve ter pelo menos 6 caracteres."}), 400

        if not validar_email(email):
            return jsonify({"status": "erro", "mensagem": "Email inválido."}), 400

        # Hash da senha
        senha_hash = generate_password_hash(senha)

        # Verifica se email ou CPF já existem
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "erro", "mensagem": "Erro de conexão com o banco."}), 500
            
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clientes WHERE email = %s OR cpf = %s", (email, cpf))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"status": "erro", "mensagem": "Email ou CPF já cadastrado."}), 400

        # Inserção
        cursor.execute('''
            INSERT INTO clientes (nome, idade, email, telefone, endereco, genero, cpf, senha)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, nome, email
        ''', (nome, idade, email, telefone, endereco, genero, cpf, senha_hash))
        
        novo_cliente = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        # Login automático
        session['cliente_id'] = novo_cliente[0]
        session['cliente_nome'] = novo_cliente[1]
        session['logged_in'] = True

        return jsonify({
            "status": "ok", 
            "mensagem": "Cliente cadastrado com sucesso!",
            "redirect": "/"
        })

    except Exception as e:
        logger.error(f"Erro interno: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro interno do servidor."}), 500

# ==============================
# APIs para listar dados
# ==============================
@app.route('/fornecedores_json')
@rate_limit(max_requests=30, window=60)
def fornecedores_json():
    try:
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "erro", "mensagem": "Erro de conexão com o banco."}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM fornecedores ORDER BY id DESC')
        rows = cursor.fetchall()
        cursor.close()
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
        conn = get_db_connection()
        if conn is None:
            return jsonify({"status": "erro", "mensagem": "Erro de conexão com o banco."}), 500
            
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT id, nome, idade, email, telefone, endereco, genero, cpf, data_criacao FROM clientes ORDER BY id DESC')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        clientes = [dict(row) for row in rows]
        return jsonify(clientes)
    except Exception as e:
        logger.error(f"Erro ao listar clientes: {e}")
        return jsonify({"status": "erro", "mensagem": "Erro ao carregar dados."}), 500

# ==============================
# Health check endpoint
# ==============================
@app.route('/health')
def health_check():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
            conn.close()
            return jsonify({"status": "healthy", "database": "connected"})
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 500
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 500

# ==============================
# Inicialização do aplicativo
# ==============================
if __name__ == "__main__":
    # Tentar criar bancos de dados
    criar_bancos()
    
    # Configurações para Render
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Servidor TechSuppliers iniciado!")
    print(f"📍 Porta: {port}")
    
    # Inicia o servidor
    app.run(
        debug=False,
        host="0.0.0.0", 
        port=port
    )
