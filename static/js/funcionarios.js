document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("Faça login primeiro!");
    window.location.href = "/login";
    return;
  }

  const user = parseJwt(token);
  if (user.role !== "gerente") {
    alert("Acesso negado! Apenas gerentes podem acessar.");
    window.location.href = "/login";
    return;
  }

  const registerForm = document.getElementById("registerForm");
  const tableBody = document.getElementById("employeesTableBody");
  const backBtn = document.getElementById("backBtn");

  // === Voltar para tela do gerente ===
  backBtn.addEventListener("click", () => {
    window.location.href = "/gerente";
  });

  // === Registrar novo funcionário ===
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const role = document.getElementById("role").value;

    const data = { name, email, senha: password, role };

    try {
      const res = await fetch("/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(data),
      });

      if (res.ok) {
        alert("Funcionário registrado com sucesso!");
        registerForm.reset();
        await loadEmployees();
      } else {
        const err = await res.json();
        alert(`Erro ao registrar: ${err.detail || res.statusText}`);
      }
    } catch (err) {
      alert("Erro de rede: " + err.message);
    }
  });

  // === Carregar lista de funcionários ===
  async function loadEmployees() {
    try {
      const res = await fetch("/usuarios", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();

      tableBody.innerHTML = "";

      data.forEach((emp) => {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td>${emp.id}</td>
          <td>${emp.name}</td>
          <td>${emp.email}</td>
          <td>${emp.role}</td>
          <td>
            <button class="btn btn-delete" data-id="${emp.id}">Deletar</button>
          </td>
        `;
        tableBody.appendChild(row);
      });

      // adicionar eventos de delete
      document.querySelectorAll(".btn-delete").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.getAttribute("data-id");
          if (!confirm("Tem certeza que deseja deletar este funcionário?")) return;

          try {
            const res = await fetch(`/usuarios/${id}`, {
              method: "DELETE",
              headers: { Authorization: `Bearer ${token}` },
            });

            if (res.ok) {
              alert("Funcionário deletado com sucesso!");
              await loadEmployees();
            } else {
              const err = await res.json();
              alert(`Erro ao deletar: ${err.detail || res.statusText}`);
            }
          } catch (err) {
            alert("Erro de rede: " + err.message);
          }
        });
      });
    } catch (err) {
      console.error("Erro ao listar funcionários:", err);
    }
  }

  // === Função auxiliar para decodificar JWT ===
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

  loadEmployees();
});
