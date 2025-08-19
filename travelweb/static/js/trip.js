/* ================== WEATHER ================== */
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
  const weatherText = document.getElementById('weatherText');
  const iconEl = document.querySelector('.hero-weather .icon');
  if (weatherText) weatherText.textContent = `${Math.round(Number(temp || 15))}°C`;
  if (iconEl){
    const emoji = wmoToEmoji(Number(code), Number(isDay) === 1);
    iconEl.textContent = emoji;
    iconEl.setAttribute('aria-label', `Weather ${emoji}`);
    iconEl.setAttribute('title', emoji);
  }
}

/* ================== HERO BG + WEATHER ================== */
const hero = document.getElementById('tripHero');

(function initHeroBg(){
  try{
    const url = new URL(window.location.href);
    const bg = url.searchParams.get('bg') || hero?.dataset.bg;
    if (bg){
      hero.style.setProperty('--hero-img', `url("${bg}")`);
      document.body.style.setProperty('--hero-img', `url("${bg}")`);
    }
  }catch{/* no-op */}
})();

(async function initTripWeather(){
  try{
    const url = new URL(window.location.href);
    const lat = Number(url.searchParams.get('lat')) || Number(hero?.dataset.lat) || 67.2804;
    const lon = Number(url.searchParams.get('lon')) || Number(hero?.dataset.lon) || 14.4049;
    const r = await fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code,is_day`);
    const j = await r.json();
    updateWeatherUI(j?.current?.temperature_2m ?? 15, j?.current?.weather_code ?? 2, j?.current?.is_day ?? 1);
  }catch{
    updateWeatherUI(15,2,1);
  }
})();

/* ================== FAVORITE FAB + NAV AVATAR ================== */
document.getElementById('favFab')?.addEventListener('click', e=>{
  e.currentTarget.classList.toggle('is-active');
});

(function setNavAvatar(){
  const el = document.getElementById('navAvatar');
  if (!el) return;
  try{
    const raw = localStorage.getItem('aclub_user');
    const { avatar } = raw ? JSON.parse(raw) : {};
    el.style.backgroundImage = `url("${avatar || '../media/avatar-default.png'}")`;
  }catch{
    el.style.backgroundImage = `url("../media/avatar-default.png")`;
  }
})();

