(() => {
  const select = document.getElementById("id_kayit_alani");
  const personFields = document.getElementById("person-record-fields");
  const autoNote = document.getElementById("auto-organization-note");
  const help = document.getElementById("record-help");
  const submit = document.getElementById("record-submit");

  if (!select) return;

  function refresh() {
    const value = select.value;
    const automatic = value === "auto";
    const selectedText = select.options[select.selectedIndex]?.text || "";

    personFields.hidden = automatic || !value;
    autoNote.hidden = !automatic;

    if (!value) {
      help.textContent = "Kayıt türünü seçtiğinizde gerekli alanlar burada açılır.";
      submit.textContent = "Kaydı Oluştur";
      submit.disabled = true;
      return;
    }

    submit.disabled = false;

    if (automatic) {
      help.textContent = "Eksik koordinatör ve saha hesapları tek algoritmik işlemde tamamlanır.";
      submit.textContent = "Organizasyonu Otomatik Tamamla";
    } else {
      help.textContent = `${selectedText} alanına yeni personel kaydı eklenecek.`;
      submit.textContent = "Personel Kaydını Oluştur";
    }
  }

  select.addEventListener("change", refresh);
  refresh();
})();
