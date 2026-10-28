// Trivia: rounds of 10 questions generated from the Archive's data.
(function () {
  var root = document.getElementById('trivia');
  if (!root) return;
  var DATA_URL = root.getAttribute('data-src');
  var ROUND = 10;
  var CAT_LABEL = { CLEV: 'Cleveland State', OHIO: 'Ohio', 'M-OH': 'Miami (OH)', LEAGUE: 'League' };
  var DIFF_LABEL = { 1: 'Easy', 2: 'Medium', 3: 'Hard' };

  var all = [];
  var round = null;
  var els = {
    setup: root.querySelector('[data-view="setup"]'),
    play: root.querySelector('[data-view="play"]'),
    done: root.querySelector('[data-view="done"]'),
    cat: root.querySelector('#tv-cat'),
    era: root.querySelector('#tv-era'),
    diff: root.querySelector('#tv-diff'),
    count: root.querySelector('[data-count]'),
    start: root.querySelector('[data-start]'),
    best: root.querySelector('[data-best]')
  };

  function show(view) {
    ['setup', 'play', 'done'].forEach(function (v) { els[v].hidden = v !== view; });
    window.scrollTo({ top: root.offsetTop - 80, behavior: 'smooth' });
  }

  function matches() {
    var c = els.cat.value, e = els.era.value, d = els.diff.value;
    return all.filter(function (q) {
      return (c === 'all' || q.cat === c) && (e === 'all' || q.era === e || q.era === 'all') && (d === 'mixed' || String(q.diff) === d);
    });
  }

  function updateCount() {
    var n = matches().length;
    els.count.textContent = !n ? 'No questions match these settings'
      : n < ROUND ? (n + ' question' + (n === 1 ? '' : 's') + ' match, so this will be a short round (it won\'t count toward your best score)')
      : (n.toLocaleString() + ' questions match');
    els.start.disabled = n === 0;
    var s = VAGames.get('trivia');
    els.best.textContent = s.plays ? ('Your best: ' + (s.best || 0) + ' of 10 · ' + s.plays + ' round' + (s.plays === 1 ? '' : 's') + ' played') : 'No rounds played yet';
  }

  function shuffle(a, rnd) {
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor((rnd || Math.random)() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  function pickRound() {
    var pool = matches();
    var seen = VAGames.seenList('trivia');
    var fresh = pool.filter(function (q) { return seen.indexOf(q.id) === -1; });
    var src = fresh.length >= ROUND ? fresh : pool;
    var picked = [];
    if (els.diff.value === 'mixed') {
      // Aim for 3 easy, 4 medium, 3 hard, then fill from whatever is left.
      var want = { 1: 3, 2: 4, 3: 3 };
      [1, 2, 3].forEach(function (d) {
        picked = picked.concat(shuffle(src.filter(function (q) { return q.diff === d; })).slice(0, want[d]));
      });
    }
    var rest = shuffle(src.filter(function (q) { return picked.indexOf(q) === -1; }));
    picked = picked.concat(rest).slice(0, Math.min(ROUND, src.length));
    return shuffle(picked).sort(function (a, b) { return a.diff - b.diff; });
  }

  function start() {
    var qs = pickRound();
    if (!qs.length) return;
    round = { qs: qs, i: 0, answers: [] };
    show('play');
    renderQuestion();
  }

  function renderQuestion() {
    var q = round.qs[round.i];
    var box = els.play;
    box.innerHTML = '';
    var head = document.createElement('div');
    head.className = 'tv-head';
    head.innerHTML = '<span class="tv-progress">Question ' + (round.i + 1) + ' of ' + round.qs.length + '</span>' +
      '<span class="gm-chip" data-cat="' + q.cat + '">' + CAT_LABEL[q.cat] + '</span>' +
      '<span class="gm-chip ghost">' + q.topic + ' · ' + DIFF_LABEL[q.diff] + '</span>';
    box.appendChild(head);
    var bar = document.createElement('div');
    bar.className = 'tv-bar';
    bar.innerHTML = '<span style="width:' + Math.round(round.i / round.qs.length * 100) + '%"></span>';
    box.appendChild(bar);
    var h = document.createElement('h2');
    h.className = 'tv-q';
    h.id = 'tv-q';
    h.textContent = q.q;
    box.appendChild(h);
    var list = document.createElement('div');
    list.className = 'tv-choices';
    list.setAttribute('role', 'group');
    list.setAttribute('aria-labelledby', 'tv-q');
    q.choices.forEach(function (c, idx) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'tv-choice';
      b.innerHTML = '<span class="k" aria-hidden="true">' + (idx + 1) + '</span><span class="t"></span>';
      b.querySelector('.t').textContent = c;
      b.addEventListener('click', function () { answer(idx); });
      list.appendChild(b);
    });
    box.appendChild(list);
    var fb = document.createElement('div');
    fb.className = 'tv-feedback';
    fb.setAttribute('aria-live', 'polite');
    box.appendChild(fb);
    h.setAttribute('tabindex', '-1');
    h.focus({ preventScroll: true });
  }

  function answer(idx) {
    var q = round.qs[round.i];
    if (round.answers.length > round.i) return;
    var right = idx === q.answer;
    round.answers.push(idx);
    var btns = els.play.querySelectorAll('.tv-choice');
    btns.forEach(function (b, j) {
      b.disabled = true;
      if (j === q.answer) b.classList.add('is-right');
      if (j === idx && !right) b.classList.add('is-wrong');
      if (j === idx) b.setAttribute('aria-pressed', 'true');
    });
    var fb = els.play.querySelector('.tv-feedback');
    fb.innerHTML = '<p class="tv-verdict ' + (right ? 'ok' : 'no') + '">' + (right ? 'Correct.' : 'Not quite.') + '</p><p class="tv-why"></p>';
    fb.querySelector('.tv-why').textContent = q.why;
    var next = document.createElement('button');
    next.type = 'button';
    next.className = 'gm-btn';
    next.textContent = round.i + 1 < round.qs.length ? 'Next question' : 'See your score';
    next.addEventListener('click', function () {
      if (round.finished || next.disabled) return;
      next.disabled = true;
      round.i += 1;
      if (round.i < round.qs.length) renderQuestion(); else finish();
    });
    fb.appendChild(next);
    next.focus({ preventScroll: true });
  }

  function verdictLine(score, n) {
    var pct = score / n;
    if (pct === 1) return 'Perfect round. Hall of Fame material.';
    if (pct >= 0.8) return 'All-American round.';
    if (pct >= 0.6) return 'A winning record. Bowl eligible.';
    if (pct >= 0.4) return 'A .500 kind of day. Next one.';
    return 'A rebuilding year. Go anyway.';
  }

  function finish() {
    if (round.finished) return;
    round.finished = true;
    els.play.innerHTML = '';
    var qs = round.qs, n = qs.length;
    var score = round.answers.filter(function (a, i) { return a === qs[i].answer; }).length;
    var stats = VAGames.record('trivia', {
      plays: 1, correct: score, answered: n,
      best: n === ROUND ? score : 0, perfect: (n === ROUND && score === n) ? 1 : 0
    });
    VAGames.seen('trivia', qs.map(function (q) { return q.id; }), 400);
    var box = els.done;
    box.innerHTML = '';
    var top = document.createElement('div');
    top.className = 'tv-score';
    top.innerHTML = '<div class="n"><b>' + score + '</b><span>/ ' + n + '</span></div>' +
      '<p class="line"></p>' +
      '<p class="muted">Best round: ' + (stats.best || 0) + ' of 10 · Accuracy: ' +
      Math.round((stats.correct / Math.max(1, stats.answered)) * 100) + '% over ' + stats.plays + ' round' + (stats.plays === 1 ? '' : 's') + '</p>';
    top.querySelector('.line').textContent = verdictLine(score, n);
    box.appendChild(top);
    var actions = document.createElement('div');
    actions.className = 'gm-actions';
    actions.innerHTML = '<button type="button" class="gm-btn" data-again>Play another round</button>' +
      '<button type="button" class="gm-btn ghost" data-settings>Change settings</button>';
    actions.querySelector('[data-again]').addEventListener('click', start);
    actions.querySelector('[data-settings]').addEventListener('click', function () { updateCount(); show('setup'); });
    box.appendChild(actions);
    var h = document.createElement('h2');
    h.className = 'section';
    h.textContent = 'Your answers';
    box.appendChild(h);
    var ol = document.createElement('ol');
    ol.className = 'tv-review';
    qs.forEach(function (q, i) {
      var li = document.createElement('li');
      var ok = round.answers[i] === q.answer;
      li.className = ok ? 'ok' : 'no';
      li.innerHTML = '<p class="q"></p><p class="a"></p><p class="why muted"></p>';
      li.querySelector('.q').textContent = q.q;
      li.querySelector('.a').textContent = ok ? ('✓ ' + q.choices[q.answer]) : ('✗ You said ' + q.choices[round.answers[i]] + '. Answer: ' + q.choices[q.answer]);
      li.querySelector('.why').textContent = q.why;
      ol.appendChild(li);
    });
    box.appendChild(ol);
    show('done');
    top.setAttribute('tabindex', '-1');
    top.focus({ preventScroll: true });
  }

  document.addEventListener('keydown', function (e) {
    if (!round || els.play.hidden) return;
    if (e.target && /INPUT|SELECT|TEXTAREA/.test(e.target.tagName)) return;
    var n = parseInt(e.key, 10);
    if (n >= 1 && n <= 4 && round.answers.length === round.i) {
      var b = els.play.querySelectorAll('.tv-choice')[n - 1];
      if (b) b.click();
    }
  });

  [els.cat, els.era, els.diff].forEach(function (s) { s.addEventListener('change', updateCount); });
  els.start.addEventListener('click', start);

  fetch(DATA_URL).then(function (r) { return r.json(); }).then(function (data) {
    all = data.questions;
    updateCount();
    root.classList.remove('is-loading');
  }).catch(function () {
    els.count.textContent = 'The question bank could not be loaded. Try refreshing the page.';
  });

  if (!VAGames.isPersistent()) {
    var warn = root.querySelector('[data-storage-note]');
    if (warn) warn.hidden = false;
  }
})();
