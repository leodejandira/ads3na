// scripts.js (NENHUMA ALTERAÇÃO NECESSÁRIA, CÓDIGO PERFEITO PARA API)

const tabelaBody = document.querySelector("#tabela tbody");
const resultadoBusca = document.getElementById("resultadoBusca");

async function listarRegistros() {
    // Caminho absoluto /api/registros está correto
    const res = await fetch("/api/registros"); 
    const dados = await res.json();

    tabelaBody.innerHTML = "";
    dados.forEach(item => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${item.id}</td><td>${item.valor}</td>`;
        tabelaBody.appendChild(tr);
    });
}

async function buscarRegistro() {
    const id = document.getElementById("buscarId").value;
    // Caminho absoluto /api/registros/id está correto
    const res = await fetch(`/api/registros/${id}`); 
    if(res.ok) {
        const data = await res.json();
        resultadoBusca.textContent = `ID: ${data.id}, Valor: ${data.valor}`;
    } else {
        resultadoBusca.textContent = "Registro não encontrado";
    }
}

async function inserirRegistro() {
    const valor = document.getElementById("novoValor").value;
    // Caminho absoluto /api/registros está correto
    await fetch("/api/registros", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ valor })
    });
    document.getElementById("novoValor").value = "";
    listarRegistros();
}

async function deletarRegistro() {
    const id = document.getElementById("deleteId").value;
    // Caminho absoluto /api/registros/id está correto
    await fetch(`/api/registros/${id}`, { method: "DELETE" });
    document.getElementById("deleteId").value = "";
    listarRegistros();
}