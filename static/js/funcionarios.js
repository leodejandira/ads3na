const modal = document.getElementById("modal");
const openBtn = document.getElementById("btn-open-modal");
const closeBtn = document.getElementById("btn-close-modal");
// abrir modal
openBtn.addEventListener("click", () => {
    modal.style.display = "flex";
});
// fechar modal
closeBtn.addEventListener("click", () => {
    modal.style.display = "none";
});
// fechar clicando fora
modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.style.display = "none";
    }
});
