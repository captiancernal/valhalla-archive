// Front page: awards showcase year switcher (progressive enhancement; the default
// year is already rendered in the HTML).
(function () {
  var dataEl = document.getElementById('award-data');
  var grid = document.querySelector('[data-grid]');
  var summary = document.querySelector('[data-summary]');
  var label = document.querySelector('[data-year-label]');
  var buttons = Array.prototype.slice.call(document.querySelectorAll('.year-picker button'));
  if (!dataEl || !grid || !buttons.length) return;
  var data = JSON.parse(dataEl.textContent);
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var names = { 'CLEV': 'Cleveland State', 'OHIO': 'Ohio', 'M-OH': 'Miami (OH)' };
  var logos = {};
  Array.prototype.forEach.call(summary.querySelectorAll('[data-program]'), function (el) {
    var img = el.querySelector('img'); if (img) logos[el.dataset.program] = img.getAttribute('src');
  });

  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var icon = '<svg class="aw-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3h10v3a5 5 0 0 1-10 0V3Zm0 1H4v1a3 3 0 0 0 3 3M17 4h3v1a3 3 0 0 1-3 3M12 11v5m-4 4h8m-6-4h4v4h-4z"/></svg>';

  function card(a) {
    var cls = a.school === 'CLEV' ? ' spot' : (a.ours ? ' ours' : '');
    return '<article class="aw-card' + cls + '"><div class="aw-top">' + icon + '<span class="aw-name">' + esc(a.award) + '</span>' +
      (a.school === 'CLEV' ? '<span class="aw-flag">Vikings</span>' : '') + '</div>' +
      '<div class="aw-note">' + esc(a.note) + '</div>' +
      '<div class="aw-player">' + (a.href ? '<a href="' + esc(a.href) + '">' + esc(a.player) + '</a>' : esc(a.player)) + '</div>' +
      '<div class="aw-school">' + (a.logo ? '<img src="' + esc(a.logo) + '" alt="" width="22" height="22">' : '') + esc(a.school_name) + '</div></article>';
  }

  function chip(pid, d) {
    var n = d.awards.filter(function (a) { return a.school === pid; }).length;
    return '<span class="as-chip" data-program="' + pid + '"><span class="team">' + (logos[pid] ? '<img class="tlogo" src="' + logos[pid] + '" alt="" width="20" height="20">' : '') +
      '<span>' + names[pid] + '</span></span> <b>' + n + '</b> ' + (n === 1 ? 'award' : 'awards') + ' · <b>' + d.aa[pid] + '</b> All-Americans</span>';
  }

  function show(year, push) {
    var d = data[year]; if (!d) return;
    buttons.forEach(function (b) { b.setAttribute('aria-pressed', b.dataset.year === year ? 'true' : 'false'); });
    label.textContent = year;
    summary.innerHTML = ['CLEV', 'OHIO', 'M-OH'].map(function (p) { return chip(p, d); }).join('');
    grid.innerHTML = d.awards.map(card).join('');
    if (!reduce) { grid.classList.remove('fade'); void grid.offsetWidth; grid.classList.add('fade'); }
    if (push) { try { history.replaceState(null, '', '#awards-' + year); } catch (e) {} }
  }

  buttons.forEach(function (b) { b.addEventListener('click', function () { show(b.dataset.year, true); }); });
  var m = /#awards-(\d{4})/.exec(location.hash);
  if (m && data[m[1]]) show(m[1], false);
})();
