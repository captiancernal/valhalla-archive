// Mobile nav disclosure (keyboard and screen-reader friendly).
(function () {
  var btn = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');
  if (!btn || !nav) return;
  function set(open) {
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    nav.classList.toggle('open', open);
  }
  btn.addEventListener('click', function () { set(btn.getAttribute('aria-expanded') !== 'true'); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && btn.getAttribute('aria-expanded') === 'true') { set(false); btn.focus(); }
  });
  window.matchMedia('(min-width: 1181px)').addEventListener('change', function (m) { if (m.matches) set(false); });
})();
