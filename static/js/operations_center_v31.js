document.addEventListener("DOMContentLoaded",()=>{
  const holder=document.getElementById("v31-map-data");
  const mapEl=document.getElementById("v31-ops-map");
  if(!holder||!mapEl||typeof L==="undefined") return;
  let points=[];
  try{points=JSON.parse(holder.textContent||"[]");}catch(e){points=[];}
  const map=L.map(mapEl).setView([40.77,29.94],9);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
    maxZoom:19,attribution:"&copy; OpenStreetMap"
  }).addTo(map);

  const bounds=[];
  points.forEach(p=>{
    const marker=L.circleMarker([p.lat,p.lng],{
      radius:p.oncelik_kod==="acil"?9:7,
      weight:2,
      color:p.oncelik_kod==="acil"?"#a43d35":"#315b46",
      fillColor:p.oncelik_kod==="acil"?"#d65b50":"#72a183",
      fillOpacity:.88
    }).addTo(map);
    marker.bindPopup(
      `<strong>${esc(p.is_emri)}</strong><br>${esc(p.ilce)} • ${esc(p.is_turu)}<br>`+
      `${esc(p.oncelik)} • ${esc(p.durum)}<br>Ekip: ${esc(p.ekip)}<br>`+
      `<a href="${esc(p.url)}">İş emrini aç →</a>`
    );
    bounds.push([p.lat,p.lng]);
  });
  if(bounds.length) map.fitBounds(bounds,{padding:[25,25],maxZoom:13});

  function esc(v){
    return String(v??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[ch]));
  }
});