// Word Search: themed grids from the Archive's data. Drag across a word or tap its first and last letter.
(function () {
  var root = document.getElementById('ws');
  if (!root) return;
  var puzzles = [], byId = {};
  var cur = null; // {p, size, grid:[[ch]], placed:[{w,label,cells:[[r,c]]}], found:{}, start, timer}
  var els = {
    pick: root.querySelector('#ws-pick'),
    diff: root.querySelectorAll('input[name="ws-diff"]'),
    grid: root.querySelector('[data-grid]'),
    words: root.querySelector('[data-words]'),
    title: root.querySelector('[data-title]'),
    blurb: root.querySelector('[data-blurb]'),
    status: root.querySelector('[data-status]'),
    clock: root.querySelector('[data-clock]'),
    key: root.querySelector('[data-key]'),
    keyToggle: root.querySelector('#ws-key')
  };
  var DIRS_EASY = [[0, 1], [1, 0]];
  var DIRS_HARD = [[0, 1], [1, 0], [1, 1], [-1, 1], [0, -1], [-1, 0], [-1, -1], [1, -1]];
  var COLORS = ['#cfe8d6', '#f6e3a7', '#d6e4f5', '#f5d3d6', '#e2d6f2', '#d3efe9', '#f7dcc0', '#e6e6c8', '#cde3f0', '#efd2e6', '#d9ead0', '#f2e1cf', '#d5dbef', '#f0d9d9'];

  function hash(s) { var h = 2166136261; for (var i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
  function seeded(seed) { return function () { seed = (seed + 0x6D2B79F5) | 0; var t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function difficulty() { var d = 'easy'; els.diff.forEach(function (r) { if (r.checked) d = r.value; }); return d; }

  // ---------- layout
  function layout(p, diff, layoutNo) {
    var words = p.words.slice().sort(function (a, b) { return b.w.length - a.w.length; });
    var longest = words[0].w.length;
    var size = diff === 'hard' ? Math.min(15, Math.max(14, longest + 2)) : Math.min(15, Math.max(12, longest + 1));
    var dirs = diff === 'hard' ? DIRS_HARD : DIRS_EASY;
    for (var attempt = 0; attempt < 60; attempt++) {
      var rnd = seeded(hash(p.id + '|' + diff + '|' + layoutNo + '|' + attempt));
      var grid = [], placed = [], ok = true;
      for (var r = 0; r < size; r++) { grid.push([]); for (var c = 0; c < size; c++) grid[r].push(''); }
      for (var wi = 0; wi < words.length && ok; wi++) {
        var w = words[wi].w, done = false;
        for (var t = 0; t < 400 && !done; t++) {
          var d = dirs[Math.floor(rnd() * dirs.length)];
          var r0 = Math.floor(rnd() * size), c0 = Math.floor(rnd() * size);
          var r1 = r0 + d[0] * (w.length - 1), c1 = c0 + d[1] * (w.length - 1);
          if (r1 < 0 || r1 >= size || c1 < 0 || c1 >= size) continue;
          var fits = true, cells = [];
          for (var k = 0; k < w.length; k++) {
            var rr = r0 + d[0] * k, cc = c0 + d[1] * k;
            if (grid[rr][cc] && grid[rr][cc] !== w[k]) { fits = false; break; }
            cells.push([rr, cc]);
          }
          if (!fits) continue;
          cells.forEach(function (x, k2) { grid[x[0]][x[1]] = w[k2]; });
          placed.push({ w: w, label: words[wi].label, cells: cells });
          done = true;
        }
        if (!done) ok = false;
      }
      if (!ok) continue;
      // Fill blanks with letters drawn from the puzzle's own words, so names don't stand out.
      var pool = p.words.map(function (x) { return x.w; }).join('');
      for (r = 0; r < size; r++) for (c = 0; c < size; c++) if (!grid[r][c]) grid[r][c] = pool[Math.floor(rnd() * pool.length)];
      // Keep the word list in the theme's own order.
      placed.sort(function (a, b) { return p.words.findIndex(function (x) { return x.w === a.w; }) - p.words.findIndex(function (x) { return x.w === b.w; }); });
      return { size: size, grid: grid, placed: placed };
    }
    return null;
  }

  // ---------- rendering
  function load(id, layoutNo) {
    var p = byId[id];
    var diff = difficulty();
    var L = layout(p, diff, layoutNo || 0);
    if (!L) { els.status.textContent = 'This puzzle could not be laid out. Try a new layout.'; return; }
    stopClock();
    cur = { p: p, diff: diff, layoutNo: layoutNo || 0, size: L.size, grid: L.grid, placed: L.placed, found: {}, start: null, sel: null, t0: null, done: false };
    els.title.textContent = p.title;
    els.blurb.textContent = p.blurb + (diff === 'hard' ? ' Hard: words can run in any of eight directions, including backwards.' : ' Easy: words run left to right or top to bottom.');
    els.grid.style.setProperty('--n', L.size);
    els.grid.innerHTML = '';
    els.grid.setAttribute('aria-rowcount', L.size);
    for (var r = 0; r < L.size; r++) {
      var row = document.createElement('div');
      row.setAttribute('role', 'row');
      row.className = 'ws-row';
      for (var c = 0; c < L.size; c++) {
        var b = document.createElement('div');
        b.className = 'ws-cell';
        b.setAttribute('role', 'gridcell');
        b.setAttribute('data-r', r);
        b.setAttribute('data-c', c);
        b.tabIndex = (r === 0 && c === 0) ? 0 : -1;
        b.textContent = L.grid[r][c];
        row.appendChild(b);
      }
      els.grid.appendChild(row);
    }
    els.words.innerHTML = '';
    L.placed.forEach(function (pw, i) {
      var li = document.createElement('li');
      li.setAttribute('data-w', pw.w);
      li.innerHTML = '<span class="w"></span><span class="lab"></span>';
      li.querySelector('.w').textContent = pw.w;
      li.querySelector('.lab').textContent = pw.label;
      els.words.appendChild(li);
    });
    renderKey();
    els.status.textContent = '0 of ' + L.placed.length + ' found';
    els.clock.textContent = '0:00';
    try { localStorage.setItem('va-ws-last', id); } catch (e) {}
  }

  function renderKey() {
    // Answer key for printing: the same grid with the hidden words in bold.
    var on = {};
    cur.placed.forEach(function (pw) { pw.cells.forEach(function (x) { on[x[0] + ',' + x[1]] = 1; }); });
    var html = '<h2>Answer key: ' + String(cur.p.title).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }) + '</h2><div class="ws-keygrid" style="--n:' + cur.size + '">';
    for (var r = 0; r < cur.size; r++) for (var c = 0; c < cur.size; c++) {
      html += '<span' + (on[r + ',' + c] ? ' class="on"' : '') + '>' + cur.grid[r][c] + '</span>';
    }
    els.key.innerHTML = html + '</div>';
  }

  function cellAt(r, c) { return els.grid.querySelector('[data-r="' + r + '"][data-c="' + c + '"]'); }
  function lineCells(a, b) {
    var dr = b[0] - a[0], dc = b[1] - a[1];
    var len = Math.max(Math.abs(dr), Math.abs(dc));
    if (!(dr === 0 || dc === 0 || Math.abs(dr) === Math.abs(dc))) return null;
    var sr = Math.sign(dr), sc = Math.sign(dc), out = [];
    for (var k = 0; k <= len; k++) out.push([a[0] + sr * k, a[1] + sc * k]);
    return out;
  }
  function paintSelection(cells) {
    els.grid.querySelectorAll('.is-sel').forEach(function (x) { x.classList.remove('is-sel'); });
    (cells || []).forEach(function (x) { var el = cellAt(x[0], x[1]); if (el) el.classList.add('is-sel'); });
  }

  function check(cells) {
    if (!cells || cells.length < 2) return false;
    var word = cells.map(function (x) { return cur.grid[x[0]][x[1]]; }).join('');
    var rev = word.split('').reverse().join('');
    for (var i = 0; i < cur.placed.length; i++) {
      var pw = cur.placed[i];
      if (cur.found[pw.w]) continue;
      var key = pw.cells.map(String).join('|');
      var fwd = cells.map(String).join('|'), back = cells.slice().reverse().map(String).join('|');
      if ((word === pw.w || rev === pw.w) && (key === fwd || key === back)) {
        markFound(pw, i);
        return true;
      }
    }
    return false;
  }
  function markFound(pw, i) {
    cur.found[pw.w] = true;
    var color = COLORS[i % COLORS.length];
    pw.cells.forEach(function (x) { var el = cellAt(x[0], x[1]); el.classList.add('is-found'); el.style.setProperty('--hl', color); });
    var li = els.words.querySelector('[data-w="' + pw.w + '"]');
    if (li) { li.classList.add('is-found'); li.style.setProperty('--hl', color); }
    var n = Object.keys(cur.found).length, total = cur.placed.length;
    els.status.textContent = 'Found ' + pw.label + '. ' + n + ' of ' + total + ' found.';
    if (n === total) win();
  }
  function win() {
    cur.done = true;
    stopClock();
    var secs = Math.round((Date.now() - (cur.t0 || Date.now())) / 1000);
    var s = VAGames.record('wordsearch', { plays: 1, completed: 1 });
    if (!s.fastest || secs < s.fastest) { s.fastest = secs; VAGames.setItem('wordsearch', s); }
    els.status.textContent = 'All ' + cur.placed.length + ' found in ' + fmtTime(secs) + '! Pick another puzzle or try a new layout.';
    root.classList.add('is-done');
  }

  // ---------- clock
  function startClock() {
    if (cur.t0) return;
    cur.t0 = Date.now();
    cur.timer = setInterval(function () { els.clock.textContent = fmtTime(Math.round((Date.now() - cur.t0) / 1000)); }, 1000);
  }
  function stopClock() { if (cur && cur.timer) { clearInterval(cur.timer); cur.timer = null; } }
  function fmtTime(s) { return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); }

  // ---------- pointer selection: drag across, or tap the first then the last letter
  var drag = null;
  function posOf(target) {
    var el = target && target.closest ? target.closest('.ws-cell') : null;
    return el ? [+el.getAttribute('data-r'), +el.getAttribute('data-c')] : null;
  }
  els.grid.addEventListener('pointerdown', function (e) {
    var p = posOf(e.target);
    if (!p || cur.done) return;
    e.preventDefault();
    startClock();
    drag = { a: p, moved: false };
    paintSelection([p]);
  });
  els.grid.addEventListener('pointermove', function (e) {
    if (!drag) return;
    var el = document.elementFromPoint(e.clientX, e.clientY);
    var p = posOf(el);
    if (!p) return;
    if (p[0] !== drag.a[0] || p[1] !== drag.a[1]) drag.moved = true;
    var cells = lineCells(drag.a, p);
    if (cells) { drag.b = p; paintSelection(cells); }
  });
  document.addEventListener('pointerup', function () {
    if (!drag) return;
    var d = drag; drag = null;
    if (d.moved && d.b) {
      check(lineCells(d.a, d.b));
      paintSelection([]);
      cur.sel = null;
    } else {
      // tap: first tap sets the start, second tap finishes the line
      if (cur.sel && (cur.sel[0] !== d.a[0] || cur.sel[1] !== d.a[1])) {
        var found = check(lineCells(cur.sel, d.a));
        if (!found) els.status.textContent = 'No hidden word there. ' + Object.keys(cur.found).length + ' of ' + cur.placed.length + ' found.';
        cur.sel = null;
        paintSelection([]);
      } else {
        cur.sel = d.a;
        paintSelection([d.a]);
      }
    }
  });

  // ---------- keyboard: arrows move, Enter or Space marks the first and last letter
  els.grid.addEventListener('keydown', function (e) {
    var p = posOf(document.activeElement);
    if (!p) return;
    var mv = { ArrowUp: [-1, 0], ArrowDown: [1, 0], ArrowLeft: [0, -1], ArrowRight: [0, 1] }[e.key];
    if (mv) {
      e.preventDefault();
      var nr = Math.max(0, Math.min(cur.size - 1, p[0] + mv[0])), nc = Math.max(0, Math.min(cur.size - 1, p[1] + mv[1]));
      var el = cellAt(nr, nc);
      document.activeElement.tabIndex = -1; el.tabIndex = 0; el.focus();
      if (cur.sel) { var cells = lineCells(cur.sel, [nr, nc]); paintSelection(cells || [cur.sel]); }
    } else if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      startClock();
      if (!cur.sel) { cur.sel = p; paintSelection([p]); els.status.textContent = 'Start set at ' + cur.grid[p[0]][p[1]] + '. Move to the last letter and press Enter.'; }
      else { var ok = check(lineCells(cur.sel, p)); if (!ok) els.status.textContent = 'No hidden word there.'; cur.sel = null; paintSelection([]); }
    } else if (e.key === 'Escape') { cur.sel = null; paintSelection([]); }
  });

  // ---------- controls
  els.pick.addEventListener('change', function () { root.classList.remove('is-done'); load(els.pick.value, 0); });
  els.diff.forEach(function (r) { r.addEventListener('change', function () { root.classList.remove('is-done'); load(cur.p.id, 0); }); });
  root.querySelector('[data-relayout]').addEventListener('click', function () { root.classList.remove('is-done'); load(cur.p.id, cur.layoutNo + 1); });
  root.querySelector('[data-print]').addEventListener('click', function () { window.print(); });
  els.keyToggle.addEventListener('change', function () { root.classList.toggle('print-key', els.keyToggle.checked); });

  fetch(root.getAttribute('data-src')).then(function (r) { return r.json(); }).then(function (d) {
    puzzles = d.puzzles;
    var groups = {};
    puzzles.forEach(function (p) { byId[p.id] = p; (groups[p.cat] = groups[p.cat] || []).push(p); });
    ['Legends', 'Rosters', 'Award winners', 'Schedules'].forEach(function (cat) {
      if (!groups[cat]) return;
      var og = document.createElement('optgroup');
      og.label = cat;
      groups[cat].slice().reverse().forEach(function (p) {
        var o = document.createElement('option'); o.value = p.id; o.textContent = p.title; og.appendChild(o);
      });
      els.pick.appendChild(og);
    });
    var last = null;
    try { last = localStorage.getItem('va-ws-last'); } catch (e) {}
    var first = byId[last] ? last : (byId['legends-CLEV-1'] ? 'legends-CLEV-1' : puzzles[0].id);
    els.pick.value = first;
    load(first, 0);
  }).catch(function () { els.status.textContent = 'The puzzles could not be loaded. Try refreshing the page.'; });
})();
