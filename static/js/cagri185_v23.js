(function(){
  document.querySelectorAll('[data-v23-open-feedback]').forEach(button=>{
    button.addEventListener('click',()=>{
      const id=button.dataset.v23OpenFeedback;
      const info=button.closest('.v21-modal');
      if(info) info.hidden=true;

      const feedback=document.querySelector(`[data-v21-feedback-modal="${id}"]`);
      if(!feedback) return;

      feedback.hidden=false;
      document.body.classList.add('v21-modal-open');

      const reached=feedback.querySelector("input[name='sonuc'][value='bilgilendirildi']");
      if(reached){
        reached.checked=true;
        reached.dispatchEvent(new Event('change',{bubbles:true}));
      }

      setTimeout(()=>{
        feedback.querySelector("input[name='memnuniyet']")?.focus();
      },30);
    });
  });
})();
