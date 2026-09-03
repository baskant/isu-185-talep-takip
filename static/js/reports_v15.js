(() => {
  const readJSON = id => {
    const el=document.getElementById(id);
    if(!el) return [];
    try{return JSON.parse(el.textContent||"[]")}catch(e){return []}
  };

  const points=readJSON("rv15-map-data");
  const typeData=readJSON("rv15-type-data");
  const trend=readJSON("rv15-trend-data");

  const mapEl=document.getElementById("report-map-v15");
  if(mapEl && window.L){
    const map=L.map(mapEl,{attributionControl:false}).setView([40.765,29.94],10);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19}).addTo(map);

    const bounds=[];
    points.forEach(p=>{
      const lat=Number(p.lat),lng=Number(p.lng),count=Number(p.adet||0);
      if(!Number.isFinite(lat)||!Number.isFinite(lng)) return;
      const radius=Math.min(34,8+(Math.sqrt(Math.max(1,count))*5));
      const circle=L.circleMarker([lat,lng],{
        radius,
        weight:2,
        fillOpacity:.55
      }).addTo(map);
      circle.bindPopup(
        `<div class="rv15-map-popup"><strong>${p.ad}</strong><span>${p.ust}</span>`+
        `<span>${p.adet} talep • ${p.aktif} aktif • ${p.acil} acil</span></div>`
      );
      bounds.push([lat,lng]);
    });
    if(bounds.length) map.fitBounds(bounds,{padding:[30,30],maxZoom:14});
  }

  if(window.Chart){
    const typeCanvas=document.getElementById("rv15-type-chart");
    if(typeCanvas){
      new Chart(typeCanvas,{
        type:"doughnut",
        data:{
          labels:typeData.map(x=>x["is_turu__ad"]),
          datasets:[{data:typeData.map(x=>x.adet)}]
        },
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:"bottom"}}}
      });
    }

    const trendCanvas=document.getElementById("rv15-trend-chart");
    if(trendCanvas){
      new Chart(trendCanvas,{
        type:"line",
        data:{
          labels:trend.map(x=>x.gun),
          datasets:[{label:"Talep",data:trend.map(x=>x.adet),tension:.25}]
        },
        options:{
          responsive:true,maintainAspectRatio:false,
          plugins:{legend:{display:false}},
          scales:{y:{beginAtZero:true,ticks:{precision:0}}}
        }
      });
    }
  }
})();
