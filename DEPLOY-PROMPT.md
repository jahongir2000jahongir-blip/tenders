# Задание для сессии, которая имеет доступ к серверу

Проект tenders.best: лендинг + каталог тендеров 15 стран (FastAPI + SQLite, сборщики каждые 3 часа, админка).
Репозиторий: https://github.com/jahongir2000jahongir-blip/tenders, ветка `claude/jolly-lamport-685he9`
(в этом архиве та же версия).

## Что нужно сделать

1. Подключиться к серверу `31.130.130.195` по SSH под root (пароль у владельца) так же, как для ArchaCRM.
2. Залить проект и запустить установку. Самый простой путь, с локальной машины:
   ```bash
   pip install paramiko
   SSH_HOST=31.130.130.195 SSH_USER=root SSH_PASSWORD='<пароль>' DOMAIN=archacrm.twc1.net python deploy/push.py
   ```
   Либо на сервере:
   ```bash
   apt-get install -y git
   git clone -b claude/jolly-lamport-685he9 https://github.com/jahongir2000jahongir-blip/tenders.git /opt/tenders-src
   DOMAIN=archacrm.twc1.net bash /opt/tenders-src/deploy/deploy.sh
   ```
   Скрипт `deploy/deploy.sh` идемпотентный: ставит nginx, certbot, Python, создаёт пользователя `tenders`,
   кладёт код в `/opt/tenders`, поднимает systemd-службу `tenders` (веб на 127.0.0.1:8000 + сбор каждые 3 ч),
   настраивает vhost `archacrm.twc1.net` и выпускает сертификат Let's Encrypt.
3. Домен `archacrm.twc1.net` должен указывать на этот сервер. Если скрипт напишет, что домен резолвится
   в другой адрес, привязать домен к серверу 31.130.130.195 в панели Timeweb Cloud (раздел «Домены»),
   затем выполнить `certbot --nginx -d archacrm.twc1.net --redirect`.
4. Проверить: `https://archacrm.twc1.net/` (лендинг), `/tenders` (каталог), `/admin` (логин `admin`,
   пароль `ololoevadmin123!`, сменить после входа). В админке нажать «Собрать сейчас (все)» и посмотреть
   статусы 15 источников; у сборщиков, которые упали, текст ошибки виден в таблице. Endpoint-ы порталов
   правятся в `server/scrapers/portals.py` и в файлах соответствующих стран.
5. Если сервер уже занят другим сайтом на 80/443 порту (ArchaCRM), деплой не трогает чужие vhost-ы,
   только удаляет `sites-enabled/default`. Порт приложения 8000 занят? Поменять в `deploy/tenders.service`
   и `deploy/nginx.conf`.

Полезное: `systemctl status tenders`, `journalctl -u tenders -f`,
`sudo -u tenders /opt/tenders/.venv/bin/python -m server.collect` (ручной сбор),
`python -m server.collect --demo` / `--purge-demo` (демо-записи для предпросмотра).

Когда будет куплен домен tenders.best: A-запись на IP сервера, затем
`certbot --nginx -d tenders.best -d www.tenders.best --redirect` и добавить домен в `server_name` vhost-а.
