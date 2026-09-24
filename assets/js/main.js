/* tenders.best — interactions */
(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));

  /* ---------- sticky header ---------- */
  const header = $('#header');
  let lastScrolled = false;
  const onScroll = () => {
    const scrolled = window.scrollY > 24;
    if (scrolled !== lastScrolled) {
      header.classList.toggle('is-scrolled', scrolled);
      lastScrolled = scrolled;
    }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* ---------- mobile menu ---------- */
  const burger = $('#burger');
  const menu = $('#mobileMenu');
  const closeMenu = () => {
    burger.classList.remove('is-open');
    menu.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };
  burger.addEventListener('click', () => {
    const open = !menu.classList.contains('is-open');
    burger.classList.toggle('is-open', open);
    menu.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  });
  $$('a', menu).forEach((a) => a.addEventListener('click', closeMenu));

  /* ---------- active nav link on scroll ---------- */
  const navLinks = $$('.nav a');
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
  const fmt = (n, decimals) => {
    const s = n.toFixed(decimals);
    return s.replace('.', ',').replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  };
  const runCounter = (el) => {
    if (el.dataset.done) return;
    el.dataset.done = '1';
    const target = parseFloat(el.dataset.count);
    const decimals = parseInt(el.dataset.decimals || '0', 10);
    if (reduceMotion) { el.textContent = fmt(target, decimals); return; }
    const dur = 1400;
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
  const runDonut = (svg) => {
    if (svg.dataset.done) return;
    svg.dataset.done = '1';
    const C = 2 * Math.PI * 40; // r = 40
    $$('.donut__seg', svg).forEach((seg, i) => {
      const pct = parseFloat(seg.dataset.seg) || 0;
      const off = parseFloat(seg.dataset.offset) || 0;
      seg.style.transitionDelay = (i * 120) + 'ms';
      seg.style.strokeDashoffset = String(-(off / 100) * C);
      requestAnimationFrame(() => {
        seg.style.strokeDasharray = `${(pct / 100) * C} ${C}`;
      });
    });
  };

  /* ---------- reveal on scroll ---------- */
  const animateIn = (root) => {
    root.classList.add('is-in');
    $$('[data-count]', root).forEach(runCounter);
    if (root.matches('[data-count]')) runCounter(root);
    $$('.donut svg', root).forEach(runDonut);
  };

  const revealTargets = $$('[data-reveal], [data-anim]');
  if ('IntersectionObserver' in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          animateIn(e.target);
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -8% 0px' });
    revealTargets.forEach((el) => io.observe(el));
  } else {
    revealTargets.forEach(animateIn);
  }

  /* ---------- hero parallax ---------- */
  const heroVisual = $('#heroVisual');
  if (heroVisual && !reduceMotion && window.matchMedia('(pointer: fine)').matches) {
    const layers = $$('[data-parallax]', heroVisual);
    let tx = 0, ty = 0, cx = 0, cy = 0, raf = null;
    const tick = () => {
      cx += (tx - cx) * 0.08;
      cy += (ty - cy) * 0.08;
      layers.forEach((l) => {
        const d = parseFloat(l.dataset.parallax) || 0.5;
        l.style.setProperty('--px', (cx * d * 18) + 'px');
        l.style.setProperty('--py', (cy * d * 18) + 'px');
        const base = l.classList.contains('hero__dash') ? 'rotateY(' + (-9 + cx * 3) + 'deg) rotateX(' + (5 - cy * 3) + 'deg) rotateZ(-1deg) ' : '';
        l.style.transform = `translate3d(var(--px), var(--py), 0) ${base}`;
      });
      if (Math.abs(tx - cx) > 0.001 || Math.abs(ty - cy) > 0.001) raf = requestAnimationFrame(tick); else raf = null;
    };
    const hero = $('.hero');
    hero.addEventListener('mousemove', (e) => {
      const r = hero.getBoundingClientRect();
      tx = ((e.clientX - r.left) / r.width - 0.5) * 2;
      ty = ((e.clientY - r.top) / r.height - 0.5) * 2;
      if (!raf) raf = requestAnimationFrame(tick);
    });
    hero.addEventListener('mouseleave', () => { tx = 0; ty = 0; if (!raf) raf = requestAnimationFrame(tick); });
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
        if (on) {
          const vis = $('[data-anim]', p);
          if (vis) {
            vis.classList.remove('is-in');
            $$('.donut svg', vis).forEach((s) => { delete s.dataset.done; $$('.donut__seg', s).forEach((seg) => { seg.style.strokeDasharray = '0 999'; }); });
            // restart chart animations
            void vis.offsetWidth;
            setTimeout(() => animateIn(vis), 60);
          }
        }
      });
    });
  });

  /* ---------- testimonial slider ---------- */
  const slider = $('#testiSlider');
  if (slider) {
    const slides = $$('.testi__slide', slider);
    const dotsWrap = $('#testiDots');
    let idx = 0, timer = null;
    slides.forEach((_, i) => {
      const b = document.createElement('button');
      b.setAttribute('aria-label', 'Отзыв ' + (i + 1));
      if (i === 0) b.classList.add('is-active');
      b.addEventListener('click', () => go(i, true));
      dotsWrap.appendChild(b);
    });
    const dots = $$('button', dotsWrap);
    const go = (n, manual) => {
      const next = (n + slides.length) % slides.length;
      if (next === idx) return;
      const cur = slides[idx];
      cur.classList.add('is-leaving');
      cur.classList.remove('is-active');
      setTimeout(() => cur.classList.remove('is-leaving'), 700);
      slides[next].classList.add('is-active');
      dots.forEach((d, i) => d.classList.toggle('is-active', i === next));
      const company = parseInt(slides[next].dataset.company || '-1', 10);
      $$('.logo-chip').forEach((c, i) => c.classList.toggle('is-active', i === company));
      idx = next;
      if (manual) restart();
    };
    const restart = () => {
      clearInterval(timer);
      if (!reduceMotion) timer = setInterval(() => go(idx + 1), 6500);
    };
    $$('.testi__arrow', slider).forEach((b) => b.addEventListener('click', () => go(idx + parseInt(b.dataset.dir, 10), true)));
    slider.addEventListener('mouseenter', () => clearInterval(timer));
    slider.addEventListener('mouseleave', restart);
    restart();
  }

  /* ---------- smooth anchors (offset for fixed header) ---------- */
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
