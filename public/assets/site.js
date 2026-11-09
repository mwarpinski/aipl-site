// aipl.sh: tabs, copy buttons, the install page's OS choice. The pages read fine without it.
(function () {
  function tabs(root) {
    var list = root.querySelectorAll('[role="tab"]');
    function pick(tab) {
      list.forEach(function (t) {
        var on = t === tab;
        t.setAttribute('aria-selected', on ? 'true' : 'false');
        t.tabIndex = on ? 0 : -1;
        var p = document.getElementById(t.getAttribute('aria-controls'));
        if (p) p.hidden = !on;
      });
    }
    list.forEach(function (t, i) {
      t.addEventListener('click', function () { pick(t); });
      t.addEventListener('keydown', function (e) {
        var j = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : -1;
        if (j < 0) return;
        j = (j + list.length) % list.length;
        list[j].focus(); pick(list[j]); e.preventDefault();
      });
    });
    return pick;
  }
  document.querySelectorAll('[data-tabs]').forEach(tabs);

  document.querySelectorAll('.copy').forEach(function (b) {
    b.addEventListener('click', function () {
      var code = b.parentNode.querySelector('code');
      var text = code.innerText.replace(/\s+$/, '');
      var done = function () { b.dataset.done = '1'; b.textContent = 'Copied'; setTimeout(function () { delete b.dataset.done; b.textContent = 'Copy'; }, 1600); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () {});
    });
  });

  // the install page: Linux, macOS, Windows; the visitor's own system first
  var os = document.querySelector('[data-os]');
  if (os) {
    var pick = tabs(os);
    var ua = (navigator.userAgent || '') + ' ' + (navigator.platform || '');
    var want = /Win/i.test(ua) ? 'os-win' : /Mac/i.test(ua) ? 'os-mac' : 'os-linux';
    var tab = os.querySelector('[aria-controls="' + want + '"]');
    if (tab) pick(tab);
  }
})();
