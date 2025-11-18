document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("loginForm");
    const emailInput = document.getElementById("emailInput");
    const passwordInput = document.getElementById("passwordInput");
    const loginError = document.getElementById("loginError");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        loginError.style.display = "none";

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        try {
            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({
                    username: email,
                    password: password
                })
            });

            const result = await response.json();

            if (!response.ok) {
                loginError.textContent = result.detail || "Login inválido";
                loginError.style.display = "block";
                return;
            }

            // Salvar token no localStorage
            localStorage.setItem("token", result.access_token);
            localStorage.setItem("role", result.role);

            // Redirecionar
            if (result.role === "gerente") {
                window.location.href = "/gerente";
            } else {
                window.location.href = "/usuario";
            }

        } catch (error) {
            loginError.textContent = "Erro ao conectar ao servidor.";
            loginError.style.display = "block";
        }
    });
});