// The Grid: fill a 3x3 board with players who fit both their row and their column.
(function () {
  var root = document.getElementById('grid');
  if (!root) return;
  var BASE = root.getAttribute('data-base');
  var GUESSES = 12;
  var PROG = { CLEV: 'Cleveland State', OHIO: 'Ohio', 'M-OH': 'Miami (OH)' };
  var data = null, byId = {}, index = {}, cond = {};
  var game = null;
  var sel = null; // selected cell index
  var els = {
    board: root.querySelector('[data-board]'),
    panel: root.querySelector('[data-panel]'),
    prompt: root.querySelector('[data-prompt]'),
    input: root.querySelector('#gr-input'),
    list: root.querySelector('#gr-list'),
    status: root.querySelector('[data-status]'),
    left: root.querySelector('[data-left]'),
    end: root.querySelector('[data-end]'),
    title: root.querySelector('[data-title]'),
    tabs: root.querySelectorAll('[data-mode]'),
    type: root.querySelector('#gr-type'),
    typeWrap: root.querySelector('[data-typewrap]')
  };

  // ---------- helpers
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function seeded(seed) { return function () { seed = (seed + 0x6D2B79F5) | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function daysSince(a, b) { var pa = a.split('-'), pb = b.split('-'); return Math.round((Date.UTC(+pb[0], pb[1] - 1, +pb[2]) - Date.UTC(+pa[0], pa[1] - 1, +pa[2])) / 86400000); }
  function norm(s) { return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]/g, ''); }
  function sample(arr, n, rnd) { var a = arr.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(rnd() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a.slice(0, n); }
  function answersFor(r, c) { var A = index[r] || [], B = index[c] || []; var setB = {}; B.forEach(function (x) { setB[x] = 1; }); return A.filter(function (x) { return setB[x]; }); }

  // Is there a way to fill all nine squares with nine different players?
  function hasMatching(cells) {
    var owner = {};
    function tryCell(i, seen) {
      var cands = cells[i];
      for (var k = 0; k < cands.length; k++) {
        var p = cands[k];
        if (seen[p]) continue;
        seen[p] = 1;
        if (owner[p] === undefined || tryCell(owner[p], seen)) { owner[p] = i; return true; }
      }
      return false;
    }
    for (var i = 0; i < cells.length; i++) if (!tryCell(i, {})) return false;
    return true;
  }

  function buildGrid(type, rnd) {
    var all = data.conditions.map(function (c) { return c.key; });
    var progCols = ['prog:CLEV', 'prog:OHIO', 'prog:M-OH'];
    var rowPool = all.filter(function (k) {
      var c = cond[k];
      return (c.cat === 'position' || c.cat === 'honor' || c.cat === 'era') && k !== 'hon:none' &&
        progCols.every(function (p) { return answersFor(k, p).length >= data.min; });
    });
    for (var t = 0; t < 5000; t++) {
      var rows, cols;
      if (type === 'programs') {
        rows = sample(rowPool, 3, rnd);
        cols = progCols.slice();
      } else {
        var six = sample(all, 6, rnd);
        rows = six.slice(0, 3); cols = six.slice(3);
        var rc = {}, ok = true;
        rows.forEach(function (k) { rc[cond[k].cat] = 1; });
        cols.forEach(function (k) { if (rc[cond[k].cat]) ok = false; });
        // "Drafted" and "1st-round pick" overlap, so a grid gets at most one draft condition.
        if (six.filter(function (k) { return cond[k].cat === 'draft'; }).length > 1) ok = false;
        if (!ok) continue;
      }
      var cells = [], fine = true;
      for (var i = 0; i < 3 && fine; i++) for (var j = 0; j < 3; j++) {
        var a = answersFor(rows[i], cols[j]);
        if (a.length < data.min) { fine = false; break; }
        cells.push(a);
      }
      if (fine && hasMatching(cells)) return { rows: rows, cols: cols, cells: cells };
    }
    return null;
  }

  // ---------- game
  function newGame(mode) {
    var g;
    if (mode === 'daily') {
      var n = Math.max(0, daysSince(data.launch, VAGames.today()));
      var type = n % 2 === 0 ? 'programs' : 'open';
      g = buildGrid(type, seeded(hash('valhalla-grid-' + n)));
      game = { mode: 'daily', number: n + 1, type: type, grid: g, filled: Array(9).fill(null), used: 0, done: false };
      var saved = VAGames.getItem('_gr_daily');
      if (saved && saved.date === VAGames.today()) { game.filled = saved.filled; game.used = saved.used; game.done = saved.done; }
      els.title.textContent = 'Daily grid #' + game.number + (type === 'programs' ? ' · Programs' : ' · Open');
    } else {
      var tp = els.type.value === 'surprise' ? (Math.random() < 0.5 ? 'programs' : 'open') : els.type.value;
      g = buildGrid(tp, Math.random);
      game = { mode: 'practice', number: 0, type: tp, grid: g, filled: Array(9).fill(null), used: 0, done: false };
      els.title.textContent = 'Practice · ' + (tp === 'programs' ? 'Programs grid' : 'Open grid');
    }
    sel = null;
    els.status.textContent = '';
    render();
  }

  function render() {
    var g = game.grid;
    els.board.innerHTML = '';
    var corner = document.createElement('div');
    corner.className = 'gr-corner';
    corner.innerHTML = '<b>' + Math.max(0, GUESSES - game.used) + '</b><span>guesses left</span>';
    els.board.appendChild(corner);
    g.cols.forEach(function (k) { els.board.appendChild(head(k, 'col')); });
    for (var i = 0; i < 3; i++) {
      els.board.appendChild(head(g.rows[i], 'row'));
      for (var j = 0; j < 3; j++) els.board.appendChild(cellEl(i * 3 + j));
    }
    els.left.textContent = '';
    renderEnd();
  }
  function head(k, kind) {
    var c = cond[k];
    var d = document.createElement('div');
    d.className = 'gr-head ' + kind;
    var prog = k.indexOf('prog:') === 0 ? k.slice(5) : null;
    if (prog) {
      d.setAttribute('data-prog', prog);
      d.innerHTML = '<img src="' + BASE + 'assets/logos/' + prog + '.png" alt="" width="34" height="34"><span></span>';
    } else {
      d.innerHTML = '<span></span>';
    }
    d.querySelector('span').textContent = c.label;
    return d;
  }
  function cellEl(idx) {
    var g = game.grid, i = Math.floor(idx / 3), j = idx % 3;
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'gr-cell';
    var label = cond[g.rows[i]].label + ' and ' + cond[g.cols[j]].label;
    var f = game.filled[idx];
    if (f) {
      var p = byId[f];
      b.classList.add('is-filled');
      b.innerHTML = '<span class="nm"></span><span class="rar">1 of ' + g.cells[idx].length + '</span>';
      b.querySelector('.nm').textContent = p.n;
      b.setAttribute('aria-label', label + ': ' + p.n);
      b.disabled = true;
    } else {
      b.innerHTML = '<span class="plus" aria-hidden="true">+</span>';
      b.setAttribute('aria-label', label + ': empty. Choose to guess.');
      if (game.done) b.disabled = true;
      if (sel === idx) b.classList.add('is-sel');
      b.addEventListener('click', function () { select(idx); });
    }
    return b;
  }

  function select(idx) {
    if (game.done) return;
    sel = idx;
    var g = game.grid, i = Math.floor(idx / 3), j = idx % 3;
    els.panel.hidden = false;
    els.prompt.textContent = cond[g.rows[i]].label + ' + ' + cond[g.cols[j]].label;
    els.input.value = '';
    els.list.hidden = true;
    render();
    els.input.focus();
  }

  function guess(pid) {
    if (sel === null || game.done) return;
    var idx = sel, p = byId[pid];
    if (game.filled.indexOf(pid) !== -1) { els.status.textContent = p.n + ' is already on your grid. Each player can be used once.'; return; }
    game.used += 1;
    var fits = game.grid.cells[idx].indexOf(pid) !== -1;
    if (fits) {
      game.filled[idx] = pid;
      els.status.textContent = 'Yes! ' + p.n + ' fits.';
      sel = null;
      els.panel.hidden = true;
    } else {
      els.status.textContent = 'No, ' + p.n + ' doesn\'t fit that square. ' + Math.max(0, GUESSES - game.used) + ' guesses left.';
      els.input.value = '';
      els.list.hidden = true;
    }
    var full = game.filled.every(Boolean);
    if (full || game.used >= GUESSES) { game.done = true; sel = null; els.panel.hidden = true; finish(); }
    if (game.mode === 'daily') VAGames.setItem('_gr_daily', { date: VAGames.today(), filled: game.filled, used: game.used, done: game.done });
    render();
    if (!game.done && sel !== null) els.input.focus();
  }

  function finish() {
    var score = game.filled.filter(Boolean).length;
    var upd = { plays: 1, squares: score, best: score, perfect: score === 9 ? 1 : 0 };
    if (game.mode === 'daily') { upd.dailyPlays = 1; }
    VAGames.record('grid', upd);
  }

  function renderEnd() {
    els.end.hidden = !game.done;
    if (!game.done) { els.end.innerHTML = ''; return; }
    var score = game.filled.filter(Boolean).length;
    els.end.innerHTML = '<p class="pd-verdict ' + (score === 9 ? 'ok' : '') + '">' +
      (score === 9 ? 'Perfect grid! 9 of 9.' : 'You filled ' + score + ' of 9.') + '</p><div class="gm-actions"></div>' +
      '<details class="gr-answers"><summary>Show every possible answer</summary><div class="gr-ans-list"></div></details>';
    var acts = els.end.querySelector('.gm-actions');
    if (game.mode === 'daily') {
      var share = document.createElement('button');
      share.type = 'button'; share.className = 'gm-btn'; share.textContent = 'Copy my result';
      share.addEventListener('click', function () { copy(shareText(), share); });
      acts.appendChild(share);
    }
    var again = document.createElement('button');
    again.type = 'button'; again.className = 'gm-btn' + (game.mode === 'daily' ? ' ghost' : ''); again.textContent = game.mode === 'daily' ? 'Play a practice grid' : 'New grid';
    again.addEventListener('click', function () { setMode('practice'); });
    acts.appendChild(again);
    var list = els.end.querySelector('.gr-ans-list');
    var g = game.grid;
    g.cells.forEach(function (ids, idx) {
      var i = Math.floor(idx / 3), j = idx % 3;
      var box = document.createElement('div');
      box.className = 'gr-ans';
      var h = document.createElement('h3');
      h.textContent = cond[g.rows[i]].label + ' + ' + cond[g.cols[j]].label + ' (' + ids.length + ')';
      box.appendChild(h);
      var p = document.createElement('p');
      ids.map(function (id) { return byId[id]; }).sort(function (a, b) { return a.n.localeCompare(b.n); }).forEach(function (pl, k) {
        if (k) p.appendChild(document.createTextNode(', '));
        var a = document.createElement('a');
        a.href = BASE + 'players/' + pl.id + '/';
        a.textContent = pl.n;
        if (game.filled[idx] === pl.id) a.className = 'mine';
        p.appendChild(a);
      });
      box.appendChild(p);
      list.appendChild(box);
    });
  }

  function shareText() {
    var rows = [0, 1, 2].map(function (i) { return [0, 1, 2].map(function (j) { return game.filled[i * 3 + j] ? '🟩' : '⬜'; }).join(''); });
    return 'Valhalla Grid #' + game.number + ' ' + game.filled.filter(Boolean).length + '/9\n' + rows.join('\n');
  }
  function copy(text, btn) {
    function done() { btn.textContent = 'Copied!'; setTimeout(function () { btn.textContent = 'Copy my result'; }, 1800); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, function () { window.prompt('Copy your result:', text); });
    else window.prompt('Copy your result:', text);
  }

  // ---------- suggestions (same behavior as Playerdle)
  var shown = [], active = -1;
  function suggest() {
    var q = norm(els.input.value.trim());
    els.list.innerHTML = ''; active = -1;
    if (q.length < 2) { els.list.hidden = true; els.input.setAttribute('aria-expanded', 'false'); return; }
    function rank(p) { var n = norm(p.n), i = n.indexOf(q); return ((i === 0 || n.charAt(i - 1) === ' ') ? 0 : 100) + i; }
    shown = data.players.filter(function (p) { return norm(p.n).indexOf(q) !== -1; })
      .sort(function (a, b) { return rank(a) - rank(b) || a.n.localeCompare(b.n); }).slice(0, 8);
    shown.forEach(function (p, i) {
      var li = document.createElement('li');
      li.id = 'gr-opt-' + i; li.setAttribute('role', 'option');
      li.innerHTML = '<span class="nm"></span><span class="gm-chip" data-cat="' + p.p + '">' + PROG[p.p] + '</span>';
      li.querySelector('.nm').textContent = p.n;
      li.addEventListener('mousedown', function (e) { e.preventDefault(); guess(p.id); });
      els.list.appendChild(li);
    });
    if (!shown.length) { var li = document.createElement('li'); li.className = 'empty'; li.textContent = 'No player matches that name.'; els.list.appendChild(li); }
    els.list.hidden = false; els.input.setAttribute('aria-expanded', 'true');
  }
  function highlight(i) {
    var opts = els.list.querySelectorAll('[role="option"]');
    opts.forEach(function (o, j) { o.classList.toggle('on', j === i); o.setAttribute('aria-selected', j === i ? 'true' : 'false'); });
    active = i;
    if (opts[i]) els.input.setAttribute('aria-activedescendant', opts[i].id); else els.input.removeAttribute('aria-activedescendant');
  }
  els.input.addEventListener('input', suggest);
  els.input.addEventListener('blur', function () { setTimeout(function () { els.list.hidden = true; }, 120); });
  els.input.addEventListener('keydown', function (e) {
    var opts = els.list.querySelectorAll('[role="option"]');
    if (e.key === 'ArrowDown') { e.preventDefault(); highlight(Math.min(opts.length - 1, active + 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); highlight(Math.max(0, active - 1)); }
    else if (e.key === 'Escape') { els.list.hidden = true; els.panel.hidden = true; sel = null; render(); }
    else if (e.key === 'Enter') { e.preventDefault(); var pick = shown[active >= 0 ? active : 0]; if (pick && !els.list.hidden) guess(pick.id); }
  });
  root.querySelector('[data-form]').addEventListener('submit', function (e) { e.preventDefault(); });
  root.querySelector('[data-cancel]').addEventListener('click', function () { els.panel.hidden = true; sel = null; render(); });

  function setMode(mode) {
    els.tabs.forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('data-mode') === mode ? 'true' : 'false'); });
    els.typeWrap.hidden = mode !== 'practice';
    els.panel.hidden = true;
    newGame(mode);
  }
  els.tabs.forEach(function (t) { t.addEventListener('click', function () { setMode(t.getAttribute('data-mode')); }); });
  els.type.addEventListener('change', function () { setMode('practice'); });

  fetch(root.getAttribute('data-src')).then(function (r) { return r.json(); }).then(function (d) {
    data = d;
    d.conditions.forEach(function (c) { cond[c.key] = c; });
    d.players.forEach(function (p) { byId[p.id] = p; p.t.forEach(function (t) { (index[t] = index[t] || []).push(p.id); }); });
    setMode('daily');
  }).catch(function () { els.status.textContent = 'The grid data could not be loaded. Try refreshing the page.'; });
  if (!VAGames.isPersistent()) root.querySelector('[data-storage-note]').hidden = false;
})();
