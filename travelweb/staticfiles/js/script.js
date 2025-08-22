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
      if (user?.name && hiEl) hiEl.textContent = `Салом, ${user.name} 👋`;
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
  if (hiEl) hiEl.textContent = `Салом, ${user.name} 👋`;
  closeModal();
}


// ================== WEATHER ==================
function wmoToEmoji(code, isDay){
  const sun='🍑', moon='🍑', sunCloud='🌤️', cloud='☁️', fog='🌫️',
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



