document.addEventListener("DOMContentLoaded", () => {
    const saveNameBtn = document.getElementById("saveNameBtn");
    const profileName = document.getElementById("profileName");
    const logoutBtn = document.getElementById("logoutBtn");

    // Salvar nome localmente
    saveNameBtn.addEventListener("click", () => {
        localStorage.setItem("username", profileName.value);
        alert("Nome salvo com sucesso!");
    });

    // Botão de sair
    logoutBtn.addEventListener("click", () => {
        localStorage.removeItem("token");
        window.location.href = "/login";
    });
});
