(function(){
  const data=document.getElementById('rc23-date-data');
  const start=document.getElementById('rc23-start');
  const end=document.getElementById('rc23-end');
  const form=document.getElementById('rc23-filter-form');

  document.querySelectorAll('[data-rc23-preset]').forEach(button=>{
    button.addEventListener('click',()=>{
      if(!data || !start || !end) return;
      const p=button.dataset.rc23Preset;
      if(p==='today'){
        start.value=data.dataset.today;
        end.value=data.dataset.today;
      }else if(p==='7days'){
        start.value=data.dataset.sevenStart;
        end.value=data.dataset.today;
      }else if(p==='month'){
        start.value=data.dataset.monthStart;
        end.value=data.dataset.today;
      }
      form?.submit();
    });
  });

  const download=document.getElementById('rc23-download');
  download?.addEventListener('click',()=>{
    const format=document.getElementById('rc23-format')?.value || 'xlsx';
    const template=download.dataset.urlTemplate || '';
    const url=template.replace('FORMAT',format);
    const query=new URLSearchParams({
      baslangic:start?.value || '',
      bitis:end?.value || ''
    });
    window.location.href=`${url}?${query.toString()}`;
  });
})();
