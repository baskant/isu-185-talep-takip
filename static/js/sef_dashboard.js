(() => {
  const el = document.getElementById("coord-map");
  if (el && typeof L !== "undefined") {
    const map = L.map("coord-map").setView([40.7656, 29.9408], 10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    const points = JSON.parse(
      document.getElementById("coord-map-data")?.textContent || "[]"
    );

    const color = status => {
      if (status === "tamamlandi") return "#3D8B58";
      if (["sahaya_atandi","kabul_edildi","yolda","yerinde","islemde","onay_bekliyor"].includes(status)) {
        return "#CF8A2E";
      }
      return "#C94B4B";
    };

    const bounds = [];
    points.forEach(x => {
      const p = [Number(x.lat), Number(x.lng)];
      if (!Number.isFinite(p[0]) || !Number.isFinite(p[1])) return;
      bounds.push(p);
      L.circleMarker(p, {
        radius: 8,
        color: color(x.durum),
        fillColor: color(x.durum),
        fillOpacity: .82,
        weight: 2
      }).addTo(map).bindPopup(
        `<strong>${x.no}</strong><br>${x.ilce}<br>${x.tur}<br><a href="/talep/${x.id}/">Talebi Gör</a>`
      );
    });

    if (bounds.length === 1) map.setView(bounds[0], 14);
    if (bounds.length > 1) map.fitBounds(bounds, {padding: [25,25]});
  }

  const root = document.querySelector("[data-live-coordinator]");
  if (!root) return;

  const statusProgress = (node, status) => {
    const steps = [...node.querySelectorAll(".mini-progress span")];
    const doneIndex = {
      sahaya_atandi: -1,
      kabul_edildi: 0,
      yolda: 1,
      yerinde: 2,
      islemde: 3,
      onay_bekliyor: 4,
      tamamlandi: 5
    }[status] ?? -1;
    steps.forEach((s, i) => s.classList.toggle("done", i <= doneIndex));
  };

  async function refresh() {
    try {
      const res = await fetch("/api/talepler/operasyon-ozet/", {
        headers: {"X-Requested-With": "XMLHttpRequest"}
      });
      if (!res.ok) return;
      const data = await res.json();

      const countMap = {
        bekleyen: "live-count-bekleyen",
        sahada: "live-count-sahada",
        onay_bekleyen: "live-count-onay",
        tamam: "live-count-tamam",
        acil: "live-count-acil"
      };
      Object.entries(countMap).forEach(([key, id]) => {
        const node = document.getElementById(id);
        if (node) node.textContent = data.counts?.[key] ?? node.textContent;
      });

      const currentCards = [...document.querySelectorAll("[data-live-ticket]")];
      const currentIds = currentCards.map(x => Number(x.dataset.liveTicket)).sort((a,b)=>a-b);
      const newIds = (data.items || []).map(x => Number(x.id)).sort((a,b)=>a-b);

      // Yeni atama/tamamlama ile kart seti değişirse paneli temiz şekilde yeniden çiz.
      if (JSON.stringify(currentIds) !== JSON.stringify(newIds)) {
        window.location.reload();
        return;
      }

      (data.items || []).forEach(item => {
        const card = document.querySelector(`[data-live-ticket="${item.id}"]`);
        if (!card) return;

        const badge = card.querySelector("[data-live-status]");
        if (badge) {
          badge.textContent = item.durum_label;
          badge.className = `badge status-${item.durum}`;
        }
        const last = card.querySelector("[data-live-last]");
        const time = card.querySelector("[data-live-time]");
        if (last) last.textContent = item.son_hareket || "Saha operasyonu güncellendi.";
        if (time) time.textContent = item.son_hareket_tarih || "";
        statusProgress(card, item.durum);

        const tableBadge = document.querySelector(`[data-ticket-status="${item.id}"]`);
        if (tableBadge) {
          tableBadge.textContent = item.durum_label;
          tableBadge.className = `badge status-${item.durum}`;
        }
      });
    } catch (e) {}
  }

  setInterval(refresh, 8000);
})();
