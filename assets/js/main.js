/* tenders.best — landing interactions */
(function () {
  'use strict';
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));

  /* ---------- language ---------- */
  const LANGS = { ru: 'RU', en: 'EN', tj: 'TJ' };
  const original = new Map();
  const applyLang = (lang) => {
    if (!LANGS[lang]) lang = 'ru';
    const dict = (window.TB_I18N || {})[lang] || {};
    $$('[data-i]').forEach((el) => {
      if (!original.has(el)) original.set(el, el.innerHTML);
      const v = dict[el.dataset.i];
      el.innerHTML = lang === 'ru' || v == null ? original.get(el) : v;
    });
    document.documentElement.lang = lang === 'tj' ? 'tg' : lang;
    $$('[data-set-lang]').forEach((b) => b.setAttribute('aria-current', String(b.dataset.setLang === lang)));
    $$('[data-lang-label]').forEach((el) => { el.textContent = LANGS[lang]; });
    $$('[data-flag]').forEach((el) => { el.className = 'flag flag--' + lang; });
    try { localStorage.setItem('tb_lang', lang); } catch (e) { /* ignore */ }
  };
  let saved = 'ru';
  try { saved = localStorage.getItem('tb_lang') || 'ru'; } catch (e) { /* ignore */ }
  applyLang(saved);

  const lang = $('#lang');
  if (lang) {
    const btn = $('.lang__btn', lang);
    const toggle = (open) => { lang.classList.toggle('is-open', open); btn.setAttribute('aria-expanded', String(open)); };
    btn.addEventListener('click', () => toggle(!lang.classList.contains('is-open')));
    document.addEventListener('click', (e) => { if (!lang.contains(e.target)) toggle(false); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') toggle(false); });
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-set-lang]');
    if (!b) return;
    applyLang(b.dataset.setLang);
    if (lang) lang.classList.remove('is-open');
  });

  /* ---------- header: compact after scroll, hidden on scroll down ---------- */
  const header = $('#header');
  const menu = $('#mobileMenu');
  let lastY = window.scrollY, ticking = false;
  const updateHeader = () => {
    const y = window.scrollY;
    header.classList.toggle('is-scrolled', y > 8);
    if (y > lastY + 6 && y > 200 && !menu.classList.contains('is-open')) header.classList.add('is-hidden');
    else if (y < lastY - 6 || y < 120) header.classList.remove('is-hidden');
    lastY = y; ticking = false;
  };
  window.addEventListener('scroll', () => { if (!ticking) { requestAnimationFrame(updateHeader); ticking = true; } }, { passive: true });
  updateHeader();

  /* ---------- mobile menu ---------- */
  const burger = $('#burger');
  const setMenu = (open) => {
    burger.classList.toggle('is-open', open); menu.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open)); document.body.style.overflow = open ? 'hidden' : '';
    if (open) header.classList.remove('is-hidden');
  };
  burger.addEventListener('click', () => setMenu(!menu.classList.contains('is-open')));
  $$('a', menu).forEach((a) => a.addEventListener('click', () => setMenu(false)));

  /* ---------- scroll spy ---------- */
  const navLinks = $$('.nav a[href^="#"]');
  const sections = navLinks.map((a) => $(a.getAttribute('href'))).filter(Boolean);
  if ('IntersectionObserver' in window && sections.length) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) navLinks.forEach((a) => a.classList.toggle('is-active', a.getAttribute('href') === '#' + e.target.id)); });
    }, { rootMargin: '-35% 0px -55% 0px' });
    sections.forEach((s) => spy.observe(s));
  }

  /* ---------- charts ---------- */
  const C = 2 * Math.PI * 40;
  const runDonut = (svg) => {
    if (svg.dataset.done) return;
    svg.dataset.done = '1';
    $$('.donut__seg', svg).forEach((seg, i) => {
      const pct = parseFloat(seg.dataset.seg) || 0, off = parseFloat(seg.dataset.offset) || 0;
      seg.style.transitionDelay = (i * 80) + 'ms';
      seg.style.strokeDashoffset = String(-(off / 100) * C);
      requestAnimationFrame(() => { seg.style.strokeDasharray = `${(pct / 100) * C} ${C}`; });
    });
  };
  const animateIn = (root) => { root.classList.add('is-in'); $$('.donut svg', root).forEach(runDonut); };
  const targets = $$('[data-reveal], [data-anim]');
  if ('IntersectionObserver' in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { animateIn(e.target); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -5% 0px' });
    targets.forEach((el) => io.observe(el));
  } else {
    targets.forEach(animateIn);
  }

  /* ---------- feature tabs ---------- */
  const tabs = $$('.tab'), panels = $$('.tab-panel');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      if (tab.classList.contains('is-active')) return;
      tabs.forEach((t) => { t.classList.remove('is-active'); t.setAttribute('aria-selected', 'false'); });
      tab.classList.add('is-active'); tab.setAttribute('aria-selected', 'true');
      panels.forEach((p) => {
        const on = p.dataset.panel === tab.dataset.tab;
        p.classList.toggle('is-active', on);
        if (!on) return;
        const vis = $('[data-anim]', p);
        if (!vis) return;
        vis.classList.remove('is-in');
        $$('.donut svg', vis).forEach((s) => { delete s.dataset.done; $$('.donut__seg', s).forEach((seg) => { seg.style.strokeDasharray = '0 999'; }); });
        void vis.offsetWidth;
        setTimeout(() => animateIn(vis), 40);
      });
    });
  });

  /* ---------- smooth anchors ---------- */
  $$('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id.length < 2) { e.preventDefault(); return; }
      const target = $(id);
      if (!target) return;
      e.preventDefault();
      window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 80, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  });
})();
