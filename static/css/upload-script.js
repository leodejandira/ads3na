document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("Faça login primeiro!");
    window.location.href = "/login";
    return;
  }

  const payload = parseJwt(token);
  if (payload.role !== "gerente") {
    alert("Acesso negado! Somente gerentes podem acessar.");
    window.location.href = "/login";
    return;
  }

  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const selectedFilesDiv = document.getElementById("selectedFiles");
  const fileListDiv = document.getElementById("fileList");
  const fileCountSpan = document.getElementById("fileCount");
  const uploadBtn = document.getElementById("uploadBtn");
  const tableBody = document.getElementById("tableBody");
  const totalFilesSpan = document.getElementById("totalFiles");
  const selectBtn = document.querySelector(".select-btn");

  let selectedFiles = [];

  // === Escolher arquivos ===
  selectBtn.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => handleFiles(e.target.files));

  // === Drag & Drop ===
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("active");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("active");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("active");
    handleFiles(e.dataTransfer.files);
  });

  // === Função para listar arquivos ===
  function handleFiles(files) {
    selectedFiles = Array.from(files);
    fileListDiv.innerHTML = "";
    selectedFiles.forEach((file) => {
      const item = document.createElement("p");
      item.textContent = `${file.name} - ${(file.size / 1024 / 1024).toFixed(2)} MB`;
      fileListDiv.appendChild(item);
    });
    fileCountSpan.textContent = selectedFiles.length;
    selectedFilesDiv.style.display = "block";
  }

  // === Upload ===
  uploadBtn.addEventListener("click", async () => {
    if (selectedFiles.length === 0) return alert("Selecione um arquivo!");

    const formData = new FormData();
    selectedFiles.forEach((file) => formData.append("files", file));

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (res.ok) {
        alert("Upload realizado com sucesso!");
        selectedFiles = [];
        selectedFilesDiv.style.display = "none";
        await loadFiles();
      } else {
        const err = await res.json();
        alert("Erro no upload: " + (err.detail || res.statusText));
      }
    } catch (err) {
      alert("Erro de rede: " + err.message);
    }
  });

  // === Carregar arquivos salvos ===
  async function loadFiles() {
    try {
      const res = await fetch("/api/files", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      tableBody.innerHTML = "";
      data.forEach((file) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${file.filename}</td>
          <td>${(file.size / 1024 / 1024).toFixed(2)} MB</td>
          <td>${file.uploaded_by}</td>
          <td>${new Date(file.uploaded_at).toLocaleString()}</td>
          <td>
            <button class="action-btn" title="Download" onclick="window.open('${file.url}', '_blank')">
              <i class='bx bx-download'></i>
            </button>
          </td>
        `;
        tableBody.appendChild(row);
      });

      totalFilesSpan.textContent = data.length;
    } catch (e) {
      console.error("Erro ao carregar arquivos:", e);
    }
  }

  loadFiles();
});

function parseJwt(token) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return {};
  }
}
