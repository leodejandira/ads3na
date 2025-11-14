document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("access_token");

  // --- Verifica login ---
  if (!token) {
    alert("Você precisa fazer login!");
    window.location.href = "/login";
    return;
  }

  const payload = parseJwt(token);
  if (payload.role !== "gerente") {
    alert("Acesso negado! Apenas gerentes podem acessar esta página.");
    window.location.href = "/login";
    return;
  }

  // --- Configura redirecionamentos ---
  document.getElementById("btn-upload").addEventListener("click", () => {
    window.location.href = "/upload";
  });

  document.getElementById("btn-funcionarios").addEventListener("click", () => {
    window.location.href = "/funcionarios";
  });

  document.getElementById("btn-chat").addEventListener("click", () => {
    window.location.href = "/chat";
  });

  document.getElementById("btn-logout").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  });
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
    console.error("Erro ao decodificar JWT:", e);
    return {};
  }
}
