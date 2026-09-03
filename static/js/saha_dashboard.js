(() => {
  // Saha ekranında başarılı işlemden sonra ilgili kartın bulunduğu konuma dön.
  const params = new URLSearchParams(window.location.search);
  const id = params.get("ticket");
  if (id) {
    const card = document.querySelector(`[data-ticket="${id}"]`);
    if (card) card.scrollIntoView({behavior:"smooth", block:"center"});
  }

  // Butonlara art arda çift tıklamayı engelle.
  document.querySelectorAll(".field-action-main").forEach(button => {
    button.closest("form")?.addEventListener("submit", () => {
      button.disabled = true;
      button.dataset.originalText = button.textContent;
      button.textContent = "Kaydediliyor...";
    });
  });
})();
