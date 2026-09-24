# tenders.best

Лендинг + каталог государственных закупок 15 стран с автоматическим сбором
объявлений с официальных порталов каждые 3 часа.

## Что внутри

```
index.html                  — лендинг
tenders.html                — каталог тендеров (поиск, фильтры, карточка, подписка, источники)
assets/                     — стили, скрипты, шрифты, логотип, фото для hero
server/                     — бэкенд (FastAPI + SQLite)
  app.py                    — сайт, публичный API, админка
  scrapers/                 — сборщики по странам (один файл на портал)
  pipeline.py               — нормализация и запись без дубликатов
  scheduler.py              — запуск сбора каждые N часов
  collect.py                — CLI для cron: python -m server.collect
  auth.py                   — вход администратора (PBKDF2, сессии)
  demo.py                   — демо-данные для предпросмотра каталога
tests/                      — unit-тесты пайплайна и парсеров
deploy/                     — systemd-юнит и пример crontab
```

## Запуск

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8000
```

* Сайт: `http://localhost:8000/`, каталог: `/tenders`, админка: `/admin`.
* При первом старте создаётся администратор **admin / ololoevadmin123!**
  (меняется в админке или переменными `TB_ADMIN_USER` / `TB_ADMIN_PASSWORD` до первого запуска).
  Смените пароль сразу после развёртывания.
* Встроенный планировщик запускает сбор сразу после старта и затем каждые 3 часа
  (`TB_COLLECT_INTERVAL_HOURS`). Для cron вместо него: `TB_SCHEDULER=0` и строка из `deploy/crontab.example`.
* Docker: `docker build -t tenders . && docker run -p 8000:8000 -v tenders-data:/data tenders`.

Предпросмотр каталога до первого сбора: `python -m server.collect --demo`
(записи помечены «Демо-данные», удаляются кнопкой в админке или `--purge-demo`).

## Как не появляются дубликаты

1. Уникальный ключ `(источник, номер на портале)` — повторный сбор обновляет запись, а не создаёт новую.
2. Отпечаток содержимого `sha1(страна | название | день дедлайна | заказчик)` — тот же тендер,
   пришедший с другого портала (например, TED и национальный сайт), пропускается и считается дубликатом.
3. Дедлайн прошёл → статус `closed`; в каталоге по умолчанию показываются только открытые.

Счётчики каждого запуска (получено / добавлено / обновлено / дубликаты / ошибка) видны в админке.

## Источники (15 стран)

| Страна | Портал | Тип | Сборщик |
|---|---|---|---|
| TJ Таджикистан | zakupki.gov.tj | HTML | `tj_zakupki` |
| UZ Узбекистан | xarid.uzex.uz | JSON API площадки | `uz_xarid` |
| KG Кыргызстан | zakupki.gov.kg (OCDS) | JSON API | `kg_zakupki` |
| KZ Казахстан | goszakup.gov.kz | Open API v3 (токен `GOSZAKUP_TOKEN`) или HTML поиска | `kz_goszakup` |
| TM Туркменистан | ungm.org | JSON/HTML поиска ООН, фильтр по стране | `ungm_tm` |
| AF Афганистан | ungm.org | то же | `ungm_af` |
| RU Россия | zakupki.gov.ru | официальный RSS расширенного поиска | `ru_zakupki` |
| BY Беларусь | icetrade.by | HTML | `by_icetrade` |
| UA Украина | prozorro.gov.ua | публичный API OpenProcurement | `ua_prozorro` |
| MD Молдова | mtender.gov.md | публичный OCDS API | `md_mtender` |
| AZ Азербайджан | etender.gov.az | JSON API портала | `az_etender` |
| PL Польша | ezamowienia.gov.pl | открытый API BZP | `pl_bzp` |
| CZ Чехия | ted.europa.eu | TED API v3, извещения по стране | `ted_cz` |
| DE Германия | ted.europa.eu | то же | `ted_de` |
| LT Литва | ted.europa.eu | то же | `ted_lt` |

**Важно.** Сборщики написаны по документации и по тому, какие запросы делают
сами порталы, но собраны в среде без доступа к этим сайтам, поэтому вживую не
проверялись. После первого запуска откройте админку: у каждого источника виден
статус и текст ошибки. Для порталов на JSON (UZ, KG, AZ) список endpoint-ов
лежит в `server/scrapers/portals.py`, для HTML-порталов (TJ, BY, KZ без токена)
селекторы в соответствующих файлах. Парсеры покрыты тестами на образцах ответов:
`python -m unittest discover -s tests -v`.

## Деплой на сервер

Одной командой с локальной машины (нужен `pip install paramiko`):

```bash
SSH_HOST=31.130.130.195 SSH_USER=root SSH_PASSWORD='…' DOMAIN=archacrm.twc1.net python deploy/push.py
```

Или на самом сервере: скопировать репозиторий и выполнить `DOMAIN=archacrm.twc1.net bash deploy/deploy.sh`.
Скрипт ставит nginx, certbot и Python, создаёт пользователя `tenders`, кладёт код в `/opt/tenders`,
поднимает systemd-службу `tenders` (веб + сбор каждые 3 ч), настраивает vhost для домена и выпускает
сертификат Let's Encrypt, если домен уже указывает на этот сервер. Повторный запуск обновляет код.

Полезные команды на сервере: `systemctl status tenders`, `journalctl -u tenders -f`,
`sudo -u tenders /opt/tenders/.venv/bin/python -m server.collect` (ручной сбор).

## Публичный API

* `GET /api/tenders?q=&country=KZ&country=RU&category=it&min_usd=&max_usd=&deadline=7|30&status=open|all&sort=new|deadline|amount_desc|amount_asc&page=1&per_page=24&lang=ru|en`
* `GET /api/tenders/{id}`, `GET /api/stats`, `GET /api/sources`, `GET /api/meta`
* `POST /api/subscribe` `{email, countries:[…], keywords}`

Админский API (после входа): `/api/admin/overview`, `POST /api/admin/collect[?source=code]`,
`POST /api/admin/sources/{code}/toggle`, `GET|DELETE /api/admin/tenders`, `POST|DELETE /api/admin/demo`,
`POST /api/admin/password`.

## Переменные окружения

См. `.env.example`. Основные: `TB_DATA_DIR` (где лежит SQLite), `TB_COLLECT_INTERVAL_HOURS`,
`TB_SCHEDULER`, `TB_COLLECT_ON_START`, `TB_SECURE_COOKIES` (включите за HTTPS), `GOSZAKUP_TOKEN`.

## Лендинг

Секции: hero (ноутбук с дашбордом как главный объект, фото специалиста, три
подсказки интерфейса), вкладки возможностей с разной композицией для каждого
раздела, «Что даёт tenders.best» с реальным интерфейсом, «Как проходит работа
с тендером», «Что получает каждый участник», источники данных, финальный CTA.
На странице нет вымышленных клиентов, отзывов и маркетинговых цифр; все числа
в макетах интерфейса подписаны как данные интерфейса.

Один шрифт Inter (локально). Радиусы 12 / 16 / 24 px, градиент только на
основной кнопке. Три языка: RU, EN, TJ (переключатель в шапке и футере,
словарь в `assets/js/i18n.js`; каталог использует свой словарь в `catalog.js`).
Анимации: fade-up при появлении, графики один раз, подсказки в hero приподнимаются
на 4 px при наведении (transition, без keyframes); шапка прячется при прокрутке вниз.
