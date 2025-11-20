document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem('access_token');
    const loading = document.getElementById('loading');
    const content = document.getElementById('content');

    if (!token) {
        window.location.href = '/login';
    } else {
        // Verificar se o token é válido e se o usuário é gerente
        fetch('/rota-gerente', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            loading.style.display = 'none';
            if (response.ok) {
                content.style.display = 'flex';
            } else {
                localStorage.removeItem('access_token');
                window.location.href = '/login';
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            loading.style.display = 'none';
            window.location.href = '/login';
        });
    }
});

// Função de logout
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/';
}

// Funções para os botões (se precisar de lógica adicional)
function goToUpload() {
    window.location.href = '/upload';
}

function goToFuncionarios() {
    window.location.href = '/funcionarios';
}

function goToChat() {
    window.location.href = '/chat';
}