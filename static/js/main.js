document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("loginForm");

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      const formData = new URLSearchParams(new FormData(form)).toString();
      const body = "grant_type=password&" + formData;

      try {
        const response = await fetch("/login", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: body,
        });

        if (!response.ok) {
          const err = await response.json();
          alert("Erro no login: " + (err.detail || response.statusText));
          return;
        }

        const data = await response.json();

        // Armazenar token JWT no navegador
        localStorage.setItem("access_token", data.access_token);

        // Se o backend envia role no retorno:
        const role = data.role || parseJwt(data.access_token).role;

        if (role === "gerente") {
          window.location.href = "/gerente";
        } else if (role === "usuario") {
          window.location.href = "/usuario";
        } else {
          alert("Login feito, mas tipo de usuário desconhecido.");
        }
      } catch (error) {
        console.error("Erro de rede:", error);
        alert("Erro ao conectar com o servidor.");
      }
    });
  }
});

function parseJwt(token) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => {
          return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    console.error("Erro ao decodificar JWT:", e);
    return {};
  }
}
