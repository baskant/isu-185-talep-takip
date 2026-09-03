document.addEventListener("DOMContentLoaded",()=>{
  const tabButtons=[...document.querySelectorAll("[data-rc33-tab]")];
  const views=[...document.querySelectorAll("[data-rc33-view]")];

  function activate(name){
    tabButtons.forEach(btn=>btn.classList.toggle("active",btn.dataset.rc33Tab===name));
    views.forEach(view=>{
      const on=view.dataset.rc33View===name;
      view.classList.toggle("active",on);
      view.hidden=!on;
    });
    try{sessionStorage.setItem("isu_v33_report_tab",name)}catch(e){}
    if(name==="detay") requestAnimationFrame(syncWidth);
  }
  tabButtons.forEach(btn=>btn.addEventListener("click",()=>activate(btn.dataset.rc33Tab)));
  try{
    const saved=sessionStorage.getItem("isu_v33_report_tab");
    if(saved==="detay"||saved==="icmal")activate(saved);
  }catch(e){}

  const data=document.getElementById("rc33-date-data");
  const start=document.getElementById("rc33-start");
  const end=document.getElementById("rc33-end");
  const form=document.getElementById("rc33-filter-form");
  document.querySelectorAll("[data-rc33-preset]").forEach(btn=>{
    btn.addEventListener("click",()=>{
      const p=btn.dataset.rc33Preset;
      if(p==="today"){start.value=data.dataset.today;end.value=data.dataset.today;}
      if(p==="7days"){start.value=data.dataset.sevenStart;end.value=data.dataset.today;}
      if(p==="month"){start.value=data.dataset.monthStart;end.value=data.dataset.today;}
      form.submit();
    });
  });

  function setupDownload(buttonId,selectId){
    const btn=document.getElementById(buttonId), select=document.getElementById(selectId);
    if(!btn||!select)return;
    btn.addEventListener("click",()=>{
      const url=btn.dataset.urlTemplate.replace("FORMAT",select.value);
      const qs=new URLSearchParams({baslangic:start.value,bitis:end.value});
      window.location.href=url+"?"+qs.toString();
    });
  }
  setupDownload("rc33-icmal-download","rc33-icmal-format");
  setupDownload("rc33-detay-download","rc33-detay-format");

  const top=document.getElementById("rc33-top-scroll");
  const bottom=document.getElementById("rc33-table-scroll");
  const table=document.getElementById("rc33-detail-table");
  let syncing=false;
  function syncWidth(){
    if(!top||!bottom||!table)return;
    top.firstElementChild.style.width=table.scrollWidth+"px";
  }
  top?.addEventListener("scroll",()=>{
    if(syncing)return; syncing=true; bottom.scrollLeft=top.scrollLeft; syncing=false;
  });
  bottom?.addEventListener("scroll",()=>{
    if(syncing)return; syncing=true; top.scrollLeft=bottom.scrollLeft; syncing=false;
  });
  window.addEventListener("resize",syncWidth);
  syncWidth();
});