// Games hub: show this browser's saved game stats.
document.addEventListener('DOMContentLoaded', function () {
  var all = VAGames.all();
  var rounds = 0;
  Object.keys(all).forEach(function (k) { if (k[0] !== '_' && all[k].plays) rounds += all[k].plays; });
  var t = all.trivia || {};
  var pdx = all.playerdle || {};
  function set(k, v) { var el = document.querySelector('[data-stat="' + k + '"]'); if (el) el.textContent = v; }
  set('rounds', rounds);
  set('streak', VAGames.streak());
  var wsx = all.wordsearch || {};
  if (wsx.plays) {
    var wm = document.querySelector('[data-game-meta="wordsearch"]');
    if (wm) wm.textContent = wsx.completed + ' puzzle' + (wsx.completed === 1 ? '' : 's') + ' solved' + (wsx.fastest ? ' · fastest ' + Math.floor(wsx.fastest / 60) + ':' + String(wsx.fastest % 60).padStart(2, '0') : '');
  }
  var grx = all.grid || {};
  if (grx.plays) {
    var gm = document.querySelector('[data-game-meta="grid"]');
    if (gm) gm.textContent = grx.plays + ' grid' + (grx.plays === 1 ? '' : 's') + ' played · best ' + (grx.best || 0) + ' of 9';
  }
  if (pdx.plays) {
    var pm = document.querySelector('[data-game-meta="playerdle"]');
    if (pm) pm.textContent = (pdx.dailyWins || 0) + ' daily win' + ((pdx.dailyWins || 0) === 1 ? '' : 's') + ' · ' + (pdx.practicePlays || 0) + ' practice game' + ((pdx.practicePlays || 0) === 1 ? '' : 's');
  }
  var hl = all.higherlower || {};
  if (hl.plays) {
    set('hlbest', hl.best || 0);
    var hm = document.querySelector('[data-game-meta="higherlower"]');
    if (hm) hm.textContent = hl.plays + ' game' + (hl.plays === 1 ? '' : 's') + ' played · best streak ' + (hl.best || 0);
  }
  if (t.plays) {
    set('tbest', t.best || 0);
    set('tacc', Math.round((t.correct / Math.max(1, t.answered)) * 100) + '%');
    var m = document.querySelector('[data-game-meta="trivia"]');
    if (m) m.textContent = t.plays + ' round' + (t.plays === 1 ? '' : 's') + ' played · best ' + (t.best || 0) + ' of 10';
  }
  if (!VAGames.isPersistent()) document.querySelector('[data-storage-note]').hidden = false;
  document.getElementById('gm-reset').addEventListener('click', function () {
    if (window.confirm('Reset all your game stats on this device? This cannot be undone.')) { VAGames.reset(); location.reload(); }
  });
});
