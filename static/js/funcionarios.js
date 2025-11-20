// Elementos globais
const modal = document.getElementById("modal");
const openBtn = document.getElementById("btn-open-modal");
const closeBtn = document.getElementById("btn-close-modal");
const registerForm = document.getElementById("registerForm");
const messageDiv = document.getElementById("message");
const authCheck = document.getElementById("authCheck");
const mainContent = document.getElementById("mainContent");

// Variável global para o token
let token = localStorage.getItem('access_token');

// Verificação de autenticação
if (!token) {
    window.location.href = '/login';
} else {
    fetch('/rota-gerente', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            authCheck.style.display = 'none';
            mainContent.style.display = 'block';
            loadUsers();
        } else {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        window.location.href = '/login';
    });
}

// Modal functions
openBtn.addEventListener("click", () => {
    modal.style.display = "flex";
    // Limpar formulário ao abrir modal
    registerForm.reset();
});

closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
});

modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.style.display = "none";
    }
});

// Carregar lista de usuários
function loadUsers() {
    fetch('/usuarios', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Erro ao carregar usuários: ' + response.status);
        }
        return response.json();
    })
    .then(users => {
        const usersList = document.getElementById("usersList");
        
        if (users.length === 0) {
            usersList.innerHTML = '<tr><td colspan="5" style="text-align: center;">Nenhum usuário cadastrado.</td></tr>';
            return;
        }

        let tableContent = '';

        users.forEach(user => {
            tableContent += `
                <tr>
                    <td>${user.id}</td>
                    <td>${user.name}</td>
                    <td>${user.email}</td>
                    <td>${user.role}</td>
                    <td>
                        <button class="btn btn-delete" onclick="deleteUser(${user.id})">Deletar</button>
                    </td>
                </tr>
            `;
        });

        usersList.innerHTML = tableContent;
    })
    .catch(error => {
        console.error('Erro ao carregar usuários:', error);
        showMessage('Erro ao carregar lista de usuários: ' + error.message, 'error');
    });
}

// Registrar novo usuário
registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    
    const submitBtn = document.getElementById("submitBtn");
    const originalText = submitBtn.textContent;
    
    // Reset message
    showMessage('', '');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Registrando...';
    
    const formData = {
        name: document.getElementById("name").value,
        email: document.getElementById("email").value,
        senha: document.getElementById("senha").value,
        role: document.getElementById("role").value
    };

    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        const result = await response.json();
        
        showMessage(`Usuário ${result.name} registrado com sucesso!`, 'success');
        // Reset form
        registerForm.reset();
        // Fechar modal
        modal.style.display = 'none';
        // Reload users list
        loadUsers();
        
    } catch (error) {
        console.error('Erro no registro:', error);
        showMessage('Erro ao registrar: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
    }
});

// Deletar usuário
window.deleteUser = async function(userId) {
    if (!confirm('Tem certeza que deseja deletar este usuário?')) {
        return;
    }

    try {
        const response = await fetch(`/usuarios/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const result = await response.json();
        showMessage(`Usuário deletado com sucesso!`, 'success');
        loadUsers();
    } catch (error) {
        console.error('Erro ao deletar usuário:', error);
        showMessage('Erro ao deletar: ' + error.message, 'error');
    }
};

// Função para mostrar mensagens
function showMessage(message, type) {
    if (!messageDiv) return;
    
    messageDiv.innerHTML = message;
    messageDiv.className = 'message';
    
    if (type) {
        messageDiv.classList.add(type);
    }
    
    // Auto-esconder mensagens de sucesso após 5 segundos
    if (type === 'success') {
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 5000);
    }
}