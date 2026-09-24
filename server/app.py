"""FastAPI application: static site, public tenders API, admin panel."""
from __future__ import annotations

import logging
import re
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from . import auth, config, db, scheduler
from .classify import CATEGORIES
from .countries import COUNTRIES, SOURCES
from .scrapers import COLLECTORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("app")

ROOT = config.ROOT
TEMPLATES = Path(__file__).parent / "templates"
COOKIE = "tb_session"


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init()
    auth.ensure_admin()
    if config.SCHEDULER_ENABLED:
        scheduler.start()
    yield
    scheduler.stop()


app = FastAPI(title="tenders.best", docs_url=None, redoc_url=None, lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")


# ---------- pages ----------
@app.get("/", include_in_schema=False)
def landing():
    return FileResponse(ROOT / "index.html")


@app.get("/tenders", include_in_schema=False)
def catalogue():
    return FileResponse(ROOT / "tenders.html")


# ---------- helpers ----------
def _like(q: str) -> str:
    return "%" + re.sub(r"\s+", "%", q.strip()) + "%"


def serialize(row: dict, lang: str = "ru") -> dict:
    src = next((s for s in SOURCES if s["code"] == row["source"]), None)
    c = COUNTRIES.get(row["country"], {})
    return {
        "id": row["id"], "source": row["source"], "external_id": row["external_id"],
        "source_name": src["name"] if src else ("Демо" if row["source"] == "demo" else row["source"]),
        "country": row["country"], "country_name": c.get(lang) or c.get("ru") or row["country"],
        "title": row["title"], "description": row["description"], "customer": row["customer"], "region": row["region"],
        "category": row["category"], "category_name": CATEGORIES.get(row["category"], CATEGORIES["other"])[lang],
        "method": row["method"], "amount": row["amount"], "currency": row["currency"], "amount_usd": row["amount_usd"],
        "published_at": row["published_at"], "deadline_at": row["deadline_at"], "url": row["url"],
        "status": row["status"], "lang": row["lang"], "first_seen_at": row["first_seen_at"], "updated_at": row["updated_at"],
        "is_demo": row["source"] == "demo",
    }


# ---------- public API ----------
@app.get("/api/tenders")
def api_tenders(
    q: str = "", country: list[str] = Query(default=[]), category: list[str] = Query(default=[]),
    status: str = "open", min_usd: float | None = None, max_usd: float | None = None,
    deadline: str = "", sort: str = "new", page: int = 1, per_page: int = 24, lang: str = "ru",
):
    lang = "en" if lang == "en" else "ru"
    where, params = [], []
    if status == "open":
        where.append("status='open'")
    if q.strip():
        where.append("(title LIKE ? OR customer LIKE ? OR description LIKE ? OR region LIKE ?)")
        params += [_like(q)] * 4
    countries = [c.upper() for c in country if c.upper() in COUNTRIES]
    if countries:
        where.append(f"country IN ({','.join('?' * len(countries))})")
        params += countries
    cats = [c for c in category if c in CATEGORIES]
    if cats:
        where.append(f"category IN ({','.join('?' * len(cats))})")
        params += cats
    if min_usd is not None:
        where.append("amount_usd >= ?"); params.append(min_usd)
    if max_usd is not None:
        where.append("amount_usd <= ?"); params.append(max_usd)
    if deadline in ("7", "30"):
        where.append("deadline_at IS NOT NULL AND deadline_at <= datetime('now', ?)")
        params.append(f"+{deadline} days")
    order = {
        "new": "COALESCE(published_at, first_seen_at) DESC, id DESC",
        "deadline": "CASE WHEN deadline_at IS NULL THEN 1 ELSE 0 END, deadline_at ASC",
        "amount_desc": "CASE WHEN amount_usd IS NULL THEN 1 ELSE 0 END, amount_usd DESC",
        "amount_asc": "CASE WHEN amount_usd IS NULL THEN 1 ELSE 0 END, amount_usd ASC",
    }.get(sort, "COALESCE(published_at, first_seen_at) DESC, id DESC")
    sql_where = ("WHERE " + " AND ".join(where)) if where else ""
    per_page = max(1, min(per_page, 100))
    page = max(1, page)
    total = db.one(f"SELECT COUNT(*) AS n FROM tenders {sql_where}", tuple(params))["n"]
    items = db.rows(
        f"SELECT * FROM tenders {sql_where} ORDER BY {order} LIMIT ? OFFSET ?",
        tuple(params) + (per_page, (page - 1) * per_page),
    )
    return {"total": total, "page": page, "per_page": per_page, "items": [serialize(r, lang) for r in items]}


@app.get("/api/tenders/{tender_id}")
def api_tender(tender_id: int, lang: str = "ru"):
    row = db.one("SELECT * FROM tenders WHERE id=?", (tender_id,))
    if not row:
        raise HTTPException(404, "not found")
    return serialize(row, "en" if lang == "en" else "ru")


@app.get("/api/stats")
def api_stats():
    per_country = {r["country"]: r for r in db.rows(
        "SELECT country, COUNT(*) AS n, COALESCE(SUM(amount_usd), 0) AS usd FROM tenders WHERE status='open' GROUP BY country")}
    total = db.one("SELECT COUNT(*) AS n, COALESCE(SUM(amount_usd),0) AS usd FROM tenders WHERE status='open'")
    cats = db.rows("SELECT category, COUNT(*) AS n FROM tenders WHERE status='open' GROUP BY category")
    return {
        "countries": [
            {"code": code, "ru": meta["ru"], "en": meta["en"], "currency": meta["currency"],
             "open": per_country.get(code, {}).get("n", 0), "usd": round(per_country.get(code, {}).get("usd", 0))}
            for code, meta in COUNTRIES.items()
        ],
        "total_open": total["n"], "total_usd": round(total["usd"]),
        "categories": {c["category"]: c["n"] for c in cats},
        "last_collect_at": db.get_setting("last_collect_at"),
        "next_collect_at": scheduler.next_run_at(),
        "has_demo": bool(db.one("SELECT 1 AS x FROM tenders WHERE source='demo' LIMIT 1")),
    }


@app.get("/api/sources")
def api_sources():
    state = {r["code"]: r for r in db.rows("SELECT * FROM sources")}
    out = []
    for s in SOURCES:
        st = state.get(s["code"], {})
        out.append({**s, "enabled": bool(st.get("enabled", 1)), "last_run_at": st.get("last_run_at"),
                    "last_status": st.get("last_status"), "last_error": st.get("last_error"),
                    "last_fetched": st.get("last_fetched", 0), "last_added": st.get("last_added", 0),
                    "country_ru": COUNTRIES[s["country"]]["ru"], "country_en": COUNTRIES[s["country"]]["en"]})
    return out


@app.get("/api/meta")
def api_meta():
    return {"countries": COUNTRIES, "categories": CATEGORIES}


@app.post("/api/subscribe")
async def api_subscribe(request: Request):
    body = await request.json()
    email = (body.get("email") or "").strip()
    countries = [c for c in (body.get("countries") or []) if c in COUNTRIES]
    keywords = (body.get("keywords") or "").strip()[:500]
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(400, "invalid email")
    if not countries:
        raise HTTPException(400, "pick a country")
    with db.tx() as con:
        con.execute("INSERT INTO subscriptions (email, countries, keywords, created_at) VALUES (?,?,?,?)",
                    (email, ",".join(countries), keywords, db.utcnow()))
    return {"ok": True}


# ---------- admin ----------
def current_user(request: Request) -> dict:
    user = auth.user_for_token(request.cookies.get(COOKIE))
    if not user:
        raise HTTPException(401, "unauthorized")
    return user


def _template(name: str, **vars) -> HTMLResponse:
    html = (TEMPLATES / name).read_text(encoding="utf-8")
    for k, v in vars.items():
        html = html.replace("{{" + k + "}}", str(v))
    return HTMLResponse(html)


@app.get("/admin/login", include_in_schema=False)
def admin_login_page(request: Request, error: str = ""):
    if auth.user_for_token(request.cookies.get(COOKIE)):
        return RedirectResponse("/admin", status_code=303)
    return _template("login.html", error=("Неверный логин или пароль" if error else ""))


@app.post("/admin/login", include_in_schema=False)
def admin_login(username: str = Form(...), password: str = Form(...)):
    token = auth.login(username, password)
    if not token:
        return RedirectResponse("/admin/login?error=1", status_code=303)
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie(COOKIE, token, httponly=True, samesite="lax", secure=config.SECURE_COOKIES,
                    max_age=config.SESSION_DAYS * 86400, path="/")
    return resp


@app.post("/admin/logout", include_in_schema=False)
def admin_logout(request: Request):
    auth.logout(request.cookies.get(COOKIE))
    resp = RedirectResponse("/admin/login", status_code=303)
    resp.delete_cookie(COOKIE, path="/")
    return resp


@app.get("/admin", include_in_schema=False)
def admin_page(request: Request):
    user = auth.user_for_token(request.cookies.get(COOKIE))
    if not user:
        return RedirectResponse("/admin/login", status_code=303)
    return _template("admin.html", username=user["username"])


@app.get("/api/admin/overview")
def admin_overview(user: dict = Depends(current_user)):
    return {
        "user": user,
        "sources": api_sources(),
        "stats": api_stats(),
        "runs": db.rows("SELECT * FROM runs ORDER BY id DESC LIMIT 60"),
        "subscriptions": db.rows("SELECT * FROM subscriptions ORDER BY id DESC LIMIT 200"),
        "totals": db.one("SELECT COUNT(*) AS all_count, SUM(status='open') AS open_count, SUM(source='demo') AS demo_count FROM tenders"),
        "interval_hours": config.COLLECT_INTERVAL_HOURS,
        "scheduler_enabled": config.SCHEDULER_ENABLED,
        "collect_running": scheduler.is_running(),
        "rates_updated_at": db.get_setting("rates_updated_at"),
    }


@app.post("/api/admin/collect")
def admin_collect(source: str | None = None, user: dict = Depends(current_user)):
    if source and source not in COLLECTORS:
        raise HTTPException(404, "unknown source")
    if scheduler.is_running():
        return JSONResponse({"ok": False, "message": "Сбор уже выполняется"}, status_code=409)
    threading.Thread(target=scheduler.collect_now, args=([source] if source else None,), daemon=True).start()
    return {"ok": True}


@app.post("/api/admin/sources/{code}/toggle")
def admin_toggle_source(code: str, user: dict = Depends(current_user)):
    if code not in COLLECTORS:
        raise HTTPException(404, "unknown source")
    with db.tx() as con:
        con.execute("UPDATE sources SET enabled = 1 - enabled WHERE code=?", (code,))
    return {"ok": True, "enabled": bool(db.one("SELECT enabled FROM sources WHERE code=?", (code,))["enabled"])}


@app.get("/api/admin/tenders")
def admin_tenders(q: str = "", page: int = 1, user: dict = Depends(current_user)):
    where, params = "", ()
    if q.strip():
        where, params = "WHERE title LIKE ? OR customer LIKE ? OR source LIKE ?", (_like(q), _like(q), _like(q))
    total = db.one(f"SELECT COUNT(*) AS n FROM tenders {where}", params)["n"]
    rows = db.rows(f"SELECT * FROM tenders {where} ORDER BY id DESC LIMIT 50 OFFSET ?", params + ((max(1, page) - 1) * 50,))
    return {"total": total, "items": [serialize(r) for r in rows]}


@app.delete("/api/admin/tenders/{tender_id}")
def admin_delete_tender(tender_id: int, user: dict = Depends(current_user)):
    with db.tx() as con:
        n = con.execute("DELETE FROM tenders WHERE id=?", (tender_id,)).rowcount
    return {"ok": bool(n)}


@app.post("/api/admin/demo")
def admin_demo(user: dict = Depends(current_user)):
    from .demo import seed
    return {"ok": True, "inserted": seed()}


@app.delete("/api/admin/demo")
def admin_purge_demo(user: dict = Depends(current_user)):
    from .demo import purge
    return {"ok": True, "removed": purge()}


@app.delete("/api/admin/subscriptions/{sub_id}")
def admin_delete_subscription(sub_id: int, user: dict = Depends(current_user)):
    with db.tx() as con:
        con.execute("DELETE FROM subscriptions WHERE id=?", (sub_id,))
    return {"ok": True}


@app.post("/api/admin/password")
async def admin_password(request: Request, user: dict = Depends(current_user)):
    body = await request.json()
    new = (body.get("password") or "")
    if len(new) < 8:
        raise HTTPException(400, "минимум 8 символов")
    auth.change_password(user["id"], new)
    return {"ok": True}
