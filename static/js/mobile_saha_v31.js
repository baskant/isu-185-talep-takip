document.addEventListener("DOMContentLoaded",()=>{
  // GPS doğrulamalı "Adrese Ulaştım"
  document.querySelectorAll(".m31-gps-form").forEach(form=>{
    form.addEventListener("submit",ev=>{
      if(form.dataset.gpsReady==="1") return;
      ev.preventDefault();
      const button=form.querySelector("button");
      const old=button.textContent;
      button.disabled=true;
      button.textContent="Konum alınıyor...";
      if(!navigator.geolocation){
        alert("Bu cihazda konum servisi kullanılamıyor.");
        button.disabled=false; button.textContent=old; return;
      }
      navigator.geolocation.getCurrentPosition(pos=>{
        form.querySelector('input[name="gps_lat"]').value=pos.coords.latitude.toFixed(6);
        form.querySelector('input[name="gps_lng"]').value=pos.coords.longitude.toFixed(6);
        form.dataset.gpsReady="1";
        form.submit();
      },err=>{
        alert("Konum alınamadı. Telefonun konumunu ve tarayıcı konum iznini açın.");
        button.disabled=false; button.textContent=old;
      },{enableHighAccuracy:true,timeout:15000,maximumAge:0});
    });
  });

  // Bildirim izni
  const enable=document.getElementById("m31-notification-enable");
  if(enable){
    enable.addEventListener("click",async()=>{
      if(!("Notification" in window)){
        alert("Bu tarayıcı sistem bildirimi desteklemiyor. Uygulama içi bildirim listesi çalışmaya devam eder.");
        return;
      }
      const result=await Notification.requestPermission();
      if(result==="granted") enable.classList.add("enabled");
    });
  }

  const list=document.getElementById("m31-notification-list");
  const badge=document.getElementById("m31-unread");
  const seen=new Set([...document.querySelectorAll(".m31-notice[data-id]")].map(x=>String(x.dataset.id)));

  async function markRead(id){
    try{await fetch(`/api/mobil/bildirim/${id}/okundu/`,{method:"POST",headers:{"X-Requested-With":"XMLHttpRequest"}});}catch(e){}
  }
  document.addEventListener("click",e=>{
    const n=e.target.closest(".m31-notice[data-id]");
    if(n && n.classList.contains("unread")){
      n.classList.remove("unread"); markRead(n.dataset.id);
    }
  });

  async function poll(){
    try{
      const r=await fetch("/api/mobil/bildirimler/",{headers:{"X-Requested-With":"XMLHttpRequest"}});
      if(!r.ok) return;
      const d=await r.json();
      if(badge) badge.textContent=d.unread;
      for(const b of [...d.bildirimler].reverse()){
        const id=String(b.id);
        if(seen.has(id)) continue;
        seen.add(id);
        if(list){
          const div=document.createElement("div");
          div.className="m31-notice unread";
          div.dataset.id=id;
          div.innerHTML=`<strong>${escapeHtml(b.baslik)}</strong><span>${escapeHtml(b.mesaj)}</span><small>Yeni</small>`;
          list.prepend(div);
        }
        if("Notification" in window && Notification.permission==="granted"){
          new Notification(b.baslik,{body:b.mesaj,tag:`isu185-${id}`});
        }
      }
    }catch(e){}
  }

  function escapeHtml(v){
    return String(v??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[ch]));
  }
  setInterval(poll,15000);
});