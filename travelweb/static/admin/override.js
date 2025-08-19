// ===== A CLUB TRAVEL — UX helpers =====
(function(){
  // 1) Автосабмит фильтров в списке
  document.querySelectorAll('.changelist-filter select, .changelist-filter input').forEach(el=>{
    el.addEventListener('change', ()=> el.closest('form')?.submit());
  });

  // 2) Горячие клавиши
  document.addEventListener('keydown', (e)=>{
    if (e.key === '/' && !/input|textarea|select/i.test(document.activeElement.tagName)){
      const search = document.querySelector('input[name="q"], .navbar input[type="search"], .navbar .form-control');
      if(search){ e.preventDefault(); search.focus(); search.select(); }
    }
    if (e.altKey && e.key.toLowerCase() === 't'){ window.location.href = '/admin/travelapp/trip/'; }
    if (e.altKey && e.key.toLowerCase() === 's'){ window.location.href = '/admin/travelapp/country/'; }
  });

  // 3) Липкая панель действий, когда прокручиваем таблицу
  const actions = document.querySelector('.actions') || document.querySelector('.object-tools');
  if(actions){ actions.style.position = 'sticky'; actions.style.top = '10px'; actions.style.zIndex = 10; }

  // 4) Превью для ImageField на форме
  const fileInputs = document.querySelectorAll('input[type="file"][name$="hero_image"]');
  fileInputs.forEach(input=>{
    const box = document.createElement('div');
    box.style.marginTop = '8px';
    const img = document.createElement('img');
    img.style.maxHeight = '140px';
    img.style.borderRadius = '12px';
    img.style.boxShadow = '0 10px 24px rgba(0,0,0,.25)';
    box.appendChild(img);
    input.parentNode.appendChild(box);
    input.addEventListener('change', ()=>{
      const f = input.files[0];
      if(!f) return;
      const url = URL.createObjectURL(f);
      img.src = url;
    });
  });

  // 5) Авто‑рост Markdown textarea
  document.querySelectorAll('textarea').forEach(t=>{
    const grow = () => { t.style.height = 'auto'; t.style.height = (t.scrollHeight+6) + 'px'; };
    t.addEventListener('input', grow); grow();
  });
})();
