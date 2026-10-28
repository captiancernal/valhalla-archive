// Shared helpers for the Archive's games: personal stats saved in this browser only.
// If the browser blocks storage, everything still works for the visit; it just isn't remembered.
(function () {
  var KEY = 'va-games-v1';
  var memory = {};
  var persistent = true;

  function readAll() {
    try {
      var raw = window.localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (e) {
      persistent = false;
      return memory;
    }
  }
  function writeAll(data) {
    memory = data;
    try {
      window.localStorage.setItem(KEY, JSON.stringify(data));
    } catch (e) {
      persistent = false;
    }
  }
  function today() {
    var d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function dayDiff(a, b) {
    var pa = a.split('-'), pb = b.split('-');
    var da = Date.UTC(+pa[0], pa[1] - 1, +pa[2]), db = Date.UTC(+pb[0], pb[1] - 1, +pb[2]);
    return Math.round((db - da) / 86400000);
  }

  var VAGames = {
    isPersistent: function () { readAll(); return persistent; },
    get: function (game) {
      var all = readAll();
      return all[game] || {};
    },
    all: function () { return readAll(); },
    // Merge a finished play into a game's stats and update the daily streak.
    record: function (game, update) {
      var all = readAll();
      var s = all[game] || {};
      Object.keys(update).forEach(function (k) {
        var v = update[k];
        if (k === 'best') { s.best = Math.max(s.best || 0, v); }
        else if (typeof v === 'number') { s[k] = (s[k] || 0) + v; }
        else { s[k] = v; }
      });
      s.lastPlayed = today();
      all[game] = s;
      var meta = all._meta || {};
      var t = today();
      if (meta.lastDay !== t) {
        meta.streak = (meta.lastDay && dayDiff(meta.lastDay, t) === 1) ? (meta.streak || 0) + 1 : 1;
        meta.bestStreak = Math.max(meta.bestStreak || 0, meta.streak);
        meta.lastDay = t;
      }
      all._meta = meta;
      writeAll(all);
      return s;
    },
    // Remember recently seen item ids so practice rounds don't repeat too soon.
    seen: function (game, ids, keep) {
      var all = readAll();
      var key = '_seen_' + game;
      var list = (all[key] || []).filter(function (x) { return ids.indexOf(x) === -1; }).concat(ids);
      all[key] = list.slice(-(keep || 300));
      writeAll(all);
    },
    seenList: function (game) { return readAll()['_seen_' + game] || []; },
    streak: function () {
      var meta = readAll()._meta || {};
      if (!meta.lastDay) return 0;
      return dayDiff(meta.lastDay, today()) <= 1 ? (meta.streak || 0) : 0;
    },
    reset: function () { writeAll({}); },
    today: today
  };
  window.VAGames = VAGames;
})();
