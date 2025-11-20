// Elementos globais
const sidebar = document.getElementById("sidebar");
const openSidebar = document.getElementById("openSidebar");
const closeSidebar = document.getElementById("closeSidebar");
const overlay = document.getElementById("sidebarOverlay");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const messagesContainer = document.getElementById("messagesContainer");
const emptyState = document.getElementById("emptyState");
const authCheck = document.getElementById("authCheck");
const appContainer = document.querySelector('.app-container');
const backButton = document.getElementById("backButton");
const backButtonText = document.getElementById("backButtonText");

// Variável global para o token
let token = localStorage.getItem('access_token');

// Função para verificar a role no servidor
async function verifyUserRole() {
    try {
        // Tentar acessar rota de gerente primeiro
        const gerenteResponse = await fetch('/rota-gerente', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (gerenteResponse.ok) {
            return 'gerente';
        }

        // Se não for gerente, tentar rota de usuário
        const usuarioResponse = await fetch('/rota-usuario', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (usuarioResponse.ok) {
            return 'usuario';
        }

        return null;
    } catch (error) {
        console.error('Erro ao verificar role:', error);
        return null;
    }
}

// Função para voltar à tela correta baseada na role
async function goBackToHome() {
    const role = await verifyUserRole();
    
    if (role === 'gerente') {
        window.location.href = '/gerente';
    } else if (role === 'usuario') {
        window.location.href = '/usuario';
    } else {
        // Se não conseguiu verificar, vai para login
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    }
}

// Função para atualizar o botão de voltar dinamicamente
async function updateBackButton() {
    const role = await verifyUserRole();
    
    if (backButton && backButtonText) {
        if (role === 'gerente') {
            backButtonText.textContent = 'Voltar ao Gerente';
        } else if (role === 'usuario') {
            backButtonText.textContent = 'Voltar ao Usuário';
        } else {
            backButtonText.textContent = 'Fazer Login';
        }
        
        // Atualizar o evento de clique
        backButton.onclick = goBackToHome;
    }
}

// Sidebar functions
openSidebar.addEventListener("click", () => {
    sidebar.classList.add("open");
    overlay.classList.add("visible");
});

closeSidebar.addEventListener("click", () => {
    sidebar.classList.remove("open");
    overlay.classList.remove("visible");
});

overlay.addEventListener("click", () => {
    sidebar.classList.remove("open");
    overlay.classList.remove("visible");
});

// Auto-expand textarea
chatInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
});

// Enviar mensagem
chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = chatInput.value.trim();
    if (!question) return;

    // Adicionar mensagem do usuário
    addMessage(question, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Esconder empty state
    emptyState.style.display = "none";
    messagesContainer.style.display = "block";

    try {
        // Mostrar indicador de digitação
        showTypingIndicator();

        const response = await fetch('/pdfs/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ query: question })
        });

        // Remover indicador de digitação
        removeTypingIndicator();

        const data = await response.json();
        
        if (response.ok) {
            addMessage(data.response, 'assistant');
        } else {
            addMessage(`Erro: ${data.detail || 'Erro na resposta'}`, 'assistant', true);
        }
    } catch (error) {
        removeTypingIndicator();
        console.error('Erro de conexão:', error);
        addMessage('Erro de conexão com o servidor. Tente novamente.', 'assistant', true);
    }
});

// Função para adicionar mensagem
function addMessage(text, type, isError = false) {
    const messageEl = document.createElement("div");
    
    if (type === 'user') {
        messageEl.classList.add("message", "user");
        messageEl.innerHTML = `
            <div class="message-content">
                <div class="message-text">${text}</div>
            </div>
        `;
    } else {
        messageEl.classList.add("message", "assistant");
        if (isError) {
            messageEl.innerHTML = `
                <div class="message-content error-message">
                    <div class="message-text">${text}</div>
                </div>
            `;
        } else {
            messageEl.innerHTML = `
                <div class="message-content">
                    <div class="message-text">${text}</div>
                </div>
            `;
        }
    }

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Mostrar indicador de digitação
function showTypingIndicator() {
    const typingEl = document.createElement("div");
    typingEl.id = "typing-indicator";
    typingEl.classList.add("message", "assistant");
    typingEl.innerHTML = `
        <div class="message-content">
            <div class="typing-indicator">
                <span>MindDesk está digitando</span>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(typingEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Remover indicador de digitação
function removeTypingIndicator() {
    const typingEl = document.getElementById("typing-indicator");
    if (typingEl) {
        typingEl.remove();
    }
}

// Limpar chat
function clearChat() {
    if (confirm('Tem certeza que deseja limpar a conversa?')) {
        messagesContainer.innerHTML = '';
        emptyState.style.display = 'flex';
        messagesContainer.style.display = 'none';
    }
}

// Enter para enviar (mas permite Shift+Enter para nova linha)
chatInput.addEventListener("keypress", function(e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Verificação de autenticação
if (!token) {
    window.location.href = '/login';
} else {
    // Verificar a role no servidor
    verifyUserRole()
    .then(role => {
        if (role) {
            authCheck.style.display = 'none';
            appContainer.style.display = 'flex';
            updateBackButton();
        } else {
            // Token inválido ou expirado
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
    })
    .catch(error => {
        console.error('Erro na verificação:', error);
        localStorage.removeItem('access_token');
        window.location.href = '/login';
    });
}