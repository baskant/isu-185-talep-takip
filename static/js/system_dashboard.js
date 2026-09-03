(() => {
  const el = document.getElementById("system-map");
  if (!el || typeof L === "undefined") return;

  const map = L.map("system-map").setView([40.7656, 29.9408], 10);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  const points = JSON.parse(
    document.getElementById("map-data")?.textContent || "[]"
  );

  const statusClass = status => {
    if (status === "tamamlandi") return "map-status-complete";
    if (status === "onay_bekliyor") return "map-status-approval";
    if (["sahaya_atandi", "kabul_edildi", "yolda", "yerinde", "islemde"].includes(status)) {
      return "map-status-progress";
    }
    return "map-status-waiting";
  };

  const priorityClass = priority => ({
    dusuk: "map-priority-low",
    normal: "map-priority-normal",
    yuksek: "map-priority-high",
    acil: "map-priority-urgent"
  }[priority] || "map-priority-normal");

  const markerList = [];

  points.forEach(x => {
    const lat = Number(x.lat);
    const lng = Number(x.lng);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    const icon = L.divIcon({
      className: "isu-ticket-marker-wrap",
      html: `
        <div class="isu-ticket-marker ${statusClass(x.durum)}">
          <span class="isu-ticket-marker-core ${priorityClass(x.oncelik)}"></span>
        </div>
      `,
      iconSize: [30, 38],
      iconAnchor: [15, 36],
      popupAnchor: [0, -32]
    });

    const marker = L.marker([lat, lng], {icon}).addTo(map);

    marker.bindPopup(`
      <div class="map-popup-card">
        <strong>${x.no}</strong>
        <span>${x.ilce} / ${x.mahalle}</span>
        <b>${x.tur}</b>
        <small>${x.alt_tur}</small>
        <div class="map-popup-meta">
          <em>${x.durum_label}</em>
          <em class="priority-text-${x.oncelik}">${x.oncelik_label}</em>
        </div>
        <a href="/talep/${x.id}/">Talep detayını aç →</a>
      </div>
    `);

    markerList.push(marker);
  });

  if (markerList.length === 1) {
    map.setView(markerList[0].getLatLng(), 14);
  } else if (markerList.length > 1) {
    const group = L.featureGroup(markerList);
    map.fitBounds(group.getBounds().pad(0.12), {maxZoom: 13});
  }

  if (window.Chart) {
    const a = JSON.parse(document.getElementById("ilce-data")?.textContent || "[]");
    const b = JSON.parse(document.getElementById("tur-data")?.textContent || "[]");
    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {legend: {display: false}}
    };

    new Chart(document.getElementById("districtChart"), {
      type: "bar",
      data: {
        labels: a.map(x => x["ilce__ad"]),
        datasets: [{data: a.map(x => x.adet)}]
      },
      options
    });

    new Chart(document.getElementById("typeChart"), {
      type: "doughnut",
      data: {
        labels: b.map(x => x["is_turu__ad"]),
        datasets: [{data: b.map(x => x.adet)}]
      },
      options: {responsive: true, maintainAspectRatio: false}
    });
  }
})();
