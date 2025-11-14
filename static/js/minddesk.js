document.addEventListener("DOMContentLoaded", () => {
    const usernameEl = document.getElementById("username");
    const storedName = localStorage.getItem("username");
    if (storedName) {
        usernameEl.textContent = storedName;
    }

    const form = document.getElementById("chatForm");
    const input = document.getElementById("chatInput");
    const messagesContainer = document.getElementById("messagesContainer");
    const emptyState = document.getElementById("emptyState");

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const message = input.value.trim();
        if (!message) return;

        emptyState.style.display = "none";
        messagesContainer.style.display = "block";

        // Adiciona mensagem do usuário
        const userMsg = document.createElement("div");
        userMsg.className = "message user";
        userMsg.textContent = message;
        messagesContainer.appendChild(userMsg);

        // Simula resposta do MindDesk
        const botMsg = document.createElement("div");
        botMsg.className = "message bot";
        botMsg.textContent = "🤖 Processando sua solicitação...";
        messagesContainer.appendChild(botMsg);

        input.value = "";
        messagesContainer.scrollTop = messagesContainer.scrollHeight;

        // Simulação de resposta
        setTimeout(() => {
            botMsg.textContent = "Aqui está a resposta simulada do MindDesk.";
        }, 1500);
    });
});
