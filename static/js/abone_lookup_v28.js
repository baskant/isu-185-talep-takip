document.addEventListener("DOMContentLoaded",()=>{
  const btn=document.getElementById("v28-abone-sorgula");
  const input=document.getElementById("id_abone_no");
  const out=document.getElementById("v28-abone-sonuc");
  if(!btn||!input||!out)return;
  btn.addEventListener("click",async()=>{
    const no=input.value.trim();
    if(!no){out.textContent="Önce abone numarası girin.";out.className="error";return;}
    out.textContent="Sorgulanıyor..."; out.className="";
    try{
      const r=await fetch(`/api/abone-sorgula/?no=${encodeURIComponent(no)}`,{headers:{"X-Requested-With":"XMLHttpRequest"}});
      const d=await r.json();
      if(!r.ok||!d.ok)throw new Error(d.message||"Abone bulunamadı.");
      const set=(id,val)=>{const el=document.getElementById(id);if(el&&val)el.value=val;};
      set("id_vatandas_ad",d.ad); set("id_vatandas_soyad",d.soyad);
      set("id_telefon",d.telefon); set("id_eposta",d.eposta); set("id_kapi_no",d.kapi_no);
      out.textContent=`✓ ${d.abone_no} • ${d.ad} ${d.soyad} • Sayaç: ${d.sayac_no||"-"} • ${d.adres||"Adres kaydı yok"}`;
      out.className="success";
    }catch(e){out.textContent=e.message;out.className="error";}
  });
});