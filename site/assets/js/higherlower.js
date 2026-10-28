// Higher or Lower: guess whether the next real stat line is higher or lower. Keep the streak alive.
(function () {
  var root = document.getElementById('hl');
  if (!root) return;
  var BASE = root.getAttribute('data-base');
  var PROG = { CLEV: 'Cleveland State', OHIO: 'Ohio', 'M-OH': 'Miami (OH)' };
  var decks = [], cards = [], byDeck = {};
  var state = null;
  var setup = root.querySelector('[data-view="setup"]');
  var play = root.querySelector('[data-view="play"]');
  var over = root.querySelector('[data-view="over"]');
  var deckList = root.querySelector('[data-decks]');

  function fmt(v) {
    if (typeof v !== 'number') return v;
    return v % 1 ? v.toFixed(1) : v.toLocaleString();
  }
  function rand(a) { return a[Math.floor(Math.random() * a.length)]; }
  function show(view) {
    [setup, play, over].forEach(function (el) { el.hidden = el !== view; });
  }
  function deckInfo(key) {
    if (key === 'mixed') return { key: 'mixed', label: 'Mixed', unit: '', scope: 'a new stat every turn' };
    return decks.filter(function (d) { return d.key === key; })[0];
  }

  function renderSetup() {
    var s = VAGames.get('higherlower');
    deckList.innerHTML = '';
    decks.concat([{ key: 'mixed', label: 'Mixed', scope: 'a different stat every turn' }]).forEach(function (d, i) {
      var id = 'hl-deck-' + d.key;
      var lab = document.createElement('label');
      lab.className = 'hl-deck';
      var n = d.key === 'mixed' ? cards.length : (byDeck[d.key] || []).length;
      lab.innerHTML = '<input type="radio" name="hl-deck" value="' + d.key + '"' + (i === 0 ? ' checked' : '') + '>' +
        '<span class="nm"></span><span class="sc"></span><span class="bs"></span>';
      lab.querySelector('.nm').textContent = d.label;
      lab.querySelector('.sc').textContent = d.scope + ' · ' + n + ' stat lines';
      var best = s['best_' + d.key];
      lab.querySelector('.bs').textContent = best ? ('Best streak: ' + best) : '';
      deckList.appendChild(lab);
    });
    var tot = root.querySelector('[data-best]');
    tot.textContent = s.plays ? ('Best streak overall: ' + (s.best || 0) + ' · ' + s.plays + ' game' + (s.plays === 1 ? '' : 's') + ' played') : 'No games played yet';
  }

  function pickCard(deck, avoid) {
    var pool = byDeck[deck];
    var recent = state.recent;
    var tries = 0, c;
    do {
      c = rand(pool);
      tries++;
    } while (tries < 60 && (recent.indexOf(c) !== -1 || (avoid && (c.v === avoid.v || (c.t === avoid.t && c.s === avoid.s)))));
    recent.push(c);
    if (recent.length > Math.min(40, Math.floor(pool.length * 0.6))) recent.shift();
    return c;
  }

  function start(deck) {
    state = { deck: deck, streak: 0, recent: [], busy: false };
    var d = deck === 'mixed' ? rand(decks).key : deck;
    state.cur = d;
    state.left = pickCard(d);
    state.right = pickCard(d, state.left);
    show(play);
    renderPlay(false);
  }

  function cardHTML(c, hidden, deck) {
    var logo = BASE + 'assets/logos/sm/' + c.p + '.png';
    return '<div class="hl-card" data-prog="' + c.p + '">' +
      '<div class="hl-top"><img src="' + logo + '" alt="" width="28" height="28"><span class="gm-chip" data-cat="' + c.p + '">' + PROG[c.p] + '</span></div>' +
      '<div class="hl-name"></div>' +
      '<div class="hl-sub"></div>' +
      '<div class="hl-val">' + (hidden ? '<span class="q">?</span>' : '<b>' + fmt(c.v) + '</b>') + '</div>' +
      '<div class="hl-unit">' + deck.unit + '</div>' +
      (c.r && !hidden ? '<div class="hl-rev">' + c.r + '</div>' : '<div class="hl-rev"></div>') +
      '</div>';
  }

  function renderPlay() {
    var deck = deckInfo(state.cur);
    play.innerHTML =
      '<div class="hl-bar"><span class="gm-chip ghost">' + (state.deck === 'mixed' ? 'Mixed · ' : '') + deck.label + '</span>' +
      '<span class="hl-streak">Streak <b>' + state.streak + '</b></span></div>' +
      '<div class="hl-pair">' + cardHTML(state.left, false, deck) +
      '<div class="hl-vs" aria-hidden="true">vs</div>' + cardHTML(state.right, true, deck) + '</div>' +
      '<p class="hl-ask" id="hl-ask"></p>' +
      '<div class="hl-btns" role="group" aria-labelledby="hl-ask">' +
      '<button type="button" class="gm-btn hl-hi" data-guess="hi">▲ Higher</button>' +
      '<button type="button" class="gm-btn hl-lo" data-guess="lo">▼ Lower</button></div>' +
      '<p class="hl-msg" aria-live="polite"></p>';
    var cardsEl = play.querySelectorAll('.hl-card');
    fill(cardsEl[0], state.left);
    fill(cardsEl[1], state.right);
    play.querySelector('.hl-ask').textContent = 'Did ' + state.right.t + ' (' + state.right.s + ') have more or fewer ' + deck.unit + ' than ' + state.left.t + ' (' + state.left.s + ')?';
    play.querySelectorAll('[data-guess]').forEach(function (b) {
      b.addEventListener('click', function () { guess(b.getAttribute('data-guess')); });
    });
    play.querySelector('.hl-hi').focus({ preventScroll: true });
  }
  function fill(el, c) {
    el.querySelector('.hl-name').textContent = c.t;
    el.querySelector('.hl-sub').textContent = c.s + (c.sub ? ' · ' + c.sub : '');
  }

  function guess(which) {
    if (state.busy) return;
    state.busy = true;
    var L = state.left.v, R = state.right.v;
    var ok = R === L || (which === 'hi' ? R > L : R < L);
    var right = play.querySelectorAll('.hl-card')[1];
    var deck = deckInfo(state.cur);
    right.querySelector('.hl-val').innerHTML = '<b>' + fmt(R) + '</b>';
    if (state.right.r) right.querySelector('.hl-rev').textContent = state.right.r;
    right.classList.add(ok ? 'is-right' : 'is-wrong');
    play.querySelectorAll('[data-guess]').forEach(function (b) { b.disabled = true; });
    var msg = play.querySelector('.hl-msg');
    var diffTxt = R === L ? 'Exactly the same, so either answer counts.' :
      (state.right.t + ' had ' + fmt(R) + ' ' + deck.unit + ', ' + (R > L ? 'more' : 'fewer') + ' than ' + fmt(L) + '.');
    msg.textContent = (ok ? 'Correct. ' : 'Not this time. ') + diffTxt;
    if (ok) {
      state.streak += 1;
      setTimeout(function () {
        if (state.deck === 'mixed') {
          state.cur = rand(decks).key;
          state.left = pickCard(state.cur);
        } else {
          state.left = state.right;
        }
        state.right = pickCard(state.cur, state.left);
        state.busy = false;
        renderPlay();
      }, 1400);
    } else {
      setTimeout(gameOver, 1600);
    }
  }

  function gameOver() {
    var upd = { plays: 1, correct: state.streak, answered: state.streak + 1, best: state.streak };
    upd['best_' + state.deck] = state.streak;
    var s = VAGames.record('higherlower', upd);
    var deck = deckInfo(state.deck);
    over.innerHTML = '<div class="tv-score"><div class="n"><b>' + state.streak + '</b><span>in a row</span></div>' +
      '<p class="line"></p><p class="muted">Best ' + deck.label.toLowerCase() + ' streak: ' + (s['best_' + state.deck] || 0) +
      ' · Best overall: ' + (s.best || 0) + '</p></div>' +
      '<div class="gm-actions" style="justify-content:center"><button type="button" class="gm-btn" data-again>Play again</button>' +
      '<button type="button" class="gm-btn ghost" data-decks-btn>Change deck</button></div>';
    var line = state.streak >= 15 ? 'A dynasty run.' : state.streak >= 10 ? 'Conference champions.' : state.streak >= 5 ? 'Bowl eligible.' : state.streak >= 1 ? 'Every streak starts somewhere.' : 'Fumbled the opening kickoff. Go again.';
    over.querySelector('.line').textContent = line;
    over.querySelector('[data-again]').addEventListener('click', function () { start(state.deck); });
    over.querySelector('[data-decks-btn]').addEventListener('click', function () { renderSetup(); show(setup); });
    show(over);
    over.querySelector('[data-again]').focus({ preventScroll: true });
  }

  document.addEventListener('keydown', function (e) {
    if (play.hidden || !state || state.busy) return;
    if (e.key === 'ArrowUp' || e.key === 'h' || e.key === 'H') { e.preventDefault(); guess('hi'); }
    if (e.key === 'ArrowDown' || e.key === 'l' || e.key === 'L') { e.preventDefault(); guess('lo'); }
  });
  root.querySelector('[data-start]').addEventListener('click', function () {
    var sel = root.querySelector('input[name="hl-deck"]:checked');
    start(sel ? sel.value : decks[0].key);
  });

  fetch(root.getAttribute('data-src')).then(function (r) { return r.json(); }).then(function (data) {
    decks = data.decks;
    cards = data.cards;
    cards.forEach(function (c) { (byDeck[c.d] = byDeck[c.d] || []).push(c); });
    renderSetup();
    root.querySelector('[data-start]').disabled = false;
  }).catch(function () {
    root.querySelector('[data-best]').textContent = 'The stat lines could not be loaded. Try refreshing the page.';
  });
  if (!VAGames.isPersistent()) root.querySelector('[data-storage-note]').hidden = false;
})();
