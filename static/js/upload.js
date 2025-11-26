// Elementos globais
const authCheck = document.getElementById('authCheck');
const container = document.querySelector('.container');
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.querySelector('.select-btn');
const selectedFiles = document.getElementById('selectedFiles');
const fileList = document.getElementById('fileList');
const uploadBtn = document.getElementById('uploadBtn');
const displayName = document.getElementById('displayName');
const messageDiv = document.getElementById('message');
const processingInfo = document.getElementById('processingInfo');

// Novos Elementos para a Tabela
const pdfTableBody = document.getElementById('pdfTableBody');
const emptyTableMessage = document.getElementById('emptyTableMessage');

// Variável global para o token
let token = localStorage.getItem('access_token');
let selectedFile = null;

// Verificação de autenticação
if (!token) {
    window.location.href = '/login';
} else {
    // Verificar se é gerente
    fetch('/rota-gerente', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            authCheck.style.display = 'none';
            container.style.display = 'block';
            // Carrega a lista de PDFs assim que a tela é liberada
            loadPdfList();
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

// Função para voltar dinamicamente
async function goBackToHome() {
    const role = await verifyUserRole();
    
    if (role === 'gerente') {
        window.location.href = '/gerente';
    } else if (role === 'usuario') {
        window.location.href = '/usuario';
    } else {
        window.location.href = '/login';
    }
}

// Função para verificar a role do usuário
async function verifyUserRole() {
    try {
        const gerenteResponse = await fetch('/rota-gerente', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (gerenteResponse.ok) return 'gerente';

        const usuarioResponse = await fetch('/rota-usuario', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (usuarioResponse.ok) return 'usuario';

        return null;
    } catch (error) {
        console.error('Erro ao verificar role:', error);
        return null;
    }
}

// Event Listeners
selectBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);

// Drag and Drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
});

function highlight() {
    dropZone.classList.add('drag-over');
}

function unhighlight() {
    dropZone.classList.remove('drag-over');
}

dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        
        // Validar se é PDF
        if (file.type !== 'application/pdf') {
            showMessage('Por favor, selecione apenas arquivos PDF.', 'error');
            return;
        }

        selectedFile = file;
        displaySelectedFile(file);
        selectedFiles.style.display = 'block';
    }
}

function displaySelectedFile(file) {
    const fileSize = (file.size / (1024 * 1024)).toFixed(2);
    
    fileList.innerHTML = `
        <div class="file-item">
            <div class="file-item-info">
                <i class='bx bxs-file-pdf'></i>
                <div>
                    <div class="file-item-name">${file.name}</div>
                    <div class="file-item-size">${fileSize} MB</div>
                </div>
            </div>
            <button class="remove-file-btn" onclick="removeFile()">
                <i class='bx bx-x'></i>
            </button>
        </div>
    `;
}

function removeFile() {
    selectedFile = null;
    fileInput.value = '';
    selectedFiles.style.display = 'none';
    hideMessage();
}

// Upload
uploadBtn.addEventListener('click', handleUpload);

async function handleUpload() {
    if (!selectedFile) {
        showMessage('Por favor, selecione um arquivo PDF.', 'error');
        return;
    }

    hideMessage();
    processingInfo.style.display = 'none';
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Enviando e processando...';

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (displayName.value) {
        formData.append('display_name', displayName.value);
    }

    try {
        const response = await fetch('/upload_pdf', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        const result = await response.json();

        if (response.ok) {
            let processingHTML = '';
            if (result.processing) {
                processingHTML = `
                    <div class="processing-info">
                        <strong>Processamento Automático Concluído:</strong>
                        <div class="processing-step success">Upload do arquivo</div>
                        <div class="processing-step success">Extração de texto (${result.processing.pages} páginas)</div>
                        <div class="processing-step success">Geração de embeddings (${result.processing.chunks_processed} chunks)</div>
                        <div class="processing-step success">Modelo: ${result.processing.model_used}</div>
                        <div class="processing-step success">Status: PDF pronto para consultas RAG</div>
                    </div>
                `;
            }

            showMessage(`
                <strong>Upload e processamento realizados com sucesso!</strong><br>
                <strong>Nome do arquivo:</strong> ${result.file_name}<br>
                <strong>Nome de exibição:</strong> ${result.display_name}<br>
                <strong>URL assinada:</strong> <a href="${result.signed_url}" target="_blank" style="color: #3b82f6; text-decoration: underline;">Visualizar PDF</a>
            `, 'success');

            processingInfo.innerHTML = processingHTML;
            processingInfo.style.display = 'block';

            // Reset form
            removeFile();
            displayName.value = '';

            // Atualiza a tabela com o novo arquivo
            loadPdfList();

        } else {
            showMessage(`Erro: ${result.detail || 'Erro no upload'}`, 'error');
        }
    } catch (error) {
        console.error('Erro no upload:', error);
        showMessage('Erro de rede ao tentar fazer upload.', 'error');
    } finally {
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Fazer Upload';
    }
}

// ==========================================
// FUNÇÕES DA TABELA DE PDFS
// ==========================================

async function loadPdfList() {
    try {
        const response = await fetch('/pdfs', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            renderTable(data.pdfs || []);
        } else {
            console.error('Erro ao listar PDFs');
        }
    } catch (error) {
        console.error('Erro na requisição da lista:', error);
    }
}

function renderTable(pdfs) {
    pdfTableBody.innerHTML = '';
    
    if (pdfs.length === 0) {
        emptyTableMessage.style.display = 'block';
        return;
    }
    
    emptyTableMessage.style.display = 'none';

    pdfs.forEach(pdf => {
        const row = document.createElement('tr');
        
        // Formatar data
        const dateObj = new Date(pdf.created_at || Date.now());
        const dateStr = dateObj.toLocaleDateString('pt-BR', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });

        const status = pdf.status || 'pendente';
        
        // Lógica de exibição do botão: some apenas se 'vetorizado'
        const isVectorized = status === 'vetorizado';
        
        const processBtnHtml = !isVectorized 
            ? `<button class="btn-sm btn-process" onclick="processPdf('${pdf.file_name}')">
                 <i class='bx bx-cog'></i> Vetorizar
               </button>` 
            : '';

        row.innerHTML = `
            <td><strong>${pdf.file_name}</strong></td>
            <td>${dateStr}</td>
            <td><span class="status-badge ${status}">${status}</span></td>
            <td>
                <div class="action-buttons">
                    ${processBtnHtml}
                    <button class="btn-sm btn-delete" onclick="deletePdf('${pdf.file_name}')">
                        <i class='bx bx-trash'></i> Deletar
                    </button>
                </div>
            </td>
        `;
        
        pdfTableBody.appendChild(row);
    });
}

async function deletePdf(fileName) {
    if (!confirm(`Tem certeza que deseja deletar o arquivo "${fileName}"?`)) return;

    try {
        const response = await fetch(`/pdfs/${encodeURIComponent(fileName)}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            showMessage(`Arquivo "${fileName}" deletado com sucesso.`, 'success');
            loadPdfList(); // Recarrega a tabela
        } else {
            const res = await response.json();
            showMessage(`Erro ao deletar: ${res.detail}`, 'error');
        }
    } catch (error) {
        console.error(error);
        showMessage('Erro de conexão ao deletar arquivo.', 'error');
    }
}

async function processPdf(fileName) {
    // Feedback visual imediato
    showMessage(`Iniciando vetorização de "${fileName}"...`, 'success');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
        const response = await fetch('/pdfs/process', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_name: fileName })
        });

        const result = await response.json();

        if (response.ok) {
            showMessage(`Arquivo vetorizado com sucesso!`, 'success');
            loadPdfList(); // Recarrega a tabela para atualizar status
        } else {
            showMessage(`Erro ao processar: ${result.detail}`, 'error');
        }
    } catch (error) {
        console.error(error);
        showMessage('Erro de conexão ao processar arquivo.', 'error');
    }
}

// Funções auxiliares
function showMessage(message, type) {
    messageDiv.innerHTML = message;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
}

function hideMessage() {
    messageDiv.style.display = 'none';
    messageDiv.className = 'message';
}