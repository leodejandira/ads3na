const sidebar = document.getElementById("sidebar");
const openSidebar = document.getElementById("openSidebar");
const closeSidebar = document.getElementById("closeSidebar");
const overlay = document.getElementById("sidebarOverlay");

// Abrir menu
openSidebar.addEventListener("click", () => {
    sidebar.classList.add("open");
    overlay.classList.add("visible");
});

// Fechar no botão
closeSidebar.addEventListener("click", () => {
    sidebar.classList.remove("open");
    overlay.classList.remove("visible");
});

// Fechar clicando fora
overlay.addEventListener("click", () => {
    sidebar.classList.remove("open");
    overlay.classList.remove("visible");
});

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");
    const messagesContainer = document.getElementById("messagesContainer");
    const emptyState = document.getElementById("emptyState");

    // Enviar mensagem
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();

        const text = chatInput.value.trim();
        if (!text) return;

        // criar elemento da mensagem do usuário
        const messageEl = document.createElement("div");
        messageEl.classList.add("message", "user-message");
        messageEl.innerHTML = `
            <div class="bubble user-bubble">${text}</div>
        `;

        // esconder empty state
        emptyState.style.display = "none";
        messagesContainer.style.display = "block";

        // adicionar mensagem na tela
        messagesContainer.appendChild(messageEl);

        // rolar até o final
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // limpar input
        chatInput.value = "";

        // (opcional) simular resposta da IA depois
        setTimeout(() => {
            receiveMessage("Mensagem recebida! Vou te ajudar");
        }, 600);
    });

    // Função para mensagem da IA
    function receiveMessage(text) {
        const messageEl = document.createElement("div");
        messageEl.classList.add("message", "ai-message");
        messageEl.innerHTML = `
            <div class="bubble ai-bubble">${text}</div>
        `;
        messagesContainer.appendChild(messageEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
