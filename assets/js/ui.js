/* tenders.best — shared UI behaviour: header, mobile menu, language dropdown (listbox with keyboard). */
window.TBUI = (function () {
  'use strict';
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));
  const LABELS = { ru: 'RU', en: 'EN', tj: 'TJ' };

  function header() {
    const header = $('#header'), menu = $('#mobileMenu'), burger = $('#burger');
    if (!header) return;
    let lastY = window.scrollY, ticking = false;
    const update = () => {
      const y = window.scrollY;
      header.classList.toggle('is-scrolled', y > 8);
      if (y > lastY + 6 && y > 200 && !(menu && menu.classList.contains('is-open'))) header.classList.add('is-hidden');
      else if (y < lastY - 6 || y < 120) header.classList.remove('is-hidden');
      lastY = y; ticking = false;
    };
    window.addEventListener('scroll', () => { if (!ticking) { requestAnimationFrame(update); ticking = true; } }, { passive: true });
    update();
    if (burger && menu) {
      const setMenu = (open) => {
        burger.classList.toggle('is-open', open); menu.classList.toggle('is-open', open);
        burger.setAttribute('aria-expanded', String(open)); document.body.style.overflow = open ? 'hidden' : '';
        if (open) header.classList.remove('is-hidden');
      };
      burger.addEventListener('click', () => setMenu(!menu.classList.contains('is-open')));
      $$('a', menu).forEach((a) => a.addEventListener('click', () => setMenu(false)));
    }
  }

  /* Language listbox: trigger + menu with role=listbox/option, arrow keys, Home/End, Esc, click-outside. */
  function lang(onChange) {
    const root = $('#lang');
    const sync = (code) => {
      $$('[data-set-lang]').forEach((b) => b.setAttribute('aria-selected', String(b.dataset.setLang === code)));
      $$('[data-lang-label]').forEach((el) => { el.textContent = LABELS[code] || code.toUpperCase(); });
      $$('[data-flag]').forEach((el) => { el.innerHTML = '<svg><use href="#flag-' + code + '"/></svg>'; });
    };
    document.addEventListener('click', (e) => {
      const b = e.target.closest('[data-set-lang]');
      if (!b) return;
      const code = b.dataset.setLang;
      sync(code); onChange(code);
      if (root) close();
    });
    if (!root) return sync;
    const btn = $('.lang__btn', root), menu = $('.lang__menu', root);
    const options = () => $$('[role="option"]', menu);
    const open = () => { root.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true'); const cur = options().find((o) => o.getAttribute('aria-selected') === 'true') || options()[0]; cur && cur.focus(); };
    const close = (focusBtn) => { root.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); if (focusBtn) btn.focus(); };
    btn.addEventListener('click', () => (root.classList.contains('is-open') ? close() : open()));
    btn.addEventListener('keydown', (e) => { if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); open(); } });
    menu.addEventListener('keydown', (e) => {
      const list = options(); const i = list.indexOf(document.activeElement);
      if (e.key === 'ArrowDown') { e.preventDefault(); list[(i + 1) % list.length].focus(); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); list[(i - 1 + list.length) % list.length].focus(); }
      else if (e.key === 'Home') { e.preventDefault(); list[0].focus(); }
      else if (e.key === 'End') { e.preventDefault(); list[list.length - 1].focus(); }
      else if (e.key === 'Escape') { e.preventDefault(); close(true); }
      else if (e.key === 'Tab') { close(); }
    });
    document.addEventListener('click', (e) => { if (!root.contains(e.target)) close(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && root.classList.contains('is-open')) close(true); });
    return sync;
  }

  function reveal(animateIn) {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const targets = $$('[data-reveal], [data-anim]');
    if ('IntersectionObserver' in window && !reduce) {
      const io = new IntersectionObserver((entries) => { entries.forEach((e) => { if (e.isIntersecting) { animateIn(e.target); io.unobserve(e.target); } }); }, { threshold: 0.12, rootMargin: '0px 0px -5% 0px' });
      targets.forEach((el) => io.observe(el));
    } else targets.forEach(animateIn);
  }

  return { header, lang, reveal, $, $$ };
})();
