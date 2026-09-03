(function(){
  function initForm(form){
    const resultInputs=[...form.querySelectorAll("input[name='sonuc']")];
    const conversation=form.querySelector('[data-v19-conversation-fields]');
    const survey=form.querySelector('[data-v19-survey-section]');
    const satisfactionInputs=[...form.querySelectorAll("input[name='memnuniyet']")];
    const duration=form.querySelector("input[name='islem_suresi']");

    function selectedResult(){
      return form.querySelector("input[name='sonuc']:checked")?.value || '';
    }

    function sync(){
      const isConversation=selectedResult()==='bilgilendirildi';
      conversation?.classList.toggle('is-hidden',!isConversation);
      survey?.classList.toggle('is-hidden',!isConversation);

      satisfactionInputs.forEach(input=>{ input.required=isConversation; });
      if(duration){ duration.required=isConversation; }

      if(!isConversation){
        satisfactionInputs.forEach(input=>{ input.checked=false; });
        if(duration) duration.value='';
        // Anket alanları opsiyonel ve yalnız görüşme varsa anlamlıdır.
        form.querySelectorAll(
          "input[name='sorun_cozuldu'], input[name='hizmet_hizi'], input[name='bilgilendirme'], input[name='personel_iletisimi'], input[name='genel_puan']"
        ).forEach(input=>{ input.checked=false; });
      }
    }

    resultInputs.forEach(input=>input.addEventListener('change',sync));
    sync();

    form.addEventListener('submit',function(event){
      if(selectedResult()==='bilgilendirildi'){
        const rating=form.querySelector("input[name='memnuniyet']:checked");
        const minutes=Number(duration?.value || 0);
        if(!rating || !Number.isFinite(minutes) || minutes<1){
          event.preventDefault();
          alert('Görüşme tamamlandıysa genel memnuniyet ve işlem süresi bilgilerini girin. Alt anket isteğe bağlıdır.');
        }
      }
    });
  }

  document.querySelectorAll('[data-v19-feedback-form]').forEach(initForm);
})();
