/* tenders.best — interactions */
(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));

  /* ---------- header: compact after scroll, hidden on scroll down, shown on scroll up ---------- */
  const header = $('#header');
  const menu = $('#mobileMenu');
  let lastY = window.scrollY;
  let ticking = false;
  const updateHeader = () => {
    const y = window.scrollY;
    header.classList.toggle('is-scrolled', y > 24);
    const goingDown = y > lastY + 4;
    const goingUp = y < lastY - 4;
    if (goingDown && y > 160 && !menu.classList.contains('is-open')) header.classList.add('is-hidden');
    else if (goingUp || y < 80) header.classList.remove('is-hidden');
    lastY = y;
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { requestAnimationFrame(updateHeader); ticking = true; }
  }, { passive: true });
  updateHeader();

  /* ---------- mobile menu ---------- */
  const burger = $('#burger');
  const setMenu = (open) => {
    burger.classList.toggle('is-open', open);
    menu.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
    if (open) header.classList.remove('is-hidden');
  };
  burger.addEventListener('click', () => setMenu(!menu.classList.contains('is-open')));
  $$('a', menu).forEach((a) => a.addEventListener('click', () => setMenu(false)));

  /* ---------- active nav link ---------- */
  const navLinks = $$('.nav a[href^="#"]');
  const sections = navLinks.map((a) => $(a.getAttribute('href'))).filter(Boolean);
  if ('IntersectionObserver' in window && sections.length) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          navLinks.forEach((a) => a.classList.toggle('is-active', a.getAttribute('href') === '#' + e.target.id));
        }
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    sections.forEach((s) => spy.observe(s));
  }

  /* ---------- counters ---------- */
  const fmt = (n, decimals) => n.toFixed(decimals).replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const runCounter = (el) => {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    const target = parseFloat(el.dataset.count);
    const decimals = parseInt(el.dataset.decimals || '0', 10);
    if (reduceMotion) { el.textContent = fmt(target, decimals); return; }
    const dur = 1100;
    const start = performance.now();
    const step = (t) => {
      const p = Math.min(1, (t - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = fmt(target * eased, decimals);
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  };

  /* ---------- donuts ---------- */
  const C = 2 * Math.PI * 40;
  const runDonut = (svg) => {
    if (svg.dataset.done) return;
    svg.dataset.done = '1';
    $$('.donut__seg', svg).forEach((seg, i) => {
      const pct = parseFloat(seg.dataset.seg) || 0;
      const off = parseFloat(seg.dataset.offset) || 0;
      seg.style.transitionDelay = (i * 100) + 'ms';
      seg.style.strokeDashoffset = String(-(off / 100) * C);
      requestAnimationFrame(() => { seg.style.strokeDasharray = `${(pct / 100) * C} ${C}`; });
    });
  };

  /* ---------- reveal on scroll (one-shot, subtle) ---------- */
  const animateIn = (root) => {
    root.classList.add('is-in');
    $$('[data-count]', root).forEach(runCounter);
    $$('.donut svg', root).forEach(runDonut);
  };
  const revealTargets = $$('[data-reveal], [data-anim]');
  if ('IntersectionObserver' in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) { animateIn(e.target); io.unobserve(e.target); }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -6% 0px' });
    revealTargets.forEach((el) => io.observe(el));
  } else {
    revealTargets.forEach(animateIn);
  }

  /* ---------- tabs ---------- */
  const tabs = $$('.tab');
  const panels = $$('.showcase__panel');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      if (tab.classList.contains('is-active')) return;
      tabs.forEach((t) => { t.classList.remove('is-active'); t.setAttribute('aria-selected', 'false'); });
      tab.classList.add('is-active');
      tab.setAttribute('aria-selected', 'true');
      panels.forEach((p) => {
        const on = p.dataset.panel === tab.dataset.tab;
        p.classList.toggle('is-active', on);
        if (!on) return;
        const vis = $('[data-anim]', p);
        if (!vis) return;
        vis.classList.remove('is-in');
        $$('.donut svg', vis).forEach((s) => {
          delete s.dataset.done;
          $$('.donut__seg', s).forEach((seg) => { seg.style.strokeDasharray = '0 999'; });
        });
        void vis.offsetWidth;
        setTimeout(() => animateIn(vis), 50);
      });
    });
  });

  /* ---------- testimonial slider (manual) ---------- */
  const slider = $('#testiSlider');
  if (slider) {
    const slides = $$('.testi__slide', slider);
    const chips = $$('.logo-chip');
    const dotsWrap = $('#testiDots');
    let idx = 0;
    slides.forEach((_, i) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Отзыв ' + (i + 1));
      if (i === 0) b.classList.add('is-active');
      b.addEventListener('click', () => go(i));
      dotsWrap.appendChild(b);
    });
    const dots = $$('button', dotsWrap);
    const go = (n) => {
      const next = (n + slides.length) % slides.length;
      if (next === idx) return;
      const cur = slides[idx];
      cur.classList.add('is-leaving');
      cur.classList.remove('is-active');
      setTimeout(() => cur.classList.remove('is-leaving'), 500);
      slides[next].classList.add('is-active');
      dots.forEach((d, i) => d.classList.toggle('is-active', i === next));
      const company = parseInt(slides[next].dataset.company || '-1', 10);
      chips.forEach((c, i) => c.classList.toggle('is-active', i === company));
      idx = next;
    };
    $$('.testi__arrow', slider).forEach((b) => b.addEventListener('click', () => go(idx + parseInt(b.dataset.dir, 10))));
  }

  /* ---------- smooth anchors ---------- */
  $$('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const id = a.getAttribute('href');
      if (id.length < 2) { e.preventDefault(); return; }
      const target = $(id);
      if (!target) return;
      e.preventDefault();
      const y = target.getBoundingClientRect().top + window.scrollY - 24;
      window.scrollTo({ top: y, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  });
})();
