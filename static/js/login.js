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
            // Formatação CORRETA igual ao script antigo
            const formData = new URLSearchParams();
            formData.append('username', email);
            formData.append('password', password);
            
            // Adiciona o campo obrigatório 'grant_type=password'
            const body = 'grant_type=password&' + formData.toString();

            const response = await fetch("/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: body
            });

            if (response.ok) {
                const data = await response.json();
                
                // Decodificar o JWT para obter a role (igual ao antigo)
                const payload = parseJwt(data.access_token);
                const role = payload.role;
                
                // Armazenar o token (igual ao antigo)
                localStorage.setItem('access_token', data.access_token);
                
                // Redirecionar com base na role (igual ao antigo)
                if (role === 'gerente') {
                    window.location.href = '/gerente'; 
                } else if (role === 'usuario') {
                    window.location.href = '/usuario';
                } else {
                    alert('Login bem-sucedido, mas função de usuário desconhecida.');
                }
            } else {
                const error = await response.json();
                loginError.textContent = 'Erro no Login: ' + (error.detail || response.statusText);
                loginError.style.display = "block";
            }

        } catch (error) {
            console.error('Erro de rede:', error);
            loginError.textContent = 'Ocorreu um erro ao tentar conectar com a API.';
            loginError.style.display = "block";
        }
    });

    // Função auxiliar para decodificar o payload do JWT (igual ao antigo)
    function parseJwt(token) {
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            return JSON.parse(jsonPayload);
        } catch (e) {
            console.error("Erro ao decodificar JWT:", e);
            return {};
        }
    }
});