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
  window.matchMedia('(min-width: 1640px)').addEventListener('change', function (m) { if (m.matches) set(false); });
})();

// Print view: a footer toggle re-lays out the page for printing. Remembered for this tab only.
// The browser's own Print command gets the same layout automatically.
(function () {
  var root = document.documentElement;
  if (root.hasAttribute('data-noprint')) return;
  var KEY = 'va-print', opened = [], auto = false;
  function on() { return root.classList.contains('print-mode'); }
  function remember(v) { try { if (v) sessionStorage.setItem(KEY, '1'); else sessionStorage.removeItem(KEY); } catch (e) {} }
  function openDetails() {
    // Collapsed sections would print empty, so open them while in print view.
    document.querySelectorAll('details:not([open])').forEach(function (d) { d.open = true; opened.push(d); });
  }
  function closeDetails() { opened.forEach(function (d) { d.open = false; }); opened = []; }
  // Tables wider than the sheet are scaled down to fit (never below 55%).
  function fitTables(limit) {
    document.querySelectorAll('.table-wrap > table, .bracket').forEach(function (t) {
      t.style.zoom = '';
      var box = t.parentElement.clientWidth, w = t.scrollWidth;
      if (limit) box = Math.min(box, limit);
      if (w > box + 1) t.style.zoom = Math.max(0.55, box / w).toFixed(3);
    });
  }
  function unfitTables() { document.querySelectorAll('.table-wrap > table, .bracket').forEach(function (t) { t.style.zoom = ''; }); }
  function sync() {
    document.querySelectorAll('.print-toggle').forEach(function (b) { b.setAttribute('aria-pressed', on() ? 'true' : 'false'); });
  }
  function set(v) {
    root.classList.toggle('print-mode', v);
    remember(v);
    if (v) { openDetails(); fitTables(); } else { closeDetails(); unfitTables(); }
    sync();
    if (v) {
      window.scrollTo(0, 0);
      var save = document.querySelector('[data-print-save]');
      if (save) save.focus();
    }
  }
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-print-toggle]');
    if (t) { set(!on()); if (!on()) { var f = document.querySelector('.print-toggle'); if (f) f.focus(); } return; }
    if (e.target.closest('[data-print-save]')) window.print();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && on() && !auto && !document.querySelector('.nav-toggle[aria-expanded="true"]')) set(false);
  });
  window.addEventListener('beforeprint', function () {
    if (!on()) { auto = true; root.classList.add('print-mode'); openDetails(); }
    fitTables(690); // a printed page is about 7.5 inches (720px) wide
  });
  window.addEventListener('afterprint', function () {
    if (auto) { auto = false; root.classList.remove('print-mode'); closeDetails(); unfitTables(); } else fitTables();
  });
  if (on()) { openDetails(); window.addEventListener('load', function () { fitTables(); }); }
  sync();
})();
