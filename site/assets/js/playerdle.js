// Playerdle: guess the mystery player in 8 tries. Daily puzzle plus unlimited practice.
(function () {
  var root = document.getElementById('pd');
  if (!root) return;
  var BASE = root.getAttribute('data-base');
  var MAX = 8;
  var PROG = { CLEV: 'Cleveland State', OHIO: 'Ohio', 'M-OH': 'Miami (OH)' };
  var TILE = { CLEV: 'Cleveland St.', OHIO: 'Ohio', 'M-OH': 'Miami (OH)' };
  var COLS = [
    { k: 'p', label: 'Program' }, { k: 'pos', label: 'Position' }, { k: 'first', label: 'First season' },
    { k: 'last', label: 'Last season' }, { k: 'hon', label: 'Honors' }, { k: 'st', label: 'Home state' },
    { k: 'stars', label: 'Recruit stars' }, { k: 'ovr', label: 'Peak rating' }
  ];
  var NEAR = { first: 2, last: 2, hon: 1, stars: 0, ovr: 3 };
  var players = [], byId = {}, launch = '2026-10-28';
  var game = null; // {mode, answer, guesses:[ids], done, won, number}

  var els = {
    tabs: root.querySelectorAll('[data-mode]'),
    filter: root.querySelector('#pd-prog'),
    filterWrap: root.querySelector('[data-filter]'),
    input: root.querySelector('#pd-input'),
    list: root.querySelector('#pd-list'),
    form: root.querySelector('[data-form]'),
    board: root.querySelector('[data-board]'),
    status: root.querySelector('[data-status]'),
    end: root.querySelector('[data-end]'),
    left: root.querySelector('[data-left]')
  };

  // ---------- helpers
  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function seeded(seed) { return function () { seed = (seed + 0x6D2B79F5) | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function daysSince(a, b) { var pa = a.split('-'), pb = b.split('-'); return Math.round((Date.UTC(+pb[0], pb[1] - 1, +pb[2]) - Date.UTC(+pa[0], pa[1] - 1, +pa[2])) / 86400000); }
  function dailyAnswer() {
    var order = players.filter(function (p) { return p.daily; }).map(function (p) { return p.id; }).sort();
    var rnd = seeded(hash('valhalla-playerdle'));
    for (var i = order.length - 1; i > 0; i--) { var j = Math.floor(rnd() * (i + 1)); var t = order[i]; order[i] = order[j]; order[j] = t; }
    var n = Math.max(0, daysSince(launch, VAGames.today()));
    return { id: order[n % order.length], number: n + 1 };
  }
  function norm(s) { return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9 ]/g, ''); }

  function compare(g, a, k) {
    var gv = g[k], av = a[k];
    if (av === null || av === undefined) return { cls: 'na', text: '?', note: 'Not on file for the mystery player' };
    if (gv === null || gv === undefined) return { cls: 'miss', text: '—', note: 'Not on file for your guess' };
    if (k === 'p') return { cls: gv === av ? 'hit' : 'miss', text: TILE[gv] };
    if (k === 'pos' || k === 'st') return { cls: gv === av ? 'hit' : 'miss', text: gv };
    if (gv === av) return { cls: 'hit', text: String(gv) };
    var arrow = av > gv ? '↑' : '↓';
    var near = Math.abs(av - gv) <= NEAR[k] && NEAR[k] > 0;
    return { cls: near ? 'near' : 'miss', text: gv + ' ' + arrow, note: 'Mystery player is ' + (av > gv ? 'higher' : 'lower') };
  }

  // ---------- rendering
  function renderBoard() {
    els.board.innerHTML = '';
    var ans = byId[game.answer];
    game.guesses.forEach(function (gid) {
      var g = byId[gid];
      var row = document.createElement('div');
      row.className = 'pd-row' + (gid === game.answer ? ' is-win' : '');
      var name = document.createElement('div');
      name.className = 'pd-name';
      name.textContent = g.n;
      row.appendChild(name);
      COLS.forEach(function (c) {
        var r = compare(g, ans, c.k);
        var cell = document.createElement('div');
        cell.className = 'pd-tile ' + r.cls;
        cell.innerHTML = '<span class="lab"></span><span class="val"></span>';
        cell.querySelector('.lab').textContent = c.label;
        cell.querySelector('.val').textContent = r.text;
        cell.setAttribute('aria-label', c.label + ': ' + r.text + ({ hit: ', match', near: ', close', miss: '', na: '' }[r.cls] || '') + (r.note ? '. ' + r.note : ''));
        if (r.note) cell.title = r.note;
        row.appendChild(cell);
      });
      els.board.appendChild(row);
    });
    var left = MAX - game.guesses.length;
    els.left.textContent = game.done ? '' : (left + ' guess' + (left === 1 ? '' : 'es') + ' left');
  }

  function renderEnd() {
    var a = byId[game.answer];
    els.end.hidden = !game.done;
    els.form.hidden = game.done;
    if (!game.done) { els.end.innerHTML = ''; return; }
    var n = game.guesses.length;
    els.end.innerHTML =
      '<p class="pd-verdict ' + (game.won ? 'ok' : 'no') + '">' + (game.won ? ('Got it in ' + n + '!') : 'Out of guesses.') + '</p>' +
      '<div class="pd-reveal"><span class="gm-chip" data-cat="' + a.p + '">' + PROG[a.p] + '</span>' +
      '<a class="pd-ans" href="' + BASE + 'players/' + a.id + '/"></a><span class="pd-meta"></span><ul class="pd-hl"></ul></div>' +
      '<div class="gm-actions"></div>';
    els.end.querySelector('.pd-ans').textContent = a.n;
    els.end.querySelector('.pd-meta').textContent = [a.pos, a.first === a.last ? a.first : (a.first + '-' + a.last), a.st].filter(Boolean).join(' · ');
    var ul = els.end.querySelector('.pd-hl');
    (a.hl.length ? a.hl : ['Season stat leader']).forEach(function (h) { var li = document.createElement('li'); li.textContent = h; ul.appendChild(li); });
    var acts = els.end.querySelector('.gm-actions');
    if (game.mode === 'daily') {
      var share = document.createElement('button');
      share.type = 'button'; share.className = 'gm-btn'; share.textContent = 'Copy my result';
      share.addEventListener('click', function () { copyShare(share); });
      acts.appendChild(share);
      var stats = VAGames.get('playerdle');
      var p = document.createElement('p');
      p.className = 'muted pd-daily-stats';
      var streak = (VAGames.getItem('_pd_streak') || {});
      p.textContent = 'Daily wins: ' + (stats.dailyWins || 0) + ' of ' + (stats.dailyPlays || 0) + ' · Current streak: ' + (streak.cur || 0) + ' · Best: ' + (streak.max || 0) + '. A new puzzle arrives tomorrow.';
      els.end.appendChild(p);
    }
    var again = document.createElement('button');
    again.type = 'button'; again.className = 'gm-btn' + (game.mode === 'daily' ? ' ghost' : ''); again.textContent = game.mode === 'daily' ? 'Play practice' : 'New player';
    again.addEventListener('click', function () { setMode('practice', true); });
    acts.appendChild(again);
  }

  function shareText() {
    var a = byId[game.answer];
    var map = { hit: '🟩', near: '🟨', miss: '⬛', na: '⬜' };
    var lines = game.guesses.map(function (gid) {
      return COLS.map(function (c) { return map[compare(byId[gid], a, c.k).cls]; }).join('');
    });
    return 'Valhalla Playerdle #' + game.number + ' ' + (game.won ? game.guesses.length : 'X') + '/' + MAX + '\n' + lines.join('\n');
  }
  function copyShare(btn) {
    var text = shareText();
    function done() { btn.textContent = 'Copied!'; setTimeout(function () { btn.textContent = 'Copy my result'; }, 1800); }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, fallback);
    } else { fallback(); }
    function fallback() {
      var ta = document.createElement('textarea'); ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'absolute'; ta.style.left = '-9999px';
      document.body.appendChild(ta); ta.select();
      try { document.execCommand('copy'); done(); } catch (e) { window.prompt('Copy your result:', text); }
      document.body.removeChild(ta);
    }
  }

  // ---------- suggestions
  var active = -1, shown = [];
  function suggest() {
    var q = norm(els.input.value.trim());
    els.list.innerHTML = '';
    active = -1;
    if (q.length < 2 || !game || game.done) { els.list.hidden = true; els.input.setAttribute('aria-expanded', 'false'); return; }
    shown = players.filter(function (p) { return game.guesses.indexOf(p.id) === -1 && norm(p.n).indexOf(q) !== -1; })
      .sort(function (a, b) { return rank(a) - rank(b) || a.n.localeCompare(b.n); }).slice(0, 8);
    function rank(p) {
      var n = norm(p.n), i = n.indexOf(q);
      var wordStart = i === 0 || n.charAt(i - 1) === ' ';
      return (wordStart ? 0 : 100) + i;
    }
    shown.forEach(function (p, i) {
      var li = document.createElement('li');
      li.id = 'pd-opt-' + i;
      li.setAttribute('role', 'option');
      li.innerHTML = '<span class="nm"></span><span class="gm-chip" data-cat="' + p.p + '">' + PROG[p.p] + '</span>';
      li.querySelector('.nm').textContent = p.n;
      li.addEventListener('mousedown', function (e) { e.preventDefault(); submit(p.id); });
      els.list.appendChild(li);
    });
    if (!shown.length) {
      var li = document.createElement('li'); li.className = 'empty'; li.textContent = 'No player in the pool matches that name.'; els.list.appendChild(li);
    }
    els.list.hidden = false;
    els.input.setAttribute('aria-expanded', 'true');
  }
  function highlight(i) {
    var opts = els.list.querySelectorAll('[role="option"]');
    opts.forEach(function (o, j) { o.classList.toggle('on', j === i); o.setAttribute('aria-selected', j === i ? 'true' : 'false'); });
    active = i;
    if (opts[i]) els.input.setAttribute('aria-activedescendant', opts[i].id); else els.input.removeAttribute('aria-activedescendant');
  }

  function submit(id) {
    if (!game || game.done || !byId[id] || game.guesses.indexOf(id) !== -1) return;
    game.guesses.push(id);
    els.input.value = '';
    els.list.hidden = true;
    els.input.setAttribute('aria-expanded', 'false');
    if (id === game.answer) { game.done = true; game.won = true; }
    else if (game.guesses.length >= MAX) { game.done = true; game.won = false; }
    if (game.mode === 'daily') VAGames.setItem('_pd_daily', { date: VAGames.today(), guesses: game.guesses, done: game.done, won: game.won });
    if (game.done) finish();
    renderBoard();
    renderEnd();
    var g = byId[id];
    els.status.textContent = game.done ? (game.won ? 'Correct! The player was ' + g.n + '.' : 'Out of guesses. The player was ' + byId[game.answer].n + '.') : (g.n + ' is not the player. ' + (MAX - game.guesses.length) + ' guesses left.');
    if (!game.done) els.input.focus();
  }

  function finish() {
    var won = game.won, n = game.guesses.length;
    if (game.mode === 'daily') {
      var upd = { plays: 1, dailyPlays: 1, dailyWins: won ? 1 : 0 };
      if (won) upd['dist' + n] = 1;
      VAGames.record('playerdle', upd);
      var s = VAGames.getItem('_pd_streak') || {};
      var t = VAGames.today();
      if (s.last !== t) {
        s.cur = won ? ((s.last && daysSince(s.last, t) === 1 && s.cur) ? s.cur + 1 : 1) : 0;
        s.max = Math.max(s.max || 0, s.cur);
        s.last = t;
        VAGames.setItem('_pd_streak', s);
      }
    } else {
      VAGames.record('playerdle', { plays: 1, practicePlays: 1, practiceWins: won ? 1 : 0 });
    }
  }

  // ---------- modes
  function setMode(mode, fresh) {
    els.tabs.forEach(function (t) { t.setAttribute('aria-selected', t.getAttribute('data-mode') === mode ? 'true' : 'false'); });
    els.filterWrap.hidden = mode !== 'practice';
    if (mode === 'daily') {
      var d = dailyAnswer();
      var saved = VAGames.getItem('_pd_daily');
      game = { mode: 'daily', answer: d.id, number: d.number, guesses: [], done: false, won: false };
      if (saved && saved.date === VAGames.today()) { game.guesses = saved.guesses.filter(function (x) { return byId[x]; }); game.done = saved.done; game.won = saved.won; }
      root.querySelector('[data-title]').textContent = 'Daily puzzle #' + d.number;
    } else {
      var f = els.filter.value;
      var pool = players.filter(function (p) { return f === 'all' || p.p === f; });
      var pick = pool[Math.floor(Math.random() * pool.length)];
      game = { mode: 'practice', answer: pick.id, number: 0, guesses: [], done: false, won: false };
      root.querySelector('[data-title]').textContent = 'Practice' + (f === 'all' ? '' : ' · ' + PROG[f]);
    }
    els.status.textContent = '';
    renderBoard();
    renderEnd();
    if (fresh && !game.done) els.input.focus();
  }

  els.tabs.forEach(function (t) { t.addEventListener('click', function () { setMode(t.getAttribute('data-mode'), true); }); });
  els.filter.addEventListener('change', function () { setMode('practice', true); });
  els.input.addEventListener('input', suggest);
  els.input.addEventListener('blur', function () { setTimeout(function () { els.list.hidden = true; els.input.setAttribute('aria-expanded', 'false'); }, 120); });
  els.input.addEventListener('keydown', function (e) {
    var opts = els.list.querySelectorAll('[role="option"]');
    if (e.key === 'ArrowDown') { e.preventDefault(); highlight(Math.min(opts.length - 1, active + 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); highlight(Math.max(0, active - 1)); }
    else if (e.key === 'Escape') { els.list.hidden = true; els.input.setAttribute('aria-expanded', 'false'); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      var pick = shown[active >= 0 ? active : 0];
      if (pick && !els.list.hidden) submit(pick.id);
    }
  });
  els.form.addEventListener('submit', function (e) { e.preventDefault(); });

  fetch(root.getAttribute('data-src')).then(function (r) { return r.json(); }).then(function (data) {
    players = data.players;
    launch = data.launch || launch;
    players.forEach(function (p) { byId[p.id] = p; });
    root.querySelector('[data-pool]').textContent = players.length;
    els.input.disabled = false;
    setMode('daily', false);
  }).catch(function () {
    els.status.textContent = 'The player list could not be loaded. Try refreshing the page.';
  });
  if (!VAGames.isPersistent()) root.querySelector('[data-storage-note]').hidden = false;
})();
