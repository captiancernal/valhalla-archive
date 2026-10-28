// Players page: live filter for the player table.
(function () {
  var q = document.getElementById('q'), t = document.getElementById('team'), f = document.getElementById('fam'), h = document.getElementById('honored');
  var form = document.querySelector('form.filters');
  if (form) form.addEventListener('submit', function (e) { e.preventDefault(); });
  var rows = Array.prototype.slice.call(document.querySelectorAll('#players tbody tr')), count = document.getElementById('count');
  var programs = ['CLEV', 'OHIO', 'M-OH'];
  function apply() {
    var qs = q.value.trim().toLowerCase(), ts = t.value, fs = f.value, hs = h.checked, shown = 0;
    rows.forEach(function (r) {
      var ok = (!qs || r.dataset.n.indexOf(qs) !== -1) && (!fs || r.dataset.f === fs) && (!hs || +r.dataset.h > 0) &&
               (!ts || (ts === 'other' ? programs.indexOf(r.dataset.t) === -1 : r.dataset.t === ts));
      r.hidden = !ok; if (ok) shown++;
    });
    count.textContent = shown + ' of ' + rows.length + ' players';
  }
  [q, t, f, h].forEach(function (el) { el.addEventListener('input', apply); el.addEventListener('change', apply); });
  try { var saved = JSON.parse(sessionStorage.getItem('va-players') || '{}'); if (saved.t) t.value = saved.t; } catch (e) {}
  t.addEventListener('change', function () { try { sessionStorage.setItem('va-players', JSON.stringify({ t: t.value })); } catch (e) {} });
  apply();
})();
