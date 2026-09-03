(function(){
  let activeMap=null;

  function closeModal(modal){
    if(!modal) return;
    modal.hidden=true;
    document.body.classList.remove('v21-modal-open');
    if(activeMap){
      activeMap.remove();
      activeMap=null;
    }
    modal.querySelectorAll('[data-v21-mini-map]').forEach(el=>{
      el.hidden=true;
      el.innerHTML='';
      delete el.dataset.ready;
    });
  }

  function openModal(modal){
    if(!modal) return;
    modal.hidden=false;
    document.body.classList.add('v21-modal-open');
    const close=modal.querySelector('.v21-modal-close');
    setTimeout(()=>close?.focus(),10);
  }

  document.querySelectorAll('[data-v21-info-open]').forEach(button=>{
    button.addEventListener('click',()=>{
      openModal(document.querySelector(`[data-v21-info-modal="${button.dataset.v21InfoOpen}"]`));
    });
  });

  document.querySelectorAll('[data-v21-feedback-open]').forEach(button=>{
    button.addEventListener('click',()=>{
      openModal(document.querySelector(`[data-v21-feedback-modal="${button.dataset.v21FeedbackOpen}"]`));
    });
  });

  document.querySelectorAll('[data-v21-close]').forEach(button=>{
    button.addEventListener('click',()=>closeModal(button.closest('.v21-modal')));
  });

  document.addEventListener('keydown',event=>{
    if(event.key!=='Escape') return;
    const modal=[...document.querySelectorAll('.v21-modal')].find(x=>!x.hidden);
    if(modal) closeModal(modal);
  });

  document.querySelectorAll('[data-v21-map-toggle]').forEach(button=>{
    button.addEventListener('click',()=>{
      const modal=button.closest('.v21-modal-card');
      const el=modal?.querySelector('[data-v21-mini-map]');
      if(!el || typeof L==='undefined') return;
      const lat=parseFloat(button.dataset.lat || '');
      const lng=parseFloat(button.dataset.lng || '');
      if(!Number.isFinite(lat) || !Number.isFinite(lng)) return;

      if(!el.hidden){
        if(activeMap){ activeMap.remove(); activeMap=null; }
        el.innerHTML='';
        el.hidden=true;
        delete el.dataset.ready;
        button.textContent=`${lat}, ${lng} • Haritada Aç`;
        return;
      }

      el.hidden=false;
      button.textContent=`${lat}, ${lng} • Haritayı Kapat`;
      activeMap=L.map(el,{zoomControl:true,attributionControl:false}).setView([lat,lng],16);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19}).addTo(activeMap);
      L.marker([lat,lng]).addTo(activeMap);
      setTimeout(()=>activeMap?.invalidateSize(),80);
    });
  });
})();
