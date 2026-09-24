/* tenders.best — catalogue page */
(function () {
  'use strict';
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => Array.from(c.querySelectorAll(s));

  /* ---------- i18n ---------- */
  const T = {
    ru: {
      nav_tenders: 'Каталог тендеров', nav_platform: 'Возможности', nav_how: 'Как проходит работа', nav_sources: 'Источники', nav_home: 'Главная', login: 'Войти', buy: 'Купить подписку', done: 'Готово',
      eyebrow: 'Каталог тендеров', h1: 'Каталог закупок пятнадцати стран',
      lead: 'Центральная Азия, Россия, Беларусь, Украина, Молдова, Азербайджан и страны ЕС. Фильтры по отрасли, бюджету и сроку подачи, суммы в долларах и местной валюте, ссылка на оригинал каждого объявления.',
      find: 'Найти', search_ph: 'Например: школьная мебель, трансформатор, ремонт дороги',
      updated: 'Обновлено', next: 'следующее обновление', never: 'сбор ещё не запускался', demo: 'Демо-данные',
      open_n: 'открытых', filters: 'Фильтры', reset: 'Сбросить', country: 'Страна', category: 'Отрасль', budget: 'Бюджет, USD',
      from: 'от', to: 'до', deadline: 'Срок подачи', any: 'Любой', d7: 'Закрывается за 7 дней', d30: 'В ближайшие 30 дней',
      only_open: 'Только открытые', favs_only: 'Только избранное', cur_local: 'Местная',
      s_new: 'Сначала новые', s_dead: 'Ближайший срок подачи', s_bud_d: 'Бюджет: больше', s_bud_a: 'Бюджет: меньше',
      found: 'Найдено', more: 'Показать ещё', empty: 'По этим условиям тендеров нет. Уберите часть фильтров или измените запрос.',
      today: 'закрывается сегодня', closed: 'приём завершён', left: 'осталось', days: ['день', 'дня', 'дней'], tenders: ['тендер', 'тендера', 'тендеров'],
      no_deadline: 'срок не указан', no_sum: 'сумма не указана', published: 'Опубликован', deadline_at: 'Приём заявок до', customer: 'Заказчик',
      location: 'Место поставки', method: 'Способ закупки', source: 'Источник', number: 'Номер', open_portal: 'Открыть на портале',
      fav_add: 'В избранное', fav_rm: 'Убрать из избранного', copy: 'Скопировать номер', copied: 'Номер скопирован', demo_note: 'Демонстрационная запись, ссылки на портал нет',
      sub_eyebrow: 'Уведомления', sub_h: 'Новые тендеры на почту', sub_p: 'Выберите страны и ключевые слова. Как только на порталах появится подходящий тендер, пришлём письмо.',
      email: 'Электронная почта', keywords: 'Ключевые слова через запятую', sub_btn: 'Подписаться', sub_ok: 'Подписка сохранена.', sub_err: 'Укажите корректный адрес почты.', sub_err2: 'Выберите хотя бы одну страну.',
      src_eyebrow: 'Источники', src_h: 'Откуда берутся тендеры', src_p: 'Объявления собираются с официальных порталов каждые 3 часа. Дубликаты одного тендера из разных источников не показываются.',
      src_country: 'Страна', src_portal: 'Источник', src_note: 'Кто публикует', src_status: 'Последнее обновление', st_ok: 'обновлено', st_err: 'ошибка при сборе', st_none: 'ещё не собирался',
    },
    en: {
      nav_tenders: 'Tender catalogue', nav_platform: 'Features', nav_how: 'How it works', nav_sources: 'Sources', nav_home: 'Home', login: 'Sign in', buy: 'Buy subscription', done: 'Done',
      eyebrow: 'Tender catalogue', h1: 'Procurement catalogue of fifteen countries',
      lead: 'Central Asia, Russia, Belarus, Ukraine, Moldova, Azerbaijan and EU countries. Filters by sector, budget and deadline, amounts in USD and local currency, a link to the original of every notice.',
      find: 'Search', search_ph: 'e.g. school furniture, transformer, road repair',
      updated: 'Updated', next: 'next update', never: 'not collected yet', demo: 'Demo data',
      open_n: 'open', filters: 'Filters', reset: 'Reset', country: 'Country', category: 'Sector', budget: 'Budget, USD',
      from: 'from', to: 'to', deadline: 'Deadline', any: 'Any', d7: 'Closes within 7 days', d30: 'Within 30 days',
      only_open: 'Open only', favs_only: 'Saved only', cur_local: 'Local',
      s_new: 'Newest first', s_dead: 'Closing soonest', s_bud_d: 'Budget: high to low', s_bud_a: 'Budget: low to high',
      found: 'Found', more: 'Show more', empty: 'No tenders match these conditions. Remove some filters or change the search.',
      today: 'closes today', closed: 'closed', left: 'left', days: ['day', 'days', 'days'], tenders: ['tender', 'tenders', 'tenders'],
      no_deadline: 'no deadline', no_sum: 'amount not stated', published: 'Published', deadline_at: 'Bids due', customer: 'Buyer',
      location: 'Delivery location', method: 'Procedure', source: 'Source', number: 'Number', open_portal: 'Open on portal',
      fav_add: 'Save', fav_rm: 'Remove from saved', copy: 'Copy number', copied: 'Number copied', demo_note: 'Demo record, no portal link',
      sub_eyebrow: 'Alerts', sub_h: 'New tenders by email', sub_p: 'Pick countries and keywords. When a matching tender appears on a portal, we send you an email.',
      email: 'Email', keywords: 'Keywords, comma-separated', sub_btn: 'Subscribe', sub_ok: 'Subscription saved.', sub_err: 'Enter a valid email address.', sub_err2: 'Pick at least one country.',
      src_eyebrow: 'Sources', src_h: 'Where tenders come from', src_p: 'Notices are collected from official portals every 3 hours. Duplicates of one tender from different sources are hidden.',
      src_country: 'Country', src_portal: 'Source', src_note: 'Publisher', src_status: 'Last update', st_ok: 'updated', st_err: 'collection error', st_none: 'not collected yet',
    },
  tj: {
      nav_tenders: 'Феҳристи тендерҳо', nav_platform: 'Имкониятҳо', nav_how: 'Ҷараёни кор', nav_sources: 'Манбаъҳо', nav_home: 'Асосӣ', login: 'Ворид шудан', buy: 'Харидани обуна', done: 'Тайёр',
      eyebrow: 'Феҳристи тендерҳо', h1: 'Феҳристи хариди понздаҳ кишвар',
      lead: 'Осиёи Марказӣ, Русия, Беларус, Украина, Молдова, Озарбойҷон ва кишварҳои ИА. Филтр аз рӯи соҳа, буҷет ва мӯҳлати пешниҳод, маблағҳо бо доллар ва асъори маҳаллӣ, пайванд ба асли ҳар эълон.',
      find: 'Ҷустуҷӯ', search_ph: 'Масалан: мебели мактабӣ, трансформатор, таъмири роҳ',
      updated: 'Навсозӣ шуд', next: 'навсозии оянда', never: 'ҷамъоварӣ ҳанӯз оғоз нашудааст', demo: 'Маълумоти намунавӣ',
      open_n: 'кушода', filters: 'Филтрҳо', reset: 'Тоза кардан', country: 'Кишвар', category: 'Соҳа', budget: 'Буҷет, USD',
      from: 'аз', to: 'то', deadline: 'Мӯҳлати пешниҳод', any: 'Ҳар кадом', d7: 'Дар 7 рӯз баста мешавад', d30: 'Дар 30 рӯзи наздик',
      only_open: 'Танҳо кушода', favs_only: 'Танҳо интихобшуда', cur_local: 'Маҳаллӣ',
      s_new: 'Аввал навҳо', s_dead: 'Мӯҳлати наздиктарин', s_bud_d: 'Буҷет: бештар', s_bud_a: 'Буҷет: камтар',
      found: 'Ёфт шуд', more: 'Боз нишон додан', empty: 'Аз рӯи ин шартҳо тендер нест. Қисми филтрҳоро бардоред ё дархостро тағйир диҳед.',
      today: 'имрӯз баста мешавад', closed: 'қабул анҷом ёфт', left: 'монд', days: ['рӯз', 'рӯз', 'рӯз'], tenders: ['тендер', 'тендер', 'тендер'],
      no_deadline: 'мӯҳлат нишон дода нашудааст', no_sum: 'маблағ нишон дода нашудааст', published: 'Нашр шуд', deadline_at: 'Қабули дархостҳо то', customer: 'Фармоишгар',
      location: 'Ҷои таҳвил', method: 'Усули харид', source: 'Манбаъ', number: 'Рақам', open_portal: 'Кушодан дар портал',
      fav_add: 'Ба интихобшуда', fav_rm: 'Аз интихобшуда бардоштан', copy: 'Нусхаи рақам', copied: 'Рақам нусхабардорӣ шуд', demo_note: 'Сабти намунавӣ, пайванд ба портал нест',
      sub_eyebrow: 'Огоҳиномаҳо', sub_h: 'Тендерҳои нав ба почта', sub_p: 'Кишварҳо ва калидвожаҳоро интихоб кунед. Ҳамин ки дар порталҳо тендери мувофиқ пайдо шавад, мактуб мефиристем.',
      email: 'Почтаи электронӣ', keywords: 'Калидвожаҳо бо вергул', sub_btn: 'Обуна шудан', sub_ok: 'Обуна захира шуд.', sub_err: 'Суроғаи дурусти почтаро нависед.', sub_err2: 'Ақаллан як кишварро интихоб кунед.',
      src_eyebrow: 'Манбаъҳо', src_h: 'Тендерҳо аз куҷо меоянд', src_p: 'Эълонҳо ҳар 3 соат аз порталҳои расмӣ ҷамъ оварда мешаванд. Такрори як тендер аз манбаъҳои гуногун нишон дода намешавад.',
      src_country: 'Кишвар', src_portal: 'Манбаъ', src_note: 'Кӣ нашр мекунад', src_status: 'Навсозии охирин', st_ok: 'навсозӣ шуд', st_err: 'хатои ҷамъоварӣ', st_none: 'ҳанӯз ҷамъ нашудааст',
    },
  };
  const state = {
    lang: localStorage.getItem('tb_lang') || 'ru', cur: localStorage.getItem('tb_cur') || 'usd',
    q: '', countries: new Set(), cats: new Set(), min: '', max: '', dl: '', open: true, fav: false, sort: 'new',
    page: 1, total: 0, items: [], meta: null, stats: null, sources: [],
    favs: new Set(JSON.parse(localStorage.getItem('tb_favs') || '[]')),
  };
  const t = (k) => (T[state.lang] && T[state.lang][k] != null ? T[state.lang][k] : T.ru[k]);
  const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const plural = (n, forms) => { n = Math.abs(n) % 100; const n1 = n % 10; if (state.lang === 'en') return n === 1 ? forms[0] : forms[1]; if (state.lang === 'tj') return forms[0]; if (n > 10 && n < 20) return forms[2]; if (n1 > 1 && n1 < 5) return forms[1]; if (n1 === 1) return forms[0]; return forms[2]; };
  const fmtNum = (n) => Math.round(n).toLocaleString(state.lang === 'en' ? 'en-US' : 'ru-RU');
  const fmtDate = (s) => s ? new Date(s).toLocaleDateString(state.lang === 'en' ? 'en-GB' : 'ru-RU', { day: '2-digit', month: 'short', year: 'numeric' }) : '—';
  const fmtDt = (s) => s ? new Date(s).toLocaleString(state.lang === 'en' ? 'en-GB' : 'ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—';
  const daysLeft = (s) => s ? Math.ceil((new Date(s) - Date.now()) / 86400000) : null;
  const toast = (m) => { const el = $('#toast'); el.textContent = m; el.classList.add('show'); setTimeout(() => el.classList.remove('show'), 2400); };

  function applyLang() {
    document.documentElement.lang = state.lang === 'tj' ? 'tg' : state.lang;
    $$('[data-i]').forEach((el) => { const v = t(el.dataset.i); if (v == null) return; if (el.tagName === 'OPTION' || !el.querySelector('svg')) el.textContent = v; else el.firstChild.nodeValue = v; });
    $$('[data-ph]').forEach((el) => { el.placeholder = t(el.dataset.ph); });
    $('#q').placeholder = t('search_ph');
    $$('[data-lang]').forEach((b) => { b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang)); b.setAttribute('aria-current', String(b.dataset.lang === state.lang)); });
    $$('[data-lang-label]').forEach((el) => { el.textContent = state.lang.toUpperCase(); });
    $$('[data-flag]').forEach((el) => { el.className = 'flag flag--' + state.lang; });
    $$('[data-cur]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.cur === state.cur)));
  }

  /* ---------- rendering ---------- */
  function money(it) {
    if (state.cur === 'usd') {
      if (it.amount_usd != null) return { main: '$' + fmtNum(it.amount_usd), sub: it.amount != null && it.currency !== 'USD' ? `${fmtNum(it.amount)} ${it.currency}` : '' };
      if (it.amount != null) return { main: `${fmtNum(it.amount)} ${esc(it.currency || '')}`, sub: '' };
      return { main: '—', sub: t('no_sum') };
    }
    if (it.amount != null) return { main: `${fmtNum(it.amount)} ${esc(it.currency || '')}`, sub: it.amount_usd != null ? '≈ $' + fmtNum(it.amount_usd) : '' };
    return { main: '—', sub: t('no_sum') };
  }
  function deadlineTag(it) {
    if (it.status === 'closed') return `<span class="tag tag--closed">${t('closed')}</span>`;
    const d = daysLeft(it.deadline_at);
    if (d == null) return '';
    if (d <= 0) return `<span class="tag tag--hot">${t('today')}</span>`;
    if (d <= 7) return `<span class="tag tag--hot">${d} ${plural(d, t('days'))} ${t('left')}</span>`;
    if (d <= 30) return `<span class="tag tag--soon">${d} ${plural(d, t('days'))} ${t('left')}</span>`;
    return '';
  }
  function card(it) {
    const m = money(it);
    return `<article class="card ${it.status === 'closed' ? 'card--closed' : ''}" data-id="${it.id}" tabindex="0">
      <button class="fav ${state.favs.has(it.id) ? 'is-on' : ''}" type="button" data-fav="${it.id}" aria-label="${t('fav_add')}"><svg class="icon"><use href="#i-star"/></svg></button>
      <div>
        <div class="card__top"><span class="tag tag--country"><i>${it.country}</i>${esc(it.country_name)}</span><span class="tag tag--cat">${esc(it.category_name)}</span>${deadlineTag(it)}${it.is_demo ? `<span class="tag tag--demo">${t('demo')}</span>` : ''}</div>
        <h3 class="card__title">${esc(it.title)}</h3>
        <div class="card__meta">
          ${it.customer ? `<span><svg class="icon"><use href="#i-building"/></svg>${esc(it.customer)}</span>` : ''}
          ${it.region ? `<span><svg class="icon"><use href="#i-pin"/></svg>${esc(it.region)}</span>` : ''}
          <span><svg class="icon"><use href="#i-calendar"/></svg>${t('published')} ${fmtDate(it.published_at || it.first_seen_at)}</span>
        </div>
      </div>
      <div class="card__side">
        <div class="card__sum">${m.main}<small>${m.sub}</small></div>
        <div class="card__deadline">${t('deadline_at')} <b>${it.deadline_at ? fmtDate(it.deadline_at) : t('no_deadline')}</b></div>
        <span class="tag">${esc(it.source_name)}</span>
      </div>
    </article>`;
  }
  function renderList(append) {
    const list = $('#list');
    let items = state.items;
    if (state.fav) items = items.filter((i) => state.favs.has(i.id));
    if (!append) list.innerHTML = '';
    if (!items.length && !append) { list.innerHTML = `<div class="empty">${t('empty')}</div>`; }
    else list.insertAdjacentHTML('beforeend', items.slice(append ? -state.lastBatch : 0).map(card).join(''));
    const shown = state.items.length;
    $('#count').innerHTML = `${t('found')} <b>${fmtNum(state.total)}</b> ${plural(state.total, t('tenders'))}`;
    $('#more').hidden = shown >= state.total;
  }
  function renderCountries() {
    const s = state.stats; if (!s) return;
    $('#countryStrip').innerHTML = s.countries.map((c) => `<button type="button" class="cty" data-country="${c.code}" aria-pressed="${state.countries.has(c.code)}">
      <span class="code">${c.code}</span><span class="name">${esc(c[state.lang] || c.ru)}</span><span class="num">${fmtNum(c.open)}</span><span class="sub">${t('open_n')}${c.usd ? ' · $' + fmtNum(c.usd / 1e6 * 10) / 10 + 'M' : ''}</span></button>`).join('');
    $('#fCountries').innerHTML = s.countries.map((c) => `<button type="button" data-fc="${c.code}" aria-pressed="${state.countries.has(c.code)}" title="${esc(c[state.lang] || c.ru)}">${c.code}</button>`).join('');
    $('#subCountries').innerHTML = s.countries.map((c) => `<button type="button" data-sc="${c.code}" aria-pressed="false">${c.code}</button>`).join('');
    const cats = state.meta.categories;
    $('#fCats').innerHTML = Object.keys(cats).map((k) => `<label class="fcheck"><input type="checkbox" data-cat="${k}" ${state.cats.has(k) ? 'checked' : ''}><span>${esc(cats[k][state.lang] || cats[k].ru)}</span><span class="n">${s.categories[k] || 0}</span></label>`).join('');
    const meta = [];
    if (s.last_collect_at) meta.push(`<span>${t('updated')}: <b>${fmtDt(s.last_collect_at)}</b></span>`); else meta.push(`<span>${t('never')}</span>`);
    if (s.next_collect_at) meta.push(`<span>${t('next')}: <b>${fmtDt(s.next_collect_at)}</b></span>`);
    if (s.has_demo) meta.push(`<span class="demo">${t('demo')}</span>`);
    $('#meta').innerHTML = meta.join('');
  }
  function renderSources() {
    const rows = state.sources.map((s) => {
      const st = s.last_status === 'ok' ? `<span class="st st--ok">${t('st_ok')} ${fmtDt(s.last_run_at)}</span>` : s.last_status === 'error' ? `<span class="st st--err">${t('st_err')}</span>` : `<span class="st st--none">${t('st_none')}</span>`;
      return `<tr><td class="c"><i>${s.country}</i>${esc(s['country_' + state.lang] || s.country_ru)}</td><td><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.name)}</a></td><td>${esc(s['publisher_' + state.lang] || s.publisher_ru)}</td><td>${st}</td></tr>`;
    });
    $('#srcTable').innerHTML = `<tr><th>${t('src_country')}</th><th>${t('src_portal')}</th><th>${t('src_note')}</th><th>${t('src_status')}</th></tr>` + rows.join('');
  }

  /* ---------- data ---------- */
  function params() {
    const p = new URLSearchParams();
    if (state.q) p.set('q', state.q);
    state.countries.forEach((c) => p.append('country', c));
    state.cats.forEach((c) => p.append('category', c));
    if (state.min !== '') p.set('min_usd', state.min);
    if (state.max !== '') p.set('max_usd', state.max);
    if (state.dl) p.set('deadline', state.dl);
    p.set('status', state.open ? 'open' : 'all');
    p.set('sort', state.sort); p.set('page', state.page); p.set('per_page', 24); p.set('lang', state.lang === 'en' ? 'en' : 'ru');
    return p.toString();
  }
  async function load(append = false) {
    if (!append) { state.page = 1; $('#list').innerHTML = '<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>'; }
    const r = await fetch('/api/tenders?' + params());
    const d = await r.json();
    state.total = d.total; state.lastBatch = d.items.length;
    state.items = append ? state.items.concat(d.items) : d.items;
    renderList(append);
    history.replaceState(null, '', state.q || state.countries.size ? '?' + params().replace(/&page=\d+|&per_page=\d+|&lang=\w+/g, '') : location.pathname);
  }
  async function loadMeta() {
    const [meta, stats, sources] = await Promise.all([fetch('/api/meta').then((r) => r.json()), fetch('/api/stats').then((r) => r.json()), fetch('/api/sources').then((r) => r.json())]);
    state.meta = meta; state.stats = stats; state.sources = sources;
    renderCountries(); renderSources();
  }

  /* ---------- drawer ---------- */
  function openDrawer(id) {
    const it = state.items.find((x) => x.id === id); if (!it) return;
    const m = money(it);
    $('#dId').textContent = `${it.source_name} · ${it.external_id}`;
    $('#dBody').innerHTML = `
      <div class="card__top"><span class="tag tag--country"><i>${it.country}</i>${esc(it.country_name)}</span><span class="tag tag--cat">${esc(it.category_name)}</span>${deadlineTag(it)}${it.is_demo ? `<span class="tag tag--demo">${t('demo')}</span>` : ''}</div>
      <h2>${esc(it.title)}</h2>
      <dl class="dl">
        <dt>${t('customer')}</dt><dd>${esc(it.customer || '—')}</dd>
        <dt>${t('location')}</dt><dd>${esc(it.region || '—')}</dd>
        <dt>${t('method')}</dt><dd>${esc(it.method || '—')}</dd>
        <dt>${t('budget').split(',')[0]}</dt><dd>${m.main}${m.sub ? ' <span style="color:var(--muted)">(' + m.sub + ')</span>' : ''}</dd>
        <dt>${t('published')}</dt><dd>${fmtDate(it.published_at || it.first_seen_at)}</dd>
        <dt>${t('deadline_at')}</dt><dd>${it.deadline_at ? fmtDt(it.deadline_at) : t('no_deadline')}</dd>
        <dt>${t('source')}</dt><dd>${esc(it.source_name)}</dd>
        <dt>${t('number')}</dt><dd style="font-family:ui-monospace,Menlo,monospace">${esc(it.external_id)}</dd>
      </dl>
      ${it.description ? `<p class="desc">${esc(it.description)}</p>` : ''}`;
    $('#dActions').innerHTML = `
      ${it.url ? `<a class="btn btn--primary btn--sm" href="${esc(it.url)}" target="_blank" rel="noopener">${t('open_portal')} <svg class="icon icon--arrow"><use href="#i-arrow-up-right"/></svg></a>` : `<span class="formmsg">${t('demo_note')}</span>`}
      <button class="btn btn--ghost btn--sm" type="button" data-fav="${it.id}">${state.favs.has(it.id) ? t('fav_rm') : t('fav_add')}</button>
      <button class="btn btn--ghost btn--sm" type="button" data-copy="${esc(it.external_id)}"><svg class="icon"><use href="#i-copy"/></svg>${t('copy')}</button>`;
    $('#drawer').classList.add('is-open'); $('#scrim').classList.add('is-open'); document.body.style.overflow = 'hidden';
  }
  function closeDrawer() { $('#drawer').classList.remove('is-open'); $('#scrim').classList.remove('is-open'); document.body.style.overflow = ''; }

  /* ---------- events ---------- */
  document.addEventListener('click', (e) => {
    const b = e.target.closest('button, a'); if (!b) return;
    if (b.dataset.lang) { state.lang = b.dataset.lang; localStorage.setItem('tb_lang', state.lang); applyLang(); renderCountries(); renderSources(); load(); $('#lang')?.classList.remove('is-open'); return; }
    if (b.classList.contains('lang__btn')) { const l = $('#lang'); const open = !l.classList.contains('is-open'); l.classList.toggle('is-open', open); b.setAttribute('aria-expanded', String(open)); return; }
    if (b.dataset.cur) { state.cur = b.dataset.cur; localStorage.setItem('tb_cur', state.cur); applyLang(); renderList(false); return; }
    if (b.dataset.country || b.dataset.fc) { const c = b.dataset.country || b.dataset.fc; state.countries.has(c) ? state.countries.delete(c) : state.countries.add(c); renderCountries(); load(); return; }
    if (b.dataset.sc) { b.setAttribute('aria-pressed', String(b.getAttribute('aria-pressed') !== 'true')); return; }
    if (b.dataset.fav) { const id = +b.dataset.fav; state.favs.has(id) ? state.favs.delete(id) : state.favs.add(id); localStorage.setItem('tb_favs', JSON.stringify([...state.favs])); $$(`[data-fav="${id}"]`).forEach((x) => { if (x.classList.contains('fav')) x.classList.toggle('is-on', state.favs.has(id)); else x.textContent = state.favs.has(id) ? t('fav_rm') : t('fav_add'); }); if (state.fav) renderList(false); e.stopPropagation(); return; }
    if (b.dataset.copy) { navigator.clipboard?.writeText(b.dataset.copy).then(() => toast(t('copied'))); return; }
    if (b.id === 'more') { state.page++; load(true); return; }
    if (b.id === 'reset') { state.q = ''; $('#q').value = ''; state.countries.clear(); state.cats.clear(); state.min = state.max = ''; $('#minUsd').value = $('#maxUsd').value = ''; state.dl = ''; $('input[name=dl][value=""]').checked = true; state.open = true; $('#onlyOpen').checked = true; state.fav = false; $('#onlyFav').checked = false; renderCountries(); load(); return; }
    if (b.id === 'filtersToggle') { $('#filters').classList.toggle('is-open'); return; }
    if (b.id === 'filtersClose') { $('#filters').classList.remove('is-open'); return; }
    if (b.id === 'dClose') { closeDrawer(); return; }
    if (b.id === 'burger') { const open = !$('#mobileMenu').classList.contains('is-open'); b.classList.toggle('is-open', open); $('#mobileMenu').classList.toggle('is-open', open); document.body.style.overflow = open ? 'hidden' : ''; return; }
  });
  $('#list').addEventListener('click', (e) => { if (e.target.closest('.fav')) return; const c = e.target.closest('.card'); if (c) openDrawer(+c.dataset.id); });
  $('#list').addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.classList.contains('card')) openDrawer(+e.target.dataset.id); });
  $('#scrim').addEventListener('click', closeDrawer);
  document.addEventListener('click', (e) => { const l = $('#lang'); if (l && !l.contains(e.target)) l.classList.remove('is-open'); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { closeDrawer(); $('#filters').classList.remove('is-open'); } });
  $('#searchForm').addEventListener('submit', (e) => { e.preventDefault(); state.q = $('#q').value.trim(); load(); $('#tenders').scrollIntoView({ behavior: 'smooth', block: 'start' }); });
  $('#fCats').addEventListener('change', (e) => { const k = e.target.dataset.cat; if (!k) return; e.target.checked ? state.cats.add(k) : state.cats.delete(k); load(); });
  let rt; const rangeChange = () => { clearTimeout(rt); rt = setTimeout(() => { state.min = $('#minUsd').value; state.max = $('#maxUsd').value; load(); }, 400); };
  $('#minUsd').addEventListener('input', rangeChange); $('#maxUsd').addEventListener('input', rangeChange);
  $$('input[name=dl]').forEach((r) => r.addEventListener('change', () => { state.dl = r.value; load(); }));
  $('#onlyOpen').addEventListener('change', (e) => { state.open = e.target.checked; load(); });
  $('#onlyFav').addEventListener('change', (e) => { state.fav = e.target.checked; renderList(false); });
  $('#sort').addEventListener('change', (e) => { state.sort = e.target.value; load(); });
  $('#subForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const msg = $('#subMsg'); msg.className = 'formmsg';
    const email = $('#subEmail').value.trim();
    const countries = $$('#subCountries button[aria-pressed="true"]').map((b) => b.dataset.sc);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { msg.textContent = t('sub_err'); msg.classList.add('err'); return; }
    if (!countries.length) { msg.textContent = t('sub_err2'); msg.classList.add('err'); return; }
    const r = await fetch('/api/subscribe', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, countries, keywords: $('#subKw').value }) });
    if (r.ok) { msg.textContent = t('sub_ok'); msg.classList.add('ok'); e.target.reset(); $$('#subCountries button').forEach((b) => b.setAttribute('aria-pressed', 'false')); }
    else { msg.textContent = t('sub_err'); msg.classList.add('err'); }
  });

  /* header: hide on scroll down */
  const header = $('#header'); let lastY = window.scrollY;
  window.addEventListener('scroll', () => { const y = window.scrollY; header.classList.toggle('is-scrolled', y > 24); if (y > lastY + 4 && y > 160) header.classList.add('is-hidden'); else if (y < lastY - 4 || y < 80) header.classList.remove('is-hidden'); lastY = y; }, { passive: true });

  /* init from URL */
  const u = new URLSearchParams(location.search);
  if (u.get('q')) { state.q = u.get('q'); $('#q').value = state.q; }
  u.getAll('country').forEach((c) => state.countries.add(c));
  u.getAll('category').forEach((c) => state.cats.add(c));
  if (u.get('sort')) { state.sort = u.get('sort'); $('#sort').value = state.sort; }
  applyLang();
  loadMeta().then(() => load());
})();
