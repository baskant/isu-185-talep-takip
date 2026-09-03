(() => {
  const map = L.map("call-map").setView([40.7656, 29.9408], 10);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  const form = document.getElementById("talep-form");
  const ilce = document.getElementById("id_ilce");
  const mahalle = document.getElementById("id_mahalle");
  const yol = document.getElementById("id_yol");
  const yolSerbest = document.getElementById("id_yol_serbest");
  const isTuru = document.getElementById("id_is_turu");
  const altTur = document.getElementById("id_is_alt_turu");
  const latInput = document.getElementById("id_lat");
  const lngInput = document.getElementById("id_lng");
  const kapi = document.getElementById("id_kapi_no");
  const status = document.getElementById("geo-status");
  let marker = null;

  function resetSelect(select, label) {
    select.innerHTML = "";
    select.add(new Option(label, ""));
  }

  function moveMap(lat, lng, zoom = 15) {
    lat = parseFloat(lat);
    lng = parseFloat(lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;
    map.setView([lat, lng], zoom);
  }

  function setPoint(lat, lng, zoom = 15) {
    lat = parseFloat(lat);
    lng = parseFloat(lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    moveMap(lat, lng, zoom);

    if (marker) {
      marker.setLatLng([lat, lng]);
    } else {
      marker = L.marker([lat, lng], {draggable: true}).addTo(map);
      marker.on("dragend", e => {
        const p = e.target.getLatLng();
        latInput.value = p.lat.toFixed(6);
        lngInput.value = p.lng.toFixed(6);
      });
    }

    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
  }

  function clearPoint() {
    latInput.value = "";
    lngInput.value = "";
    if (marker) {
      map.removeLayer(marker);
      marker = null;
    }
  }

  async function getJSON(url) {
    const response = await fetch(url);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || "İstek başarısız");
    return payload;
  }

  function resetNewTicketForm() {
    if (!form) return;
    form.reset();

    resetSelect(mahalle, "Önce ilçe seçiniz");
    resetSelect(yol, "Önce mahalle seçiniz");
    resetSelect(altTur, "Önce iş türü seçiniz");

    if (ilce.options.length) ilce.selectedIndex = 0;
    if (isTuru.options.length) isTuru.selectedIndex = 0;

    if (yolSerbest) yolSerbest.value = "";
    clearPoint();
    map.setView([40.7656, 29.9408], 10);
    status.textContent = "Haritadaki noktaya tıklayarak konumu düzeltebilirsiniz.";
  }

  if (!ilce.value && ilce.options.length) ilce.options[0].text = "İlçe seçiniz";
  if (!mahalle.value) resetSelect(mahalle, "Önce ilçe seçiniz");
  if (!yol.value) resetSelect(yol, "Önce mahalle seçiniz");
  if (!isTuru.value && isTuru.options.length) isTuru.options[0].text = "İş türü seçiniz";
  if (!altTur.value) resetSelect(altTur, "Önce iş türü seçiniz");

  map.on("click", e => setPoint(e.latlng.lat, e.latlng.lng, map.getZoom()));

  ilce.addEventListener("change", async () => {
    resetSelect(
      mahalle,
      ilce.value ? "Güncel mahalleler yükleniyor..." : "Önce ilçe seçiniz"
    );
    resetSelect(yol, "Önce mahalle seçiniz");
    clearPoint();

    if (!ilce.value) return;

    try {
      const [payload, detay] = await Promise.all([
        getJSON(`/api/adres/mahalleler/?ilce=${ilce.value}`),
        getJSON(`/api/adres/ilce/?ilce=${ilce.value}`)
      ]);

      const mahalleler = payload.items || [];
      resetSelect(
        mahalle,
        mahalleler.length ? "Mahalle seçiniz" : "Mahalle verisi bulunamadı"
      );
      mahalleler.forEach(x => mahalle.add(new Option(x.ad, x.id)));

      // Yalnız haritayı ilçeye götür; koordinatı talebe yazma.
      if (detay.lat && detay.lng) moveMap(detay.lat, detay.lng, 12);

      if (payload.source) {
        const version = payload.datasetVersion ? ` • veri seti ${payload.datasetVersion}` : "";
        const updated = payload.lastUpdated ? ` • güncelleme ${payload.lastUpdated}` : "";
        status.textContent = `Mahalle kaynağı: ${payload.source}${version}${updated}`;
      }
    } catch (e) {
      resetSelect(mahalle, "Mahalleler yüklenemedi - tekrar deneyin");
      status.textContent = e.message || "Güncel mahalle verisine ulaşılamadı.";
    }
  });

  mahalle.addEventListener("change", async () => {
    resetSelect(
      yol,
      mahalle.value ? "Cadde / sokaklar yükleniyor..." : "Önce mahalle seçiniz"
    );
    clearPoint();
    if (!mahalle.value) return;

    try {
      const yollar = await getJSON(`/api/adres/yollar/?mahalle=${mahalle.value}`);
      resetSelect(
        yol,
        yollar.length ? "Cadde / sokak seçiniz" : "Listede yol yoksa aşağıya yazınız"
      );
      yollar.forEach(x => yol.add(new Option(x.ad, x.id)));

      const payload = await getJSON(`/api/adres/mahalleler/?ilce=${ilce.value}`);
      const secili = (payload.items || []).find(
        x => String(x.id) === String(mahalle.value)
      );
      // Mahalle merkezi varsa sadece ekranda yaklaş.
      if (secili?.lat && secili?.lng) moveMap(secili.lat, secili.lng, 15);
    } catch (e) {
      resetSelect(yol, "Listede yol yoksa aşağıya yazınız");
    }
  });

  yol.addEventListener("change", async () => {
    clearPoint();
    if (!yol.value) return;
    try {
      const yollar = await getJSON(`/api/adres/yollar/?mahalle=${mahalle.value}`);
      const secili = yollar.find(x => String(x.id) === String(yol.value));
      // Gerçek yol merkez koordinatı varsa talebe yazılabilir.
      if (secili?.lat && secili?.lng) setPoint(secili.lat, secili.lng, 17);
    } catch (e) {}
  });

  isTuru.addEventListener("change", async () => {
    resetSelect(
      altTur,
      isTuru.value ? "İş alt türleri yükleniyor..." : "Önce iş türü seçiniz"
    );
    if (!isTuru.value) return;

    try {
      const items = await getJSON(
        `/api/talepler/alt-turler/?is_turu=${isTuru.value}`
      );
      resetSelect(
        altTur,
        items.length ? "İş alt türü seçiniz" : "Bu iş türüne ait alt tür bulunamadı"
      );
      items.forEach(x => altTur.add(new Option(x.ad, x.id)));
    } catch (e) {
      resetSelect(altTur, "İş alt türleri yüklenemedi");
    }
  });

  document.getElementById("find-address")?.addEventListener("click", async () => {
    if (!ilce.value) {
      status.textContent = "Önce ilçe seçin.";
      return;
    }

    const seciliYol = yol.options[yol.selectedIndex]?.text || "";
    const yolText = yol.value ? seciliYol : (yolSerbest?.value || "");

    const params = new URLSearchParams({
      ilce: ilce.options[ilce.selectedIndex]?.text || "",
      mahalle: mahalle.options[mahalle.selectedIndex]?.text || "",
      yol: yolText,
      kapi: kapi.value || ""
    });

    status.textContent = "Adres haritada aranıyor...";
    try {
      const d = await getJSON(`/api/adres/geocode/?${params}`);
      if (d.ok) {
        setPoint(d.lat, d.lng, 18);
        status.textContent = d.display_name;
      } else {
        status.textContent = d.message || "Adres bulunamadı.";
      }
    } catch (e) {
      status.textContent =
        "Adres servisine ulaşılamadı; konumu haritadan seçebilirsiniz.";
    }
  });

  // Kayıt başarılıysa sunucu ?created=... ile temiz GET'e yönlendirir.
  // Tarayıcının form/autofill geçmişi alanları geri doldurmasın diye ayrıca resetlenir.
  const params = new URLSearchParams(window.location.search);
  if (params.has("created")) {
    resetNewTicketForm();
    setTimeout(resetNewTicketForm, 80);
    setTimeout(resetNewTicketForm, 300);

    const cleanUrl = window.location.pathname;
    window.history.replaceState({}, document.title, cleanUrl);
  }

  // 185 çalışma sekmeleri
  const buttons = [...document.querySelectorAll("[data-call-tab]")];
  const panels = [...document.querySelectorAll("[data-call-panel]")];

  function activateCallTab(target) {
    buttons.forEach(x => {
      const active = x.dataset.callTab === target;
      x.classList.toggle("active", active);
      x.setAttribute("aria-selected", active ? "true" : "false");
    });
    panels.forEach(panel => {
      const active = panel.dataset.callPanel === target;
      panel.classList.toggle("active", active);
      panel.hidden = !active;
    });
    if (target === "new") setTimeout(() => map.invalidateSize(), 50);
  }

  buttons.forEach(button => {
    button.addEventListener("click", () => {
      activateCallTab(button.dataset.callTab);
    });
  });

  const requestedTab = new URLSearchParams(window.location.search).get("tab");
  if (requestedTab && ["new","list"].includes(requestedTab)) {
    activateCallTab(requestedTab);
  }


  async function refreshTicketStatuses() {
    try {
      const response = await fetch("/api/talepler/operasyon-ozet/", {
        headers: {"X-Requested-With": "XMLHttpRequest"}
      });
      if (!response.ok) return;
      const data = await response.json();

      (data.items || []).forEach(item => {
        const badge = document.querySelector(`[data-ticket-status="${item.id}"]`);
        if (!badge) return;
        badge.textContent = item.durum_label;
        badge.className = `badge status-${item.durum}`;
      });

      const statsNew = document.querySelector("[data-live-stat='new']");
      const statsField = document.querySelector("[data-live-stat='field']");
      const statsApproval = document.querySelector("[data-live-stat='approval']");
      const statsDone = document.querySelector("[data-live-stat='done']");
      const statsFeedback = document.querySelector("[data-live-stat='feedback']");
      const tabFeedback = document.querySelector("[data-feedback-tab-count]");
      const notice = document.getElementById("feedback-live-notice");

      if (statsNew) statsNew.textContent = data.counts?.bekleyen ?? statsNew.textContent;
      if (statsField) statsField.textContent = data.counts?.sahada ?? statsField.textContent;
      if (statsApproval) statsApproval.textContent = data.counts?.onay_bekleyen ?? statsApproval.textContent;
      if (statsDone) statsDone.textContent = data.counts?.tamam ?? statsDone.textContent;

      const currentFeedback = Number(tabFeedback?.textContent || statsFeedback?.textContent || 0);
      const nextFeedback = Number(data.counts?.geri_bildirim_bekleyen ?? currentFeedback);

      if (statsFeedback) statsFeedback.textContent = nextFeedback;
      if (tabFeedback) tabFeedback.textContent = nextFeedback;

      // Do not auto-reload while an operator is typing a new citizen call.
      // Instead surface a safe live notice.
      if (notice && nextFeedback > currentFeedback) {
        notice.hidden = false;
      }
    } catch (e) {}
  }

  setInterval(refreshTicketStatuses, 8000);



  // V13: soldaki arama kuyruğundan seçilen kaydın tüm detaylarını sağ panelde aç.
  const callbackQueueItems = [...document.querySelectorAll("[data-callback-ticket]")];
  const callbackDetailItems = [...document.querySelectorAll("[data-callback-detail]")];
  let callbackDetailMap = null;

  function renderCallbackDetailMap(detail) {
    if (callbackDetailMap) {
      callbackDetailMap.remove();
      callbackDetailMap = null;
    }
    const el = detail?.querySelector("[data-detail-map]");
    if (!el || typeof L === "undefined") return;

    const lat = parseFloat(el.dataset.lat || "");
    const lng = parseFloat(el.dataset.lng || "");
    el.innerHTML = "";
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      el.classList.add("no-map-point");
      el.textContent = "Bu kayıtta harita koordinatı bulunmuyor.";
      return;
    }

    el.classList.remove("no-map-point");
    callbackDetailMap = L.map(el, {zoomControl: true, attributionControl: false}).setView([lat, lng], 16);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {maxZoom: 19}).addTo(callbackDetailMap);
    L.marker([lat, lng]).addTo(callbackDetailMap);
    setTimeout(() => callbackDetailMap?.invalidateSize(), 80);
  }

  function openCallbackTicket(id) {
    callbackQueueItems.forEach(item => {
      const active = item.dataset.callbackTicket === String(id);
      item.classList.toggle("active", active);
      item.setAttribute("aria-pressed", active ? "true" : "false");
    });
    callbackDetailItems.forEach(detail => {
      const active = detail.dataset.callbackDetail === String(id);
      detail.classList.toggle("active", active);
      detail.hidden = !active;
      if (active) renderCallbackDetailMap(detail);
    });
  }

  callbackQueueItems.forEach(item => {
    item.addEventListener("click", () => openCallbackTicket(item.dataset.callbackTicket));
  });

  const initialCallbackItem = callbackQueueItems.find(x => x.classList.contains("active")) || callbackQueueItems[0];
  if (initialCallbackItem) openCallbackTicket(initialCallbackItem.dataset.callbackTicket);


  window.copyCitizenPhone = function(button) {
    const value = button?.dataset?.copyPhone || "";
    if (!value) return;

    const done = () => {
      const old = button.textContent;
      button.textContent = "Kopyalandı";
      setTimeout(() => button.textContent = old, 1200);
    };

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(value).then(done);
      return;
    }

    const tmp = document.createElement("textarea");
    tmp.value = value;
    tmp.style.position = "fixed";
    tmp.style.opacity = "0";
    document.body.appendChild(tmp);
    tmp.select();
    try {
      document.execCommand("copy");
      done();
    } finally {
      tmp.remove();
    }
  };



  // V17: Telefon görüşmesi kurum telefonu üzerinden yapılır.
  // Uygulama yalnız görüşme SONRASI manuel geri bildirim kaydını toplar.
  document.querySelectorAll("[data-v17-feedback-form]").forEach(form => {
    const fields=form.querySelector("[data-v17-conversation-fields]");
    const satisfactionInputs=[...form.querySelectorAll("input[name='memnuniyet']")];
    const duration=form.querySelector("input[name='islem_suresi']");
    const resultInputs=[...form.querySelectorAll("input[name='sonuc']")];

    function syncFeedbackFields(){
      const result=form.querySelector("input[name='sonuc']:checked")?.value || "";
      const talked=result==="bilgilendirildi";

      if(fields) fields.classList.toggle("is-hidden",!talked);

      satisfactionInputs.forEach(input => {
        input.required=talked;
        if(!talked) input.checked=false;
      });

      if(duration){
        duration.required=talked;
        if(!talked) duration.value="";
      }
    }

    resultInputs.forEach(input => input.addEventListener("change",syncFeedbackFields));
    syncFeedbackFields();

    form.addEventListener("submit",event => {
      const result=form.querySelector("input[name='sonuc']:checked")?.value || "";

      if(result==="bilgilendirildi"){
        const rating=form.querySelector("input[name='memnuniyet']:checked");
        const minutes=Number(duration?.value || 0);

        if(!rating || !Number.isFinite(minutes) || minutes<1){
          event.preventDefault();
          alert("Görüşme tamamlandıysa memnuniyet ve işlem süresi bilgilerini girin.");
          return;
        }

        if(!confirm("Görüşme bilgilerini kaydedip vatandaş geri bildirim sürecini kapatmak istiyor musunuz?")){
          event.preventDefault();
        }
      }
    });
  });

})();
