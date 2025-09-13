// TechSuppliers - Enhanced script.js
// Solução para problemas de carregamento de imagens no Render

// ==================================================
// CONFIGURAÇÃO E DETECÇÃO DE AMBIENTE
// ==================================================

// Configuração inicial
const config = {
    basePath: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' ? '' : '/img',
    apiBaseUrl: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:3000' 
        : 'https://techsuppliers-backend00.onrender.com',
    isProduction: !(window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
};

// ==================================================
// CORREÇÃO DE IMAGENS PARA O RENDER
// ==================================================

/**
 * Corrige os paths das imagens para funcionar no Render
 * Esta função deve ser chamada quando o DOM estiver carregado
 */
function fixImagePaths() {
    console.log('Iniciando correção de caminhos de imagens para o ambiente:', config.isProduction ? 'Produção (Render)' : 'Desenvolvimento');
    
    const images = document.querySelectorAll('img');
    let fixedCount = 0;
    
    images.forEach(img => {
        const src = img.getAttribute('src');
        if (src && !src.startsWith('http') && !src.startsWith('data:') && !src.startsWith('/img/')) {
            if (src.startsWith('img/')) {
                // Mantém caminho relativo mas adiciona basePath se necessário
                img.src = config.basePath + '/' + src;
                fixedCount++;
            } else if (src.startsWith('./')) {
                img.src = config.basePath + src.substring(1);
                fixedCount++;
            } else {
                // Paths absolutos sem a barra inicial
                img.src = config.basePath + '/' + src;
                fixedCount++;
            }
        }
    });
    
    console.log(`Correção de imagens concluída. ${fixedCount} imagens ajustadas.`);
}

// ==================================================
// FUNÇÃO PARA ALTERNAR SUBMENUS (ORIGINAL MELHORADA)
// ==================================================

function setupToggle(idLink, idSubmenu) {
    const link = document.getElementById(idLink);
    const submenu = document.getElementById(idSubmenu);
    
    if (!link || !submenu) {
        console.warn(`Elemento não encontrado para setupToggle: ${idLink} ou ${idSubmenu}`);
        return;
    }
    
    // Inicialmente esconder submenus
    submenu.style.display = 'none';
    link.setAttribute('aria-expanded', 'false');
    
    link.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        
        const isOpen = submenu.style.display === 'block';
        
        // Fechar todos os outros submenus abertos
        document.querySelectorAll('.submenu').forEach(menu => {
            if (menu.id !== idSubmenu) {
                menu.style.display = 'none';
                const parent = menu.previousElementSibling;
                if (parent && parent.classList.contains('menu-item')) {
                    parent.classList.remove('open');
                    const linkElem = parent.querySelector('a');
                    if (linkElem) linkElem.setAttribute('aria-expanded', 'false');
                }
            }
        });
        
        // Alternar o submenu atual
        if (isOpen) {
            submenu.style.display = 'none';
            link.parentElement.classList.remove('open');
            link.setAttribute('aria-expanded', 'false');
        } else {
            submenu.style.display = 'block';
            link.parentElement.classList.add('open');
            link.setAttribute('aria-expanded', 'true');
        }
    });
}

// ==================================================
// MODAL DE FORNECEDORES (ORIGINAL MELHORADA)
// ==================================================

// Dados de fornecedores (exemplo)
const fornecedores = {
    'Notebooks': [
        {
            nome: 'Fornecedor A',
            preco: 'R$ 2.500,00',
            regiao: 'São Paulo',
            endereco: 'https://www.google.com/maps?q=São+Paulo,+SP',
            site: 'https://www.fornecedora.com.br',
            imagem: 'img/notebook-a.jpg', // Caminho corrigido
            descricao: 'Notebook A é ideal para estudantes e profissionais.'
        },
        {
            nome: 'Fornecedor B',
            preco: 'R$ 2.700,00',
            regiao: 'Rio de Janeiro',
            endereco: 'https://www.google.com/maps?q=Rio+de+Janeiro,+RJ',
            site: 'https://www.fornecedoraB.com.br',
            imagem: 'img/notebook-b.jpg', // Caminho corrigido
            descricao: 'Notebook B é perfeito para jogos e entretenimento.'
        },
    ],
    // Adicione outros produtos e fornecedores conforme necessário
};

function initModal() {
    const modal = document.getElementById('product-modal');
    const modalInfoPanel = document.getElementById('modal-info-panel');
    const modalProductDetailsPanel = document.getElementById('modal-product-details-panel');
    const closeButton = document.querySelector('.close-button');
    const productLinks = document.querySelectorAll('.submenu a');

    if (!modal || !modalInfoPanel || !modalProductDetailsPanel || !closeButton) {
        console.warn('Elementos do modal não encontrados. A funcionalidade de modal será desativada.');
        return;
    }

    // Função para exibir informações no modal
    function displayModalInfo(produto) {
        const fornecedoresParaProduto = fornecedores[produto] || [];
        
        if (fornecedoresParaProduto.length > 0) {
            let content = `<h3>Fornecedores de ${produto}</h3>`;
            fornecedoresParaProduto.forEach(fornecedor => {
                content += `
                    <div class="fornecedor">
                        <p><strong>Fornecedor:</strong> ${fornecedor.nome}</p>
                        <p><strong>Preço:</strong> ${fornecedor.preco}</p>
                        <p><strong>Região:</strong> ${fornecedor.regiao}</p>
                        <p><strong>Endereço:</strong> <a href="${fornecedor.endereco}" target="_blank">Ver no Google Maps</a></p>
                        <p><strong>Site:</strong> <a href="${fornecedor.site}" target="_blank">${fornecedor.site}</a></p>
                    </div>
                `;
            });
            modalInfoPanel.innerHTML = content;

            const fornecedor = fornecedoresParaProduto[0];
            // Aplicar correção de caminho para a imagem
            const imagemCorrigida = config.basePath ? config.basePath + '/' + fornecedor.imagem : fornecedor.imagem;
            
            const detailsContent = `
                <h3>Detalhes do Produto: ${produto}</h3>
                <img src="${imagemCorrigida}" alt="Imagem de ${produto}" onerror="this.style.display='none'" />
                <p>${fornecedor.descricao}</p>
            `;
            modalProductDetailsPanel.innerHTML = detailsContent;

            modal.style.display = "block";
        } else {
            modalInfoPanel.innerHTML = '<p>Nenhum fornecedor encontrado para este produto.</p>';
            modalProductDetailsPanel.innerHTML = '';
            modal.style.display = "block";
        }
    }

    // Adicionar a função de exibição ao clicar nos links de produtos
    productLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const produto = this.innerText;
            displayModalInfo(produto);
        });
    });

    // Fecha o modal ao clicar no botão de fechar
    closeButton.addEventListener('click', function() {
        modal.style.display = "none";
    });

    // Fecha o modal ao clicar fora do conteúdo do modal
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
}

// ==================================================
// BOTÕES FLUTUANTES (ORIGINAL MELHORADA)
// ==================================================

function createFloatingButton(options) {
    const { href, className, text, title, target, position } = options;
    
    const btn = document.createElement('a');
    btn.href = href;
    btn.className = className + '-btn';
    btn.textContent = text;
    btn.title = title;
    if (target) btn.target = target;
    
    const container = document.createElement('div');
    container.className = className + '-container';
    container.style.top = position || 'auto';
    
    container.appendChild(btn);
    document.body.appendChild(container);
    
    return container;
}

function initFloatingButtons() {
    // Botões flutuantes
    const buttons = [
        {
            href: 'Main.html',
            className: 'saiba-mais',
            text: 'Saiba mais',
            title: 'Clique para mais informações',
            position: 'auto'
        },
        {
            href: 'Listar.html',
            className: 'fornecedores',
            text: 'Fornecedores cadastrados',
            title: 'Visualizar lista de fornecedores',
            position: '70px'
        },
        {
            href: 'https://empresas-sustentaveis.vercel.app/',
            className: 'sustentabilidade',
            text: 'Empresas Sustentáveis',
            title: 'Conheça empresas sustentáveis',
            target: '_blank',
            position: '120px'
        },
        {
            href: 'Help.html',
            className: 'ajuda',
            text: 'Ajuda/Dúvidas',
            title: 'Clique para obter ajuda',
            position: '170px'
        },
        {
            href: 'https://simulador-lime.vercel.app/',
            className: 'simulador',
            text: 'Simulador Financeiro',
            title: 'Acessar simulador financeiro',
            target: '_blank',
            position: '220px'
        }
    ];
    
    buttons.forEach(btnConfig => {
        createFloatingButton(btnConfig);
    });
}

// ==================================================
// MODO ESCURO (ORIGINAL MELHORADA)
// ==================================================

function initDarkMode() {
    const darkModeToggle = document.createElement('button');
    darkModeToggle.className = 'dark-mode-toggle';
    darkModeToggle.textContent = '🌙';
    darkModeToggle.title = 'Alternar modo escuro';
    document.body.appendChild(darkModeToggle);
    
    // Verificar se há preferência salva
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
        darkModeToggle.textContent = '☀️';
    }
    
    // Adicionar evento de clique para o toggle
    darkModeToggle.addEventListener('click', function() {
        document.body.classList.toggle('dark-mode');
        const darkModeEnabled = document.body.classList.contains('dark-mode');
        localStorage.setItem('darkMode', darkModeEnabled);
        darkModeToggle.textContent = darkModeEnabled ? '☀️' : '🌙';
    });
}

// ==================================================
// TOGGLE DA SIDEBAR (ORIGINAL MELHORADA)
// ==================================================

function initSidebarToggle() {
    const sidebarToggleBtn = document.createElement('button');
    sidebarToggleBtn.id = 'sidebar-toggle-btn';
    sidebarToggleBtn.innerHTML = '◀';
    sidebarToggleBtn.title = 'Recolher/Expandir menu';
    document.body.appendChild(sidebarToggleBtn);
    
    // Verificar se há preferência salva
    const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isSidebarCollapsed) {
        document.body.classList.add('sidebar-collapsed');
        sidebarToggleBtn.innerHTML = '▶';
    }
    
    // Adicionar evento de clique para o botão
    sidebarToggleBtn.addEventListener('click', function() {
        document.body.classList.toggle('sidebar-collapsed');
        sidebarToggleBtn.innerHTML = document.body.classList.contains('sidebar-collapsed') ? '▶' : '◀';
        
        // Salvar preferência do usuário
        localStorage.setItem('sidebarCollapsed', document.body.classList.contains('sidebar-collapsed'));
    });
}

// ==================================================
// INICIALIZAÇÃO DO SITE (FUNÇÃO PRINCIPAL)
// ==================================================

function initSite() {
    console.log('Inicializando TechSuppliers...');
    
    // Configurar toggles dos submenus
    const menuItems = [
        'computadores', 'hardware', 'acessorios', 'redes', 
        'armazenamento', 'software', 'dispositivos-moveis', 
        'tecnologia-casa', 'games', 'educacao'
    ];
    
    menuItems.forEach(item => {
        setupToggle(`${item}-link`, `${item}-submenu`);
    });
    
    // Inicializar modal de fornecedores
    initModal();
    
    // Inicializar botões flutuantes
    initFloatingButtons();
    
    // Inicializar modo escuro
    initDarkMode();
    
    // Inicializar toggle da sidebar
    initSidebarToggle();
    
    // Corrigir caminhos das imagens (SOLUÇÃO PARA O RENDER)
    fixImagePaths();
    
    // Adicionar ícone ao nome do site
    const siteNameElement = document.querySelector('.site-name');
    if (siteNameElement) {
        const originalText = siteNameElement.textContent;
        siteNameElement.innerHTML = `
            <span class="site-icon">⚙️</span>
            <span class="site-text">${originalText}</span>
        `;
        siteNameElement.classList.add('animated-site-name');
    }
    
    console.log('TechSuppliers inicializado com sucesso!');
}

// ==================================================
// ESTILOS DINÂMICOS (ORIGINAL MELHORADA)
// ==================================================

function addDynamicStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Estilos para os botões flutuantes */
        .saiba-mais-container, .fornecedores-container, .sustentabilidade-container, 
        .ajuda-container, .simulador-container {
            position: fixed;
            right: 0;
            width: 40px;
            height: 40px;
            border-radius: 0 0 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            z-index: 1000;
            overflow: hidden;
        }
        
        .saiba-mais-container { bottom: 20px; background: rgba(0, 0, 0, 0.05); }
        .fornecedores-container { top: 70px; background: rgba(67, 97, 238, 0.1); }
        .sustentabilidade-container { top: 120px; background: rgba(76, 175, 80, 0.1); }
        .ajuda-container { bottom: 70px; background: rgba(255, 193, 7, 0.1); }
        .simulador-container { top: 170px; background: rgba(147, 51, 234, 0.1); }
        
        .saiba-mais-container:hover { width: 120px; background: rgba(0, 0, 0, 0.1); }
        .fornecedores-container:hover { width: 200px; background: rgba(67, 97, 238, 0.2); }
        .sustentabilidade-container:hover { width: 200px; background: rgba(76, 175, 80, 0.2); }
        .ajuda-container:hover { width: 150px; background: rgba(255, 193, 7, 0.2); }
        .simulador-container:hover { width: 200px; background: rgba(147, 51, 234, 0.2); }
        
        .saiba-mais-btn, .fornecedores-btn, .sustentabilidade-btn, 
        .ajuda-btn, .simulador-btn {
            color: #fff;
            background-color: #000000;
            padding: 10px 15px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            white-space: nowrap;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        .saiba-mais-btn { transform: translateX(80px); }
        .fornecedores-btn { transform: translateX(160px); font-size: 14px; }
        .sustentabilidade-btn { transform: translateX(160px); font-size: 14px; }
        .ajuda-btn { transform: translateX(110px); }
        .simulador-btn { transform: translateX(160px); font-size: 14px; }
        
        .saiba-mais-container:hover .saiba-mais-btn { transform: translateX(0); }
        .fornecedores-container:hover .fornecedores-btn { transform: translateX(0); }
        .sustentabilidade-container:hover .sustentabilidade-btn { transform: translateX(0); }
        .ajuda-container:hover .ajuda-btn { transform: translateX(0); }
        .simulador-container:hover .simulador-btn { transform: translateX(0); }
        
        .saiba-mais-btn:hover { background-color: #0056b3; }
        .fornecedores-btn:hover { background-color: #3a56d4; }
        .sustentabilidade-btn:hover { background-color: #4caf50; }
        .ajuda-btn:hover { background-color: #e0a800; }
        .simulador-btn:hover { background-color: #9333ea; }
        
        /* Estilos para o botão de modo escuro */
        .dark-mode-toggle {
            position: fixed;
            left: 10px;
            bottom: 10px;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: none;
            background-color: #333;
            color: white;
            cursor: pointer;
            font-size: 18px;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        .dark-mode-toggle:hover { transform: scale(1.1); }
        
        /* Estilos para o botão de toggle da sidebar */
        #sidebar-toggle-btn {
            position: fixed;
            left: 100px;
            bottom: 30px;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            border: none;
            background-color: #333;
            color: white;
            cursor: pointer;
            font-size: 14px;
            z-index: 1001;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }
        
        #sidebar-toggle-btn:hover { background-color: #555; transform: scale(1.1); }
        .sidebar-collapsed #sidebar-toggle-btn { left: 0px; transform: rotate(180deg); }
        
        /* Media queries para responsividade */
        @media (max-width: 768px) {
            .fornecedores-container:hover, 
            .sustentabilidade-container:hover, 
            .simulador-container:hover { width: 180px; }
            
            .fornecedores-btn, 
            .sustentabilidade-btn, 
            .simulador-btn { font-size: 12px; transform: translateX(140px); }
            
            .fornecedores-container:hover .fornecedores-btn,
            .sustentabilidade-container:hover .sustentabilidade-btn,
            .simulador-container:hover .simulador-btn { transform: translateX(0); }
        }
        
        /* ESTILOS DO MODO ESCURO */
        body.dark-mode {
            background-color: #1a1a1a;
            color: white;
        }
        
        body.dark-mode .menu,
        body.dark-mode header {
            background-color: #2d3748;
            color: white;
        }
        
        body.dark-mode .menu a,
        body.dark-mode header a {
            color: white;
        }
        
        body.dark-mode .content,
        body.dark-mode main,
        body.dark-mode section {
            background-color: #2d3748;
            color: white;
        }
        
        body.dark-mode .modal-content {
            background-color: #2d3748;
            color: #e0e0e0;
        }
        
        body.dark-mode .fornecedor p:first-child,
        body.dark-mode .fornecedor p:first-child * {
            color: #000000 !important;
            font-weight: bold;
        }
        
        body.dark-mode .fornecedor {
            background-color: #a0aec0;
            padding: 12px;
            margin-bottom: 15px;
            border-radius: 6px;
            border-left: 4px solid #4299e1;
        }
        
        body.dark-mode .fornecedor p:not(:first-child) {
            color: white;
        }
        
        body.dark-mode .fornecedor a {
            color: #2b6cb0;
            font-weight: bold;
        }
        
        body.dark-mode .fornecedor a:hover {
            color: #2c5282;
            text-decoration: underline;
        }
        
        body.dark-mode .saiba-mais-btn,
        body.dark-mode .fornecedores-btn,
        body.dark-mode .sustentabilidade-btn,
        body.dark-mode .ajuda-btn,
        body.dark-mode .simulador-btn {
            background-color: #4a5568;
            color: white;
            border: 1px solid #718096;
        }
        
        body.dark-mode .saiba-mais-btn:hover,
        body.dark-mode .fornecedores-btn:hover,
        body.dark-mode .sustentabilidade-btn:hover,
        body.dark-mode .ajuda-btn:hover,
        body.dark-mode .simulador-btn:hover {
            background-color: #4299e1;
            color: white;
        }
        
        body.dark-mode .saiba-mais-container:hover,
        body.dark-mode .fornecedores-container:hover,
        body.dark-mode .sustentabilidade-container:hover,
        body.dark-mode .ajuda-container:hover,
        body.dark-mode .simulador-container:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        body.dark-mode input,
        body.dark-mode select,
        body.dark-mode textarea {
            background-color: #2d3748;
            color: #e0e0e0;
            border: 1px solid #4a5568;
        }
        
        body.dark-mode table {
            background-color: #2d3748;
            color: #e0e0e0;
        }
        
        body.dark-mode th,
        body.dark-mode td {
            border-color: #4a5568;
            color: #e0e0e0;
        }
        
        body.dark-mode tr:nth-child(even) {
            background-color: #4a5568;
        }
        
        /* Estilos para a sidebar (ajuste conforme suas classes) */
        .menu, .sidebar, nav {
            transition: all 0.5s ease;
        }
        
        .sidebar-collapsed .menu,
        .sidebar-collapsed .sidebar,
        .sidebar-collapsed nav {
            width: 0px !important;
            overflow: hidden;
        }
        
        .sidebar-collapsed .menu li a span,
        .sidebar-collapsed .sidebar li a span,
        .sidebar-collapsed nav li a span {
            display: none;
        }
        
        .sidebar-collapsed .menu li a::before,
        .sidebar-collapsed .sidebar li a::before,
        .sidebar-collapsed nav li a::before {
            content: '☰';
            margin-right: 0;
        }
        
        .sidebar-collapsed .content,
        .sidebar-collapsed main {
            margin-left: 0px !important;
            width: calc(100% - 60px) !important;
        }
    `;
    
    document.head.appendChild(style);
}

// ==================================================
// INICIALIZAÇÃO QUANDO O DOM ESTIVER PRONTO
// ==================================================

document.addEventListener('DOMContentLoaded', function() {
    // Adicionar estilos dinâmicos
    addDynamicStyles();
    
    // Inicializar o site
    initSite();
});

// ==================================================
// TRATAMENTO DE ERROS GLOBAL
// ==================================================

window.addEventListener('error', function(e) {
    console.error('Erro global capturado:', e.error);
});

// Para garantir que as imagens sejam corrigidas mesmo se carregadas dinamicamente
const originalAppendChild = Element.prototype.appendChild;
Element.prototype.appendChild = function() {
    const result = originalAppendChild.apply(this, arguments);
    if (arguments[0].tagName === 'IMG') {
        setTimeout(fixImagePaths, 100);
    }
    return result;
};
