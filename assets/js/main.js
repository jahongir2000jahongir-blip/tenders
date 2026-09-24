/* tenders.best — landing page */
(function () {
  'use strict';
  const { $, $$ } = window.TBUI;

  /* ---------- i18n ---------- */
  const original = new Map();
  const applyLang = (code) => {
    if (!['ru', 'en', 'tj'].includes(code)) code = 'ru';
    const dict = (window.TB_I18N || {})[code] || {};
    $$('[data-i]').forEach((el) => {
      if (!original.has(el)) original.set(el, el.innerHTML);
      const v = dict[el.dataset.i];
      el.innerHTML = code === 'ru' || v == null ? original.get(el) : v;
    });
    document.documentElement.lang = code === 'tj' ? 'tg' : code;
    try { localStorage.setItem('tb_lang', code); } catch (e) { /* ignore */ }
  };
  const sync = window.TBUI.lang(applyLang);
  let saved = 'ru';
  try { saved = localStorage.getItem('tb_lang') || 'ru'; } catch (e) { /* ignore */ }
  applyLang(saved); sync(saved);

  window.TBUI.header();

  /* ---------- scroll spy ---------- */
  const navLinks = $$('.nav a[href^="#"]');
  const sections = navLinks.map((a) => $(a.getAttribute('href'))).filter(Boolean);
  if ('IntersectionObserver' in window && sections.length) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) navLinks.forEach((a) => a.classList.toggle('is-active', a.getAttribute('href') === '#' + e.target.id)); });
    }, { rootMargin: '-35% 0px -55% 0px' });
    sections.forEach((s) => spy.observe(s));
  }

  /* ---------- charts + reveal ---------- */
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
  window.TBUI.reveal(animateIn);

  /* ---------- feature tabs ---------- */
  const tabs = $$('.tab'), panels = $$('.tab-panel');
  const activate = (tab) => {
    if (tab.classList.contains('is-active')) return;
    tabs.forEach((t) => { t.classList.remove('is-active'); t.setAttribute('aria-selected', 'false'); t.tabIndex = -1; });
    tab.classList.add('is-active'); tab.setAttribute('aria-selected', 'true'); tab.tabIndex = 0;
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
  };
  tabs.forEach((tab, i) => {
    tab.tabIndex = tab.classList.contains('is-active') ? 0 : -1;
    tab.addEventListener('click', () => activate(tab));
    tab.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
      e.preventDefault();
      const next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
      next.focus(); activate(next);
    });
  });

  /* ---------- smooth anchors ---------- */
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  $$('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id.length < 2) { e.preventDefault(); return; }
      const target = $(id);
      if (!target) return;
      e.preventDefault();
      window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - 84, behavior: reduce ? 'auto' : 'smooth' });
    });
  });
})();
