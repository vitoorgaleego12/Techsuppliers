document.addEventListener('DOMContentLoaded', function () {
    // Função para alternar o submenu
    function setupToggle(idLink, idSubmenu) {
        const link = document.getElementById(idLink);
        const submenu = document.getElementById(idSubmenu);
        link.addEventListener('click', function () {
            const isOpen = submenu.style.display === 'block';
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
    
    // Configura o toggle de cada categoria
    setupToggle('computadores-link', 'computadores-submenu');
    setupToggle('hardware-link', 'hardware-submenu');
    setupToggle('acessorios-link', 'acessorios-submenu');
    setupToggle('redes-link', 'redes-submenu');
    setupToggle('armazenamento-link', 'armazenamento-submenu');
    setupToggle('software-link', 'software-submenu');
    setupToggle('dispositivos-moveis-link', 'dispositivos-moveis-submenu');
    setupToggle('tecnologia-casa-link', 'tecnologia-casa-submenu');
    setupToggle('games-link', 'games-submenu');
    setupToggle('educacao-link', 'educacao-submenu');
  
    // Preencher as informações do fornecedor ao clicar nos produtos
    const productLinks = document.querySelectorAll('.submenu a');
    const modal = document.getElementById('product-modal');
    const modalInfoPanel = document.getElementById('modal-info-panel');
    const modalProductDetailsPanel = document.getElementById('modal-product-details-panel');
    const closeButton = document.querySelector('.close-button');

    const fornecedores = {
        'Notebooks': [
            {
                nome: 'Fornecedor A',
                preco: 'R$ 2.500,00',
                regiao: 'São Paulo',
                endereco: 'https://www.google.com/maps?q=São+Paulo,+SP',
                site: 'https://www.fornecedora.com.br',
                imagem: 'link-para-imagem-notebook-a.jpg',
                descricao: 'Notebook A é ideal para estudantes e profissionais.'
            },
            {
                nome: 'Fornecedor B',
                preco: 'R$ 2.700,00',
                regiao: 'Rio de Janeiro',
                endereco: 'https://www.google.com/maps?q=Rio+de+Janeiro,+RJ',
                site: 'https://www.fornecedoraB.com.br',
                imagem: 'link-para-imagem-notebook-b.jpg',
                descricao: 'Notebook B é perfeito para jogos e entretenimento.'
            },
        ],
        // Adicione outros produtos e fornecedores conforme necessário
    };

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

            const fornecedor = fornecedoresParaProduto[0]; // Exibe o primeiro fornecedor como exemplo
            const detailsContent = `
                <h3>Detalhes do Produto: ${produto}</h3>
                <img src="${fornecedor.imagem}" alt="Imagem de ${produto}" />
                <p>${fornecedor.descricao}</p>
            `;
            modalProductDetailsPanel.innerHTML = detailsContent;

            modal.style.display = "block"; // Abre o modal
        } else {
            modalInfoPanel.innerHTML = '<p>Nenhum fornecedor encontrado para este produto.</p>';
        }
    }

    // Adiciona a função de exibição ao clicar nos links de produtos
    productLinks.forEach (link => {
        link.addEventListener('click', function () {
            const produto = this.innerText; // Obtém o nome do produto
            displayModalInfo(produto); // Chama a função para exibir informações no modal
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
});


document.addEventListener('DOMContentLoaded', function() {
    // Criar o elemento do botão "Saiba mais"
    const saibaMaisBtn = document.createElement('a');
    saibaMaisBtn.href = 'Main.html';
    saibaMaisBtn.className = 'saiba-mais-btn';
    saibaMaisBtn.textContent = 'Saiba mais';
    saibaMaisBtn.title = 'Clique para mais informações';
    
    // Criar o container do botão (para a área de hover)
    const btnContainer = document.createElement('div');
    btnContainer.className = 'saiba-mais-container';
    
    // Adicionar o botão ao container
    btnContainer.appendChild(saibaMaisBtn);
    
    // Adicionar o container ao corpo do documento
    document.body.appendChild(btnContainer);
    
    // Adicionar estilos dinamicamente
    const style = document.createElement('style');
    style.textContent = `
        .saiba-mais-container {
            position: fixed;
            right: 0;
            bottom: 20px; /* Posiciona 20px acima do fundo */
            width: 40px;
            height: 40px; /* Altura reduzida para ficar mais compacto */
            background: rgba(0, 0, 0, 0.05);
            border-radius: 10px 0 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            z-index: 1000;
            overflow: hidden;
        }
        
        .saiba-mais-container:hover {
            width: 120px;
            background: rgba(0, 0, 0, 0.1);
        }
        
        .saiba-mais-btn {
            color: #fff;
            background-color: #000000;
            padding: 10px 15px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            white-space: nowrap;
            transform: translateX(80px);
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        .saiba-mais-container:hover .saiba-mais-btn {
            transform: translateX(0);
        }
        
        .saiba-mais-btn:hover {
            background-color: #0056b3;
        }
    `;
    
    document.head.appendChild(style);
});

document.addEventListener('DOMContentLoaded', function() {
    // Criar o elemento do botão
    const fornecedoresBtn = document.createElement('a');
    fornecedoresBtn.href = 'Listar.html';
    fornecedoresBtn.className = 'fornecedores-btn';
    fornecedoresBtn.textContent = 'Fornecedores cadastrados';
    fornecedoresBtn.title = 'Visualizar lista de fornecedores';
    
    // Criar o container do botão (para a área de hover)
    const btnContainer = document.createElement('div');
    btnContainer.className = 'fornecedores-container';
    
    // Adicionar o botão ao container
    btnContainer.appendChild(fornecedoresBtn);
    
    // Adicionar o container ao corpo do documento
    document.body.appendChild(btnContainer);
    
    // Adicionar estilos dinamicamente
    const style = document.createElement('style');
    style.textContent = `
        .fornecedores-container {
            position: fixed;
            right: 0;
            top: 70px;
            width: 40px;
            height: 40px;
            background: rgba(67, 97, 238, 0.1);
            border-radius: 0 0 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            z-index: 1000;
            overflow: hidden;
        }
        
        .fornecedores-container:hover {
            width: 200px;
            background: rgba(67, 97, 238, 0.2);
        }
        
        .fornecedores-btn {
            color: #fff;
            background-color: black;
            padding: 10px 15px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            white-space: nowrap;
            transform: translateX(160px);
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            font-size: 14px;
        }
        
        .fornecedores-container:hover .fornecedores-btn {
            transform: translateX(0);
        }
        
        .fornecedores-btn:hover {
            background-color: #3a56d4;
        }
        
        @media (max-width: 768px) {
            .fornecedores-container:hover {
                width: 180px;
            }
            
            .fornecedores-btn {
                font-size: 12px;
                transform: translateX(140px);
            }
        }
    `;
    
    document.head.appendChild(style);
});


document.addEventListener('DOMContentLoaded', function() {
    // Criar el elemento del botón
    const sustentabilidadeBtn = document.createElement('a');
    sustentabilidadeBtn.href = 'https://empresas-sustentaveis.vercel.app/';
    sustentabilidadeBtn.className = 'sustentabilidade-btn';
    sustentabilidadeBtn.textContent = 'Empresas Sustentáveis';
    sustentabilidadeBtn.title = 'Conheça empresas sustentáveis';
    sustentabilidadeBtn.target = '_blank'; // Abrir en nueva pestaña
    
    // Crear el contenedor del botón (para el área de hover)
    const btnContainer = document.createElement('div');
    btnContainer.className = 'sustentabilidade-container';
    
    // Agregar el botón al contenedor
    btnContainer.appendChild(sustentabilidadeBtn);
    
    // Agregar el contenedor al cuerpo del documento
    document.body.appendChild(btnContainer);
    
    // Agregar estilos dinámicamente
    const style = document.createElement('style');
    style.textContent = `
        .sustentabilidade-container {
            position: fixed;
            right: 0;
            top: 120px; /* Posicionado debajo del botón de fornecedores */
            width: 40px;
            height: 40px;
            background: rgba(76, 175, 80, 0.1); /* Verde claro para tema sustentável */
            border-radius: 0 0 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            z-index: 1000;
            overflow: hidden;
        }
        
        .sustentabilidade-container:hover {
            width: 200px;
            background: black;
        }
        
        .sustentabilidade-btn {
            color: #fff;
            background-color: black; /* Verde para tema sustentável */
            padding: 10px 15px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            white-space: nowrap;
            transform: translateX(160px);
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
            font-size: 14px;
        }
        
        .sustentabilidade-container:hover .sustentabilidade-btn {
            transform: translateX(0);
        }
        
        .sustentabilidade-btn:hover {
            background-color: black; /* Verde más oscuro en el hover */
        }
        
        @media (max-width: 768px) {
            .sustentabilidade-container:hover {
                width: 180px;
            }
            
            .sustentabilidade-btn {
                font-size: 12px;
                transform: translateX(140px);
            }
        }
    `;
    
    document.head.appendChild(style);
});


document.addEventListener('DOMContentLoaded', function() {
    // Criar o elemento do botão de ajuda
    const ajudaBtn = document.createElement('a');
    ajudaBtn.href = 'Help.html';
    ajudaBtn.className = 'ajuda-btn';
    ajudaBtn.textContent = 'Ajuda/Dúvidas';
    ajudaBtn.title = 'Clique para obter ajuda';
    
    // Criar o container do botão de ajuda
    const ajudaContainer = document.createElement('div');
    ajudaContainer.className = 'ajuda-container';
    
    // Adicionar o botão ao container
    ajudaContainer.appendChild(ajudaBtn);
    
    // Adicionar o container ao corpo do documento
    document.body.appendChild(ajudaContainer);
    
    // Criar botão para alternar modo dark/light
    const darkModeToggle = document.createElement('button');
    darkModeToggle.className = 'dark-mode-toggle';
    darkModeToggle.textContent = '🌙';
    darkModeToggle.title = 'Alternar modo escuro';
    
    // Adicionar botão dark mode ao corpo
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
    
    // Adicionar estilos dinamicamente - VERSÃO CORRIGIDA
    const style = document.createElement('style');
    style.textContent = `
        /* Estilos para o botão de ajuda */
        .ajuda-container {
            position: fixed;
            right: 0;
            bottom: 70px;
            width: 40px;
            height: 40px;
            background: rgba(255, 193, 7, 0.1);
            border-radius: 10px 0 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            z-index: 1000;
            overflow: hidden;
        }
        
        .ajuda-container:hover {
            width: 150px;
            background: black;
        }
        
        .ajuda-btn {
            color: #fff;
            background-color: black;
            padding: 10px 15px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            white-space: nowrap;
            transform: translateX(110px);
            transition: all 0.3s ease;
            box-shadow: black;
        }
        
        .ajuda-container:hover .ajuda-btn {
            transform: translateX(0);
        }
        
        .ajuda-btn:hover {
            background-color: #e0a800;
        }
        
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
        
        .dark-mode-toggle:hover {
            transform: scale(1.1);
        }
        
        /* ESTILOS DO MODO ESCURO - CORRIGIDOS */
        body.dark-mode {
            background-color: #1a1a1a;
            color: white;
        }
        
        /* Header e menu */
        body.dark-mode .menu,
        body.dark-mode header {
            background-color: #2d3748;
            color: white;
        }
        
        /* Links no menu */
        body.dark-mode .menu a,
        body.dark-mode header a {
            color: white;
        }
        
        /* Conteúdo principal */
        body.dark-mode .content,
        body.dark-mode main,
        body.dark-mode section {
            background-color: #2d3748;
            color: white;
        }
        
        /* Modal no modo escuro */
        body.dark-mode .modal-content {
            background-color: #2d3748;
            color: #e0e0e0;
        }
        
        /* NOME DOS FORNECEDORES EM PRETO (corrigindo o problema) */
        body.dark-mode .fornecedor p:first-child,
        body.dark-mode .fornecedor p:first-child * {
            color: #000000 !important;
            font-weight: bold;
        }
        
        /* Garantir contraste para o texto preto */
        body.dark-mode .fornecedor {
            background-color: #a0aec0;
            padding: 12px;
            margin-bottom: 15px;
            border-radius: 6px;
            border-left: 4px solid #4299e1;
        }
        
        /* Estilizar os outros textos dos fornecedores */
        body.dark-mode .fornecedor p:not(:first-child) {
            color: white;
        }
        
        /* Links dentro dos fornecedores */
        body.dark-mode .fornecedor a {
            color: #2b6cb0;
            font-weight: bold;
        }
        
        body.dark-mode .fornecedor a:hover {
            color: #2c5282;
            text-decoration: underline;
        }
        
        /* Botões flutuantes */
        body.dark-mode .saiba-mais-btn,
        body.dark-mode .fornecedores-btn,
        body.dark-mode .sustentabilidade-btn,
        body.dark-mode .ajuda-btn {
            background-color: #4a5568;
            color: white;
            border: 1px solid #718096;
        }
        
        body.dark-mode .saiba-mais-btn:hover,
        body.dark-mode .fornecedores-btn:hover,
        body.dark-mode .sustentabilidade-btn:hover,
        body.dark-mode .ajuda-btn:hover {
            background-color: #4299e1;
            color: white;
        }
        
        /* Containers dos botões flutuantes */
        body.dark-mode .saiba-mais-container:hover,
        body.dark-mode .fornecedores-container:hover,
        body.dark-mode .sustentabilidade-container:hover,
        body.dark-mode .ajuda-container:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        /* Elementos de formulário */
        body.dark-mode input,
        body.dark-mode select,
        body.dark-mode textarea {
            background-color: #2d3748;
            color: #e0e0e0;
            border: 1px solid #4a5568;
        }
        
        /* Tabelas */
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
    
    `;
    
    document.head.appendChild(style);
});

document.addEventListener('DOMContentLoaded', function() {
    // Criar botão para controlar a sidebar
    const sidebarToggleBtn = document.createElement('button');
    sidebarToggleBtn.id = 'sidebar-toggle-btn';
    sidebarToggleBtn.innerHTML = '◀'; // Seta para a esquerda quando expandido
    sidebarToggleBtn.title = 'Recolher/Expandir menu';
    
    // Adicionar o botão ao corpo do documento
    document.body.appendChild(sidebarToggleBtn);
    
    // Adicionar estilos para o botão e sidebar
    const style = document.createElement('style');
    style.textContent = `
        #sidebar-toggle-btn {
            position: fixed;
            left: 100px; /* Posição inicial ao lado da sidebar expandida */
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
        
        #sidebar-toggle-btn:hover {
            background-color: #555;
            transform: scale(1.1);
        }
        
        /* Quando a sidebar estiver minimizada */
        .sidebar-collapsed #sidebar-toggle-btn {
            left: 0px; /* Posição ao lado da sidebar minimizada */
            transform: rotate(180deg);
        }
        
        /* Estilos para a sidebar (ajuste conforme suas classes) */
        .menu, .sidebar, nav {
            transition: all 0.5s ease;
        }
        
        /* Quando a sidebar estiver minimizada */
        .sidebar-collapsed .menu,
        .sidebar-collapsed .sidebar,
        .sidebar-collapsed nav {
            width: 0px !important;
            overflow: hidden;
        }
        
        /* Esconder texto dos links quando minimizado */
        .sidebar-collapsed .menu li a span,
        .sidebar-collapsed .sidebar li a span,
        .sidebar-collapsed nav li a span {
            display: none;
        }
        
        /* Manter ícones visíveis */
        .sidebar-collapsed .menu li a::before,
        .sidebar-collapsed .sidebar li a::before,
        .sidebar-collapsed nav li a::before {
            content: '☰';
            margin-right: 0;
        }
        
        /* Ajustar conteúdo principal quando sidebar é minimizada */
        .sidebar-collapsed .content,
        .sidebar-collapsed main {
            margin-left: 0px !important;
            width: calc(100% - 60px) !important;
        }
    `;
    
    document.head.appendChild(style);
    
    // Adicionar evento de clique para o botão
    sidebarToggleBtn.addEventListener('click', function() {
        document.body.classList.toggle('sidebar-collapsed');
        
        // Alterar a direção da seta
        if (document.body.classList.contains('sidebar-collapsed')) {
            sidebarToggleBtn.innerHTML = '▶';
        } else {
            sidebarToggleBtn.innerHTML = '◀';
        }
        
        // Salvar preferência do usuário
        const isCollapsed = document.body.classList.contains('sidebar-collapsed');
        localStorage.setItem('sidebarCollapsed', isCollapsed);
        
        // Disparar evento personalizado para outros scripts
        window.dispatchEvent(new CustomEvent('sidebarToggle', { 
            detail: { collapsed: isCollapsed } 
        }));
    });
    
    // Verificar se há preferência salva
    const isSidebarCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isSidebarCollapsed) {
        document.body.classList.add('sidebar-collapsed');
        sidebarToggleBtn.innerHTML = '▶';
    }
    
    // Ajustar a posição do botão com base no tamanho atual da sidebar
    function adjustTogglePosition() {
        const sidebar = document.querySelector('.menu, .sidebar, nav');
        if (sidebar) {
            const sidebarWidth = window.getComputedStyle(sidebar).width;
            const toggleBtn = document.getElementById('sidebar-toggle-btn');
            
            if (document.body.classList.contains('sidebar-collapsed')) {
                toggleBtn.style.left = '60px';
            } else {
                toggleBtn.style.left = parseInt(sidebarWidth) - 10 + 'px';
            }
        }
    }
    
    // Ajustar a posição quando a janela é redimensionada
    window.addEventListener('resize', adjustTogglePosition);
    
    // Ajustar a posição inicial
    setTimeout(adjustTogglePosition, 100);
});


document.addEventListener('DOMContentLoaded', function() {
    // Criar o elemento do botão do simulador
    const simuladorBtn = document.createElement('a');
    simuladorBtn.href = 'https://simulador-lime.vercel.app/';
    simuladorBtn.className = 'simulador-btn';
    simuladorBtn.textContent = 'Simulador Financeiro';
    simuladorBtn.title = 'Acessar simulador financeiro';
    simuladorBtn.target = '_blank'; // Abrir em nova aba
    
    // Criar o container do botão (para a área de hover)
    const btnContainer = document.createElement('div');
    btnContainer.className = 'simulador-container';
    
    // Adicionar o botão ao container
    btnContainer.appendChild(simuladorBtn);
    
    // Adicionar o container ao corpo do documento
    document.body.appendChild(btnContainer);
    
    // Adicionar estilos dinamicamente
    const style = document.createElement('style');
    style.textContent = `
        .simulador-container {
            position: fixed;
            right: 0;
            top: 170px; /* Posicionado abaixo do botão de sustentabilidade */
            width: 40px;
            height: 40px;
            background: rgba(147, 51, 234, 0.1); /* Roxo claro */
            border-radius: 0 0 0 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            z-index: 1000;
            overflow: hidden;
        }
        
        .simulador-container:hover {
            width: 200px;
            background: black;
        }
        
        .simulador-btn {
            color: #fff;
            background-color: black; /* Roxo */
            padding: 10px 15px;
            border-radius: 5px;
            text-decoration: none;
            font-weight: bold;
            white-space: nowrap;
            transform: translateX(160px);
            transition: all 0.3s ease;
            box-shadow: black;
            font-size: 14px;
        }
        
        .simulador-container:hover .simulador-btn {
            transform: translateX(0);
        }
        
        .simulador-btn:hover {
            background-color: black; /* Roxo mais escuro no hover */
        }
        
        @media (max-width: 768px) {
            .simulador-container:hover {
                width: 180px;
            }
            
            .simulador-btn {
                font-size: 12px;
                transform: translateX(140px);
            }
        }
        
        /* Estilos para modo escuro */
        body.dark-mode .simulador-container:hover {
            background: #4a5568;
        }
        
        body.dark-mode .simulador-btn {
            background-color: #4a5568;
            color: white;
        }
        
        body.dark-mode .simulador-btn:hover {
            background-color: #4a5568;
        }
    `;
    
    document.head.appendChild(style);
});


// script.js
document.addEventListener('DOMContentLoaded', function() {
    // Encontrar o elemento com a classe site-name
    const siteNameElement = document.querySelector('.site-name');
    
    if (siteNameElement) {
        // Adicionar ícone antes do texto
        const originalText = siteNameElement.textContent;
        siteNameElement.innerHTML = `
            <span class="site-icon">⚙️</span>
            <span class="site-text">${originalText}</span>
        `;
        
        // Adicionar classe para animação
        siteNameElement.classList.add('animated-site-name');
    }
});

