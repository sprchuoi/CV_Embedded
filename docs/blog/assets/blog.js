/* DSP blog - progressive enhancement only.
 *
 * Nothing here is required to read an article: with JavaScript disabled the
 * page renders, the TOC links still jump, and the maths still typesets. These
 * four behaviours are comfort features, so every one of them is wrapped so a
 * failure cannot break the page.
 */
(function () {
  'use strict';

  var THEME_KEY = 'dsp-blog-theme';

  /* Every user-visible string lives in a data- attribute on <body>, written by
   * the page template in the page's own language. The fallbacks only matter if
   * the script is somehow served against a page that predates them. */
  var L = null;
  function labels() {
    if (!L) {
      var b = document.body || {};
      var get = function (name, fallback) {
        var value = b.getAttribute ? b.getAttribute(name) : null;
        return value || fallback;
      };
      L = {
        copy: get('data-copy', 'Copy'),
        copied: get('data-copied', 'Copied'),
        failed: get('data-copy-failed', 'Failed'),
        toDark: get('data-theme-dark', 'Switch to dark theme'),
        toLight: get('data-theme-light', 'Switch to light theme')
      };
    }
    return L;
  }

  /* ------------------------------------------------------------- theming -- */
  function applyTheme(theme) {
    if (theme === 'dark' || theme === 'light') {
      document.documentElement.setAttribute('data-theme', theme);
    } else {
      document.documentElement.removeAttribute('data-theme');
    }
    var btn = document.querySelector('[data-theme-toggle]');
    if (btn) {
      var dark = theme === 'dark' ||
        (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches);
      btn.setAttribute('aria-pressed', String(dark));
      btn.setAttribute('title', dark ? labels().toLight : labels().toDark);
      var icon = btn.querySelector('i');
      if (icon) { icon.className = dark ? 'fa-solid fa-sun' : 'fa-solid fa-moon'; }
    }
  }

  function storedTheme() {
    try { return localStorage.getItem(THEME_KEY); } catch (e) { return null; }
  }

  function initTheme() {
    applyTheme(storedTheme());
    var btn = document.querySelector('[data-theme-toggle]');
    if (!btn) { return; }
    btn.addEventListener('click', function () {
      var now = document.documentElement.getAttribute('data-theme');
      var isDark = now === 'dark' ||
        (!now && window.matchMedia('(prefers-color-scheme: dark)').matches);
      var next = isDark ? 'light' : 'dark';
      try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* private mode */ }
      applyTheme(next);
    });
  }

  /* --------------------------------------------------- reading progress -- */
  function initProgress() {
    var bar = document.querySelector('.read-progress');
    if (!bar) { return; }
    var ticking = false;
    function update() {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
      bar.style.width = Math.max(0, Math.min(100, pct)) + '%';
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ----------------------------------------------------------- toc spy -- */
  function initTocSpy() {
    var links = Array.prototype.slice.call(document.querySelectorAll('.toc a[href^="#"]'));
    if (!links.length || !('IntersectionObserver' in window)) { return; }

    var byId = {};
    var targets = [];
    links.forEach(function (link) {
      var el = document.getElementById(decodeURIComponent(link.hash.slice(1)));
      if (el) { byId[el.id] = link; targets.push(el); }
    });
    if (!targets.length) { return; }

    var visible = {};
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { visible[entry.target.id] = entry.isIntersecting; });
      var current = null;
      for (var i = 0; i < targets.length; i++) {
        if (visible[targets[i].id]) { current = targets[i].id; break; }
      }
      links.forEach(function (l) { l.classList.remove('active'); });
      if (current && byId[current]) { byId[current].classList.add('active'); }
    }, { rootMargin: '-5rem 0px -70% 0px', threshold: 0 });

    targets.forEach(function (t) { observer.observe(t); });
  }

  /* --------------------------------------------------------- copy code -- */
  function initCopyButtons() {
    if (!navigator.clipboard) { return; }
    Array.prototype.forEach.call(document.querySelectorAll('.prose pre'), function (pre) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'copy-btn';
      btn.textContent = labels().copy;
      btn.addEventListener('click', function () {
        var code = pre.querySelector('code');
        navigator.clipboard.writeText(code ? code.innerText : pre.innerText).then(function () {
          btn.textContent = labels().copied;
          window.setTimeout(function () { btn.textContent = labels().copy; }, 1400);
        }, function () { btn.textContent = labels().failed; });
      });
      pre.appendChild(btn);
    });
  }

  function boot() {
    [initTheme, initProgress, initTocSpy, initCopyButtons].forEach(function (fn) {
      try { fn(); } catch (e) { if (window.console) { console.warn('[blog]', e); } }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
