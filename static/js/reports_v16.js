(() => {
  const page=document.querySelector(".report-v16");
  const mapEl=document.getElementById("report-map-v16");

  if(mapEl && window.L){
    const map=L.map(mapEl).setView([40.7656,29.9408],10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
      maxZoom:19,
      attribution:"&copy; OpenStreetMap contributors"
    }).addTo(map);

    let points=[];
    try{
      points=JSON.parse(document.getElementById("r16-map-data")?.textContent||"[]");
    }catch(e){points=[]}

    const statusClass=status=>{
      if(status==="tamamlandi") return "map-status-complete";
      if(status==="onay_bekliyor") return "map-status-approval";
      if(["sahaya_atandi","kabul_edildi","yolda","yerinde","islemde"].includes(status)){
        return "map-status-progress";
      }
      return "map-status-waiting";
    };

    const priorityClass=priority=>({
      dusuk:"map-priority-low",
      normal:"map-priority-normal",
      yuksek:"map-priority-high",
      acil:"map-priority-urgent"
    }[priority]||"map-priority-normal");

    const markers=[];
    points.forEach(x=>{
      const lat=Number(x.lat),lng=Number(x.lng);
      if(!Number.isFinite(lat)||!Number.isFinite(lng)) return;

      const icon=L.divIcon({
        className:"isu-ticket-marker-wrap",
        html:`<div class="isu-ticket-marker ${statusClass(x.durum)}">
                <span class="isu-ticket-marker-core ${priorityClass(x.oncelik)}"></span>
              </div>`,
        iconSize:[30,38],
        iconAnchor:[15,36],
        popupAnchor:[0,-32]
      });

      const marker=L.marker([lat,lng],{icon}).addTo(map);
      marker.bindPopup(`
        <div class="map-popup-card">
          <strong>${x.no}</strong>
          <span>${x.ilce} / ${x.mahalle}</span>
          <span>${x.yol||""}</span>
          <b>${x.tur}</b>
          <small>${x.alt_tur}</small>
          <div class="map-popup-meta">
            <em>${x.durum_label}</em>
            <em>${x.oncelik_label}</em>
          </div>
          <small>Son güncelleme: ${x.guncelleme}</small>
          <a href="/talep/${x.id}/">Talep detayını aç →</a>
        </div>
      `);
      markers.push(marker);
    });

    if(markers.length===1){
      map.setView(markers[0].getLatLng(),14);
    }else if(markers.length>1){
      map.fitBounds(L.featureGroup(markers).getBounds().pad(.1),{maxZoom:13});
    }
  }

  // Tam otomatik rapor:
  // Yeni talep / durum değişimi / şef onayı / 185 geri dönüşü olursa
  // veritabanı sürümü değişir ve rapor kendi kendine yenilenir.
  if(page){
    const liveUrl=page.dataset.liveUrl;
    const originalVersion=page.dataset.reportVersion||"";
    const chip=document.querySelector(".r16-live-chip");
    const lastCheck=document.getElementById("r16-last-check");
    let refreshing=false;

    async function checkForChanges(){
      if(!liveUrl || refreshing || document.hidden) return;
      try{
        const response=await fetch(liveUrl,{
          headers:{"X-Requested-With":"XMLHttpRequest"},
          cache:"no-store"
        });
        if(!response.ok) return;
        const data=await response.json();

        if(lastCheck && data.checked_at){
          lastCheck.textContent=`Kontrol: ${data.checked_at}`;
        }

        if(data.version && data.version!==originalVersion){
          refreshing=true;
          if(chip){
            chip.classList.add("refreshing");
            const label=chip.querySelector("strong");
            if(label) label.textContent="YENİ VERİ GELDİ";
          }
          if(lastCheck) lastCheck.textContent="Rapor otomatik güncelleniyor...";
          setTimeout(()=>window.location.reload(),500);
        }
      }catch(e){
        if(lastCheck) lastCheck.textContent="Canlı bağlantı yeniden denenecek";
      }
    }

    setInterval(checkForChanges,5000);
    checkForChanges();
  }
})();
