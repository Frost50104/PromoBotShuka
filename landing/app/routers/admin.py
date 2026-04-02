import csv
import io

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import get_db
from app.services import promo as promo_svc

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")
signer = URLSafeTimedSerializer(settings.SECRET_KEY)

ADMIN_COOKIE = "admin_session"


def _check_admin(request: Request) -> bool:
    token = request.cookies.get(ADMIN_COOKIE, "")
    try:
        signer.loads(token, max_age=86400 * 7)
        return True
    except BadSignature:
        return False


# ── Авторизация ───────────────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if _check_admin(request):
        return RedirectResponse("/admin/dashboard")
    return templates.TemplateResponse("admin/login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...),
):
    if login == settings.ADMIN_LOGIN and password == settings.ADMIN_PASSWORD:
        token = signer.dumps("admin")
        response = RedirectResponse("/admin/dashboard", status_code=303)
        response.set_cookie(ADMIN_COOKIE, token, max_age=86400 * 7, httponly=True)
        return response
    return templates.TemplateResponse("admin/login.html", {
        "request": request,
        "error": "Неверный логин или пароль",
    })


@router.get("/logout")
async def logout():
    response = RedirectResponse("/admin/login")
    response.delete_cookie(ADMIN_COOKIE)
    return response


# ── Дашборд ───────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    if not _check_admin(request):
        return RedirectResponse("/admin/login")
    stats = await promo_svc.get_stats(db)
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
    })


# ── Загрузка кодов ────────────────────────────────────────────────────────────

@router.post("/upload-codes")
async def upload_codes(
    request: Request,
    codes: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    if not _check_admin(request):
        return RedirectResponse("/admin/login")

    lines = codes.splitlines()
    added, skipped = await promo_svc.import_codes(db, lines)
    stats = await promo_svc.get_stats(db)

    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "stats": stats,
        "upload_result": f"Добавлено: {added}, пропущено дублей: {skipped}",
    })


# ── Выгрузка участников ───────────────────────────────────────────────────────

@router.get("/export-users")
async def export_users(request: Request, db: AsyncSession = Depends(get_db)):
    if not _check_admin(request):
        return RedirectResponse("/admin/login")

    rows = await promo_svc.get_all_users_with_codes(db)

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=["phone", "name", "email", "code", "issued_at", "registered_at"],
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue().encode("utf-8-sig")]),  # utf-8-sig для Excel
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=participants.csv"},
    )
