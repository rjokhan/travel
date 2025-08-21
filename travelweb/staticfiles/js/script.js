// ================== DOM ==================
const modal        = document.getElementById('createUserModal');
const nameInput    = document.getElementById('name');
const phoneInput   = document.getElementById('phone');
const hiEl         = document.getElementById('hi');

const weatherText  = document.getElementById('weatherText');
const weatherIconEl= document.querySelector('.weather .icon');

const locationBadge= document.getElementById('locationBadge');

const searchTrigger= document.getElementById('searchTrigger');
const overlay      = document.getElementById('searchOverlay');
const field        = document.getElementById('searchField');
const closeBtn     = document.getElementById('searchClose');
const form         = document.getElementById('searchForm');

const fab          = document.getElementById('editProfileFab');

document.querySelectorAll('[data-close]')
  .forEach(b => b.addEventListener('click', closeModal));

// save button может отсутствовать на части страниц
const saveBtn = document.getElementById('saveUserBtn');
if (saveBtn) saveBtn.addEventListener('click', saveUser);
if (fab) fab.addEventListener('click', openModal);

function openModal(){
  if (!modal) return;
  modal.classList.add('open');
  setTimeout(()=> nameInput && nameInput.focus(), 50);
}
function closeModal(){
  if (!modal) return;
  modal.classList.remove('open');
}


// ================== USER INIT ==================
(function initUser(){
  try{
    const saved = localStorage.getItem('aclub_user');
    if (saved) {
      const user = JSON.parse(saved);
      if (user?.name && hiEl) hiEl.textContent = `Hi, ${user.name} 👋`;
    } else {
      // модалка есть только на index — на других страницах просто пропускаем
      if (modal) openModal();
    }
  }catch{/* ignore */}
})();

function saveUser(){
  if (!nameInput) return;
  const name  = (nameInput.value  || '').trim();
  const phone = (phoneInput?.value || '').trim();
  if (!name){
    alert('Укажите имя.');
    return;
  }
  const user = { name, phone };
  try{ localStorage.setItem('aclub_user', JSON.stringify(user)); }catch{}
  if (hiEl) hiEl.textContent = `Hi, ${user.name} 👋`;
  closeModal();
}


// ================== WEATHER ==================
function wmoToEmoji(code, isDay){
  const sun='☀️', moon='🌙', sunCloud='🌤️', cloud='☁️', fog='🌫️',
        drizzle='🌦️', rain='🌧️', snow='❄️', thunder='⛈️';
  if (code === 0) return isDay ? sun : moon;
  if (code === 1 || code === 2) return sunCloud;
  if (code === 3) return cloud;
  if (code === 45 || code === 48) return fog;
  if (code >= 51 && code <= 57) return drizzle;
  if ((code >= 61 && code <= 67) || (code >= 80 && code <= 82)) return rain;
  if ((code >= 71 && code <= 77) || code === 85 || code === 86) return snow;
  if (code >= 95 && code <= 99) return thunder;
  return sunCloud;
}

function updateWeatherUI(temp, code, isDay){
  if (weatherText) weatherText.textContent = `${Math.round(Number(temp ?? 15))}°C`;
  if (weatherIconEl){
    const emoji = wmoToEmoji(Number(code ?? 2), Number(isDay) === 1);
    weatherIconEl.textContent = emoji;
    weatherIconEl.setAttribute('aria-label', `Weather ${emoji}`);
    weatherIconEl.setAttribute('title', emoji);
  }
}


// ================== LOCATION BADGE ==================
function countryCodeToFlagEmoji(cc) {
  if (!cc) return '';
  cc = cc.trim().toUpperCase();
  if (cc.length !== 2) return '';
  const codePoints = [...cc].map(ch => 127397 + ch.charCodeAt());
  return String.fromCodePoint(...codePoints);
}

async function setLocationBadge(lat, lon){
  if (!locationBadge) return;
  try{
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}&accept-language=en`
    );
    const j = await res.json();

    const city    = j.address?.city || j.address?.town || j.address?.village || j.address?.county;
    const country = j.address?.country || '';
    let countryCode = (j.address?.country_code || '').trim().toLowerCase();
    if (countryCode === 'uk') countryCode = 'gb';

    const text = [city, country].filter(Boolean).join(', ') || 'Your location';

    let flagMarkup = '';
    if (countryCode){
      const src  = `https://flagcdn.com/24x18/${countryCode}.png`;
      const src2 = `https://flagcdn.com/48x36/${countryCode}.png`;
      const emoji= countryCodeToFlagEmoji(countryCode);
      flagMarkup =
        `<img class="flag-img" src="${src}" srcset="${src2} 2x" width="24" height="18" alt="${country} flag" title="${emoji || country.toUpperCase()}">`;
    }

    locationBadge.innerHTML = `${flagMarkup}<span>${text}</span>`;
  }catch(e){
    console.warn('Reverse geocoding failed:', e);
    locationBadge.textContent = 'Your location';
  }
}


// ================== GEO + WEATHER FLOW ==================
(function initGeo(){
  if (!locationBadge) return;

  const SECURE = window.isSecureContext || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

  locationBadge.textContent = 'Loading location…';

  if (!SECURE){
    locationBadge.textContent = 'Enable HTTPS for location';
    updateWeatherUI(15, 2, 1);
    return;
  }

  function onSuccess(pos){
    const { latitude: lat, longitude: lon } = pos.coords;

    // Weather
    (async () => {
      try{
        const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code,is_day`;
        const r = await fetch(url);
        const j = await r.json();
        updateWeatherUI(j?.current?.temperature_2m, j?.current?.weather_code, j?.current?.is_day);
      }catch{
        updateWeatherUI(15, 2, 1);
      }
    })();

    // Badge
    setLocationBadge(lat, lon);
  }

  function onError(err){
    if (err && err.code === err.PERMISSION_DENIED) {
      locationBadge.textContent = 'Location blocked';
    } else if (err && err.code === err.POSITION_UNAVAILABLE) {
      locationBadge.textContent = 'Location unavailable';
    } else {
      locationBadge.textContent = 'Unknown location';
    }
    updateWeatherUI(15, 2, 1);
  }

  function requestPosition(){
    if (!('geolocation' in navigator)) {
      locationBadge.textContent = 'Geolocation not supported';
      updateWeatherUI(15, 2, 1);
      return;
    }
    navigator.geolocation.getCurrentPosition(onSuccess, onError, {
      enableHighAccuracy:true, timeout:8000, maximumAge:60_000
    });
  }

  if (navigator.permissions?.query){
    navigator.permissions.query({ name: 'geolocation' }).then(p => {
      if (p.state === 'denied') {
        locationBadge.textContent = 'Location blocked';
        updateWeatherUI(15, 2, 1);
        return;
      }
      requestPosition();
      p.onchange = () => {
        if (p.state === 'denied') {
          locationBadge.textContent = 'Location blocked';
          updateWeatherUI(15, 2, 1);
        } else {
          locationBadge.textContent = 'Loading location…';
          requestPosition();
        }
      };
    }).catch(requestPosition);
  } else {
    requestPosition();
  }
})();


// ================== SEARCH OVERLAY ==================
function openSearch(){
  if (!overlay) return;
  overlay.classList.add('open');
  overlay.setAttribute('aria-hidden','false');
  setTimeout(()=> field && field.focus(), 120);
}
function closeSearch(){
  if (!overlay) return;
  overlay.classList.remove('open');
  overlay.setAttribute('aria-hidden','true');
}

searchTrigger?.addEventListener('click', openSearch);
closeBtn?.addEventListener('click', closeSearch);
overlay?.addEventListener('click', (e)=>{ if(e.target === overlay) closeSearch(); });
document.addEventListener('keydown', (e)=>{ if(e.key === 'Escape') closeSearch(); });
form?.addEventListener('submit', (e)=>{ e.preventDefault(); /* TODO: поиск */ });


// ====== Trip slider helpers ======

// 1) высота левой капсулы = фактическая высота карточки
function syncTripPills(){
  document.querySelectorAll('.trip-card').forEach(card => {
    const h = Math.round(card.getBoundingClientRect().height || 0);
    const clamped = Math.max(86, Math.min(h - 8, 160));
    card.style.setProperty('--cardH', clamped + 'px');
  });
}
window.addEventListener('load',   syncTripPills);
window.addEventListener('resize', syncTripPills);
document.fonts?.ready?.then(syncTripPills);

// 2) избранное toggle
document.addEventListener('click', (e)=>{
  const btn = e.target.closest?.('.trip-fav');
  if(!btn) return;
  btn.classList.toggle('is-active');
});


// Уважаем «reduce motion»
const v = document.getElementById('bgCircleVideo');
if (v && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  v.removeAttribute('autoplay');
  try{ v.pause(); }catch{}
}

// Аватар в навбаре (без ошибок, если элемента нет)
(function setNavAvatar(){
  const el = document.getElementById('navAvatar');
  if (!el) return;
  const url = localStorage.getItem('aclub_avatar') || '../media/avatar-default.jpg';
  el.style.backgroundImage = `url("${url}")`;
})();


// ===== Desktop hint (всегда показываем не на телефоне) =====
(function deviceHintInit(){
  try{
    const ua = navigator.userAgent || navigator.vendor || window.opera || '';
    const isIPadOS  = (/iPad|Macintosh/i.test(ua) && (navigator.maxTouchPoints || 0) > 1);
    const isPhoneUA = /iPhone|Android.+Mobile|Windows Phone|IEMobile|Opera Mini|Mobi/i.test(ua);
    const isPhone   = isPhoneUA && !isIPadOS;
    if (isPhone) return;

    const el  = document.getElementById('deviceHint');
    const btn = document.getElementById('deviceHintContinue');
    if (!el || !btn) return;

    el.classList.add('open');
    document.body.classList.add('is-device-hint-open');

    btn.addEventListener('click', () => {
      el.classList.remove('open');
      document.body.classList.remove('is-device-hint-open');
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && el.classList.contains('open')) {
        el.classList.remove('open');
        document.body.classList.remove('is-device-hint-open');
      }
    });
  }catch{/* ignore */}
})();



(function(){
    const $ = s => document.querySelector(s);
    const $$ = s => document.querySelectorAll(s);
    const show = el => el && el.classList.remove('hidden');
    const hide = el => el && el.classList.add('hidden');
    const on  = (el, ev, fn) => el && el.addEventListener(ev, fn);

    const authModal = $('#authModal');
    const openBtn   = $('#openAuthBtn');
    const errorBox  = $('#authError');

    // Получение CSRF из cookie
    function getCookie(name){
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if(parts.length === 2) return parts.pop().split(';').shift();
    }
    function csrfHeaders() {
      const csrftoken = getCookie('csrftoken');
      return csrftoken ? {'X-CSRFToken': csrftoken} : {};
    }
    function setError(msg){
      if(!msg){ hide(errorBox); errorBox.textContent=''; return; }
      errorBox.textContent = msg;
      show(errorBox);
    }

    // Открытие/закрытие модалки
    on(openBtn, 'click', ()=> {
      resetForms();
      show(authModal);
    });
    $$('#authModal [data-ac-close]').forEach(b=>on(b,'click',()=> hide(authModal)));

    // Табы
    $$('.ac-tab').forEach(btn=>{
      on(btn,'click',()=>{
        $$('.ac-tab').forEach(b=> b.classList.remove('ac-tab--active'));
        btn.classList.add('ac-tab--active');
        const target = btn.dataset.tab;
        $$('.ac-pane').forEach(p=> p.classList.toggle('hidden', p.dataset.pane !== target));
        setError('');
      });
    });

    // ====== LOGIN ======
    on($('#formLogin'),'submit', async (e)=>{
      e.preventDefault();
      setError('');
      const fd = new FormData(e.target);
      try{
        const r = await fetch('/auth/login/', {
          method:'POST',
          headers: csrfHeaders(),
          body: fd
        });
        const data = await r.json();
        if(!data.successful){ setError(data.message || 'Ошибка входа'); return; }
        hide(authModal);
        await postLoginUIUpdate(data);
      }catch(err){
        setError('Сеть недоступна. Попробуйте ещё раз.');
      }
    });

    // ====== REGISTER FLOW ======
    const reg1 = $('#regStep1');   // имя, почта, телефон, пароль -> получить код
    const reg2 = $('#regStep2');   // ввод кода
    const reg3 = $('#regStep3');   // аватар

    let regEmail = '';
    let regPassword = '';
    let regName = '';
    let regPhone = '';

    function resetForms(){
      // Чистим все поля/ошибки и возвращаем первый шаг регистрации
      $('#formLogin')?.reset();
      reg1?.reset(); reg2?.reset(); reg3?.reset();
      show(reg1); hide(reg2); hide(reg3);
      setError('');
    }

    // Step 1 → запрос кода
    on(reg1, 'submit', async (e)=>{
      e.preventDefault();
      setError('');
      const fd = new FormData(reg1);
      regName = String(fd.get('name')||'').trim();
      regEmail = String(fd.get('email')||'').trim();
      regPhone = String(fd.get('phone')||'').trim();
      regPassword = String(fd.get('password')||'');
      if(!regName || !regEmail || regPassword.length < 6){
        setError('Проверьте корректность имени, почты и пароля (мин. 6 символов).');
        return;
      }
      try{
        const fdReq = new FormData();
        fdReq.append('name', regName);
        fdReq.append('email', regEmail);
        if(regPhone) fdReq.append('phone', regPhone);
        fdReq.append('password', regPassword);

        const r = await fetch('/auth/request-code/', {
          method:'POST',
          headers: csrfHeaders(),
          body: fdReq
        });
        const data = await r.json();
        if(!data.successful){ setError(data.message || 'Не удалось отправить код'); return; }
        hide(reg1); show(reg2);
        alert('Код отправлен на почту');
      }catch(err){
        setError('Сеть недоступна. Попробуйте ещё раз.');
      }
    });

    // Повторная отправка кода
    on($('#resendCodeBtn'), 'click', async ()=>{
      setError('');
      if(!regEmail){ setError('Сначала заполните шаг 1.'); return; }
      try{
        const fd = new FormData();
        fd.append('email', regEmail);
        const r = await fetch('/auth/request-code/', {
          method:'POST',
          headers: csrfHeaders(),
          body: fd
        });
        const data = await r.json();
        if(!data.successful){ setError(data.message || 'Не удалось отправить код'); return; }
        alert('Код повторно отправлен на почту');
      }catch(err){
        setError('Сеть недоступна. Попробуйте ещё раз.');
      }
    });

    // Step 2 → верификация кода
    on(reg2, 'submit', async (e)=>{
      e.preventDefault();
      setError('');
      const fd = new FormData(reg2);
      const code = String(fd.get('code')||'').trim();
      if(!code){ setError('Введите код из письма.'); return; }
      try{
        const f = new FormData();
        f.append('email', regEmail);
        f.append('code', code);
        const r = await fetch('/auth/verify/', {
          method:'POST',
          headers: csrfHeaders(),
          body: f
        });
        const data = await r.json();
        if(!data.successful){ setError(data.message || 'Код неверный или просрочен'); return; }
        hide(reg2); show(reg3);
      }catch(err){
        setError('Сеть недоступна. Попробуйте ещё раз.');
      }
    });

    // Step 3 → загрузка аватара и авто-вход
    on(reg3, 'submit', async (e)=>{
      e.preventDefault();
      setError('');
      const fd = new FormData(reg3);
      if(!fd.get('avatar')){ setError('Пожалуйста, загрузите аватар.'); return; }
      try{
        const r = await fetch('/auth/upload-avatar/', {
          method:'POST',
          headers: csrfHeaders(),
          body: fd
        });
        const data = await r.json();
        if(!data.successful){ setError(data.message || 'Не удалось загрузить аватар'); return; }

        // После аватара — сразу логиним по введённой ранее паре email+password
        const loginForm = new FormData();
        loginForm.append('email', regEmail);
        loginForm.append('password', regPassword);
        const r2 = await fetch('/auth/login/', {
          method:'POST',
          headers: csrfHeaders(),
          body: loginForm
        });
        const loginData = await r2.json();
        if(!loginData.successful){ setError(loginData.message || 'Ошибка авто-входа'); return; }

        hide(authModal);
        await postLoginUIUpdate(loginData);
      }catch(err){
        setError('Сеть недоступна. Попробуйте ещё раз.');
      }
    });

    // Обновление UI после входа
    async function postLoginUIUpdate(me){
      try{
        // Обновим шапку: аватар/имя
        const resp = await fetch('/auth/me/');
        const data = await resp.json();
        if(data && data.authenticated){
          const navAv = $('#navAvatar');
          const hi = $('#hi');
          if(data.name) hi.textContent = `Салом, ${data.name} 👋`;
          if(data.avatar_url){
            if(navAv) navAv.innerHTML = `<img src="${data.avatar_url}" alt="avatar" style="width:24px;height:24px;border-radius:50%;object-fit:cover">`;
            if(openBtn){
              openBtn.outerHTML = `<img src="${data.avatar_url}" alt="" style="width:36px;height:36px;border-radius:50%;object-fit:cover">`;
            }
          }else if(openBtn){
            openBtn.textContent = data.name || data.email || 'Профиль';
          }
        }
        // Обновим страницу, если нужно подтянуть персональные данные
        // location.reload(); // при желании раскомментируйте
      }catch(_){}
    }

    // Авто-запрос /auth/me/ для состояния
    (async ()=>{
      try{
        const r = await fetch('/auth/me/');
        const data = await r.json();
        if(data && data.authenticated){
          const hi = $('#hi');
          if(data.name) hi.textContent = `Салом, ${data.name} 👋`;
          if(data.avatar_url){
            $('#navAvatar').innerHTML =
              `<img src="${data.avatar_url}" alt="avatar" style="width:24px;height:24px;border-radius:50%;object-fit:cover">`;
            if(openBtn){
              openBtn.outerHTML =
                `<img src="${data.avatar_url}" alt="" style="width:36px;height:36px;border-radius:50%;object-fit:cover">`;
            }
          }else if(openBtn){
            openBtn.textContent = data.name || data.email || 'Профиль';
          }
        }
      }catch(_){}
    })();

    // Избежать "старых" автозаполнений/попапов локально (если ранее что-то сохраняли)
    // Ничего не храним в localStorage для auth — всё на сессиях/куках.
    try{
      ['aclub_user','aclub_avatar'].forEach(k=> localStorage.removeItem(k));
    }catch(_){}
  })();