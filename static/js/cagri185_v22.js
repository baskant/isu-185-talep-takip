(function(){
  // Tarayıcı bazı durumlarda <details> açık/kapalı durumunu geri yükleyebilir.
  // Behlül Bey isteğine göre Kapanan İşler her sayfa açılışında kapalı başlar.
  document.querySelectorAll('.v22-archive').forEach(panel=>{
    panel.open=false;
  });

  // Telefon numarasını panoya kopyala.
  function fallbackCopy(text){
    const input=document.createElement('textarea');
    input.value=text;
    input.setAttribute('readonly','');
    input.style.position='fixed';
    input.style.opacity='0';
    document.body.appendChild(input);
    input.select();
    try{ document.execCommand('copy'); }catch(e){}
    input.remove();
  }

  document.querySelectorAll('[data-v22-copy-phone]').forEach(button=>{
    button.addEventListener('click',async()=>{
      const phone=(button.dataset.v22CopyPhone || '').trim();
      if(!phone) return;

      try{
        if(navigator.clipboard && window.isSecureContext){
          await navigator.clipboard.writeText(phone);
        }else{
          fallbackCopy(phone);
        }
      }catch(e){
        fallbackCopy(phone);
      }

      const old=button.textContent;
      button.textContent='Kopyalandı';
      button.classList.add('is-copied');
      setTimeout(()=>{
        button.textContent=old;
        button.classList.remove('is-copied');
      },1200);
    });
  });

  // "Arandı" doğrudan kaydı kapatmaz:
  // sonucu yanlışlıkla tamamlandı saymamak için geri bildirim penceresini açar
  // ve "Görüşüldü" seçeneğini hazırlar. Kaydet sonrası backend:
  // - Görüşüldü => kuyruktan çıkar, Kapanan İşler'e gider
  // - Ulaşılamadı / Tekrar Aranacak => kuyrukta kalır
  document.querySelectorAll('[data-v22-called-open]').forEach(button=>{
    button.addEventListener('click',()=>{
      const id=button.dataset.v22CalledOpen;
      const modal=document.querySelector(`[data-v21-feedback-modal="${id}"]`);
      if(!modal) return;

      const form=modal.querySelector('[data-v19-feedback-form]');
      const reached=form?.querySelector("input[name='sonuc'][value='bilgilendirildi']");
      if(reached){
        reached.checked=true;
        reached.dispatchEvent(new Event('change',{bubbles:true}));
      }

      setTimeout(()=>{
        form?.querySelector("input[name='memnuniyet']")?.focus();
      },30);
    });
  });
})();
