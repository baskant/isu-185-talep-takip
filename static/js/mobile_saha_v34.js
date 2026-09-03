document.addEventListener("DOMContentLoaded",()=>{
  // GPS doğrulamalı "Adrese Ulaştım"
  document.querySelectorAll(".m31-gps-form").forEach(form=>{
    form.addEventListener("submit",ev=>{
      if(form.dataset.gpsReady==="1") return;
      ev.preventDefault();
      const button=form.querySelector("button");
      const old=button.textContent;
      button.disabled=true; button.textContent="Konum alınıyor...";
      if(!navigator.geolocation){ alert("Bu cihazda konum servisi kullanılamıyor."); button.disabled=false; button.textContent=old; return; }
      navigator.geolocation.getCurrentPosition(pos=>{
        form.querySelector('input[name="gps_lat"]').value=pos.coords.latitude.toFixed(6);
        form.querySelector('input[name="gps_lng"]').value=pos.coords.longitude.toFixed(6);
        form.dataset.gpsReady="1"; form.submit();
      },()=>{
        alert("Konum alınamadı. Cihaz konumunu ve site konum iznini kontrol edin.");
        button.disabled=false; button.textContent=old;
      },{enableHighAccuracy:true,timeout:15000,maximumAge:0});
    });
  });

  // Kart içinde harita. Google Maps'e sayfa geçişi yoktur.
  const maps=new Map();
  const parseCoord=v=>Number(String(v??"").replace(",","."));
  document.querySelectorAll(".m34-map-toggle").forEach(btn=>{
    btn.addEventListener("click",()=>{
      const panel=document.getElementById(btn.dataset.mapTarget);
      if(!panel) return;
      const opening=panel.hidden;
      panel.hidden=!opening;
      btn.textContent=opening ? "⌖ Haritayı Gizle" : "⌖ Haritada Göster";
      if(!opening) return;
      const lat=parseCoord(panel.dataset.lat), lng=parseCoord(panel.dataset.lng);
      const canvas=panel.querySelector(".m34-map-canvas");
      if(!Number.isFinite(lat)||!Number.isFinite(lng)||!canvas){
        panel.innerHTML='<div class="m34-map-error">Konum bilgisi okunamadı.</div>'; return;
      }
      if(window.L){
        if(!maps.has(panel.id)){
          const map=L.map(canvas,{zoomControl:true,attributionControl:true}).setView([lat,lng],16);
          L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap"}).addTo(map);
          L.marker([lat,lng]).addTo(map).bindPopup(panel.dataset.title||"Arıza noktası").openPopup();
          maps.set(panel.id,map);
        }
        setTimeout(()=>maps.get(panel.id)?.invalidateSize(),80);
      }else{
        canvas.innerHTML='<div class="m34-map-error">Harita yüklenemedi.</div>';
      }
    });
  });

  // V34 saha bildirim modalı: sayfa açılır açılmaz öndedir; Tamam sadece kapatır.
  const overlay=document.getElementById("m34-notification-overlay");
  const openButton=document.getElementById("m34-notification-button");
  const okButton=document.getElementById("m34-modal-ok");
  const badge=document.getElementById("m31-unread");
  const content=document.getElementById("m34-modal-content");
  let lastActive=Number(badge?.textContent||0);

  function openModal(){ if(!overlay) return; overlay.classList.add("open"); document.body.classList.add("m34-modal-open"); }
  function closeModal(){ if(!overlay) return; overlay.classList.remove("open"); document.body.classList.remove("m34-modal-open"); }
  openButton?.addEventListener("click",openModal);
  okButton?.addEventListener("click",closeModal);
  openModal();

  const escapeHtml=v=>String(v??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[ch]));
  function renderModal(items){
    if(!content) return;
    if(!items.length){ content.innerHTML='<div class="m34-no-work"><span>✓</span><h2>Şu an atanmış aktif iş yok</h2></div>'; return; }
    content.innerHTML=`<h2>${items.length===1?"1 iş emri atandı / aktif":items.length+" iş emri atandı / aktif"}</h2><div class="m34-modal-work-list">${items.map(b=>`<div class="m34-modal-work"><strong>${escapeHtml(b.baslik)}</strong><span>${escapeHtml(b.mesaj)}</span><small>${escapeHtml(b.is_emri_no)} • ${escapeHtml(b.talep_no)}</small></div>`).join("")}</div>`;
  }

  async function poll(){
    try{
      const r=await fetch("/api/mobil/bildirimler/",{headers:{"X-Requested-With":"XMLHttpRequest"}});
      if(!r.ok) return;
      const d=await r.json();
      const active=Number(d.active_count??0);
      if(badge) badge.textContent=active;
      renderModal(d.bildirimler||[]);
      if(active>lastActive) openModal();
      lastActive=active;
    }catch(_){ }
  }
  setInterval(poll,15000);
});
