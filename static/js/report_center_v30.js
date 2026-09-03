document.addEventListener("DOMContentLoaded",()=>{
  const buttons=[...document.querySelectorAll("[data-rc30-tab]")];
  const panels=[...document.querySelectorAll("[data-rc30-panel]")];

  function activate(name){
    buttons.forEach(b=>{
      const on=b.dataset.rc30Tab===name;
      b.classList.toggle("active",on);
      b.setAttribute("aria-selected",on?"true":"false");
    });
    panels.forEach(p=>{
      const on=p.dataset.rc30Panel===name;
      p.classList.toggle("active",on);
      p.hidden=!on;
    });
    try{sessionStorage.setItem("isu_rc30_tab",name)}catch(e){}
  }
  buttons.forEach(b=>b.addEventListener("click",()=>activate(b.dataset.rc30Tab)));
  try{
    const saved=sessionStorage.getItem("isu_rc30_tab");
    if(saved==="detay"||saved==="icmal")activate(saved);
  }catch(e){}

  const data=document.getElementById("rc30-date-data");
  const start=document.getElementById("rc30-start");
  const end=document.getElementById("rc30-end");
  const form=document.getElementById("rc30-filter-form");
  document.querySelectorAll("[data-rc30-preset]").forEach(btn=>{
    btn.addEventListener("click",()=>{
      const p=btn.dataset.rc30Preset;
      if(p==="today"){start.value=data.dataset.today;end.value=data.dataset.today;}
      if(p==="7days"){start.value=data.dataset.sevenStart;end.value=data.dataset.today;}
      if(p==="month"){start.value=data.dataset.monthStart;end.value=data.dataset.today;}
      form.submit();
    });
  });

  function download(btnId,selectId){
    const btn=document.getElementById(btnId);
    const select=document.getElementById(selectId);
    if(!btn||!select)return;
    btn.addEventListener("click",()=>{
      let url=btn.dataset.urlTemplate.replace("FORMAT",select.value);
      const qs=new URLSearchParams({baslangic:start.value,bitis:end.value});
      window.location.href=url+"?"+qs.toString();
    });
  }
  download("rc30-icmal-download","rc30-icmal-format");
  download("rc30-detay-download","rc30-detay-format");
});