document.addEventListener("DOMContentLoaded",()=>{
  const box=document.querySelector(".v34-workorder-map");
  const el=document.getElementById("v34-workorder-map-canvas");
  if(!box||!el||!window.L)return;
  const cv=v=>Number(String(v??"").replace(",","."));
  const lat=cv(box.dataset.targetLat),lng=cv(box.dataset.targetLng);
  if(!Number.isFinite(lat)||!Number.isFinite(lng))return;

  const map=L.map(el,{zoomControl:true,attributionControl:true}).setView([lat,lng],16);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
    maxZoom:19,
    attribution:"© OpenStreetMap"
  }).addTo(map);

  L.marker([lat,lng]).addTo(map).bindPopup("Arıza noktası").openPopup();
});
