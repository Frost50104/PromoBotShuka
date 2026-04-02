import re
from datetime import date

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import get_db
from app.services import promo as promo_svc
from app.services.qr import generate_qr_bytes

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
signer = URLSafeTimedSerializer(settings.SECRET_KEY)

PHONE_RE = re.compile(r"^(\+7|7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$")


def _normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    return "+" + digits


def _is_promo_active() -> bool:
    today = date.today()
    return settings.PROMO_START <= today <= settings.PROMO_END


# ── Главная ───────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "promo_active": _is_promo_active(),
        "promo_end": settings.PROMO_END.strftime("%d.%m.%Y"),
    })


# ── Форма → QR ────────────────────────────────────────────────────────────────

@router.post("/claim")
async def claim(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    def render_error(error: str):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "promo_active": True,
            "promo_end": settings.PROMO_END.strftime("%d.%m.%Y"),
            "error": error,
            "name_value": name,
            "phone_value": phone,
            "email_value": email,
        })

    if not _is_promo_active():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "promo_active": False,
            "promo_end": settings.PROMO_END.strftime("%d.%m.%Y"),
        })

    if not PHONE_RE.match(phone.strip()):
        return render_error("Введите корректный номер телефона.")

    norm_phone = _normalize_phone(phone)

    # Уже получал код?
    existing_user = await promo_svc.get_user_by_phone(db, norm_phone)
    if existing_user:
        existing_code = await promo_svc.user_has_code(db, existing_user)
        if existing_code:
            token = signer.dumps(norm_phone)
            return RedirectResponse(f"/success?t={token}", status_code=303)

    user = await promo_svc.get_or_create_user(
        db, norm_phone, name.strip() or None, email.strip() or None
    )
    promo_code = await promo_svc.assign_code(db, user)

    if promo_code is None:
        return render_error("К сожалению, все подарки уже разобрали. Следите за нашими акциями!")

    token = signer.dumps(norm_phone)
    return RedirectResponse(f"/success?t={token}", status_code=303)


# ── Страница с QR ─────────────────────────────────────────────────────────────

@router.get("/success", response_class=HTMLResponse)
async def success_page(
    request: Request,
    t: str = "",
    db: AsyncSession = Depends(get_db),
):
    try:
        phone = signer.loads(t, max_age=86400 * 30)
    except BadSignature:
        return RedirectResponse("/")

    user = await promo_svc.get_user_by_phone(db, phone)
    if not user:
        return RedirectResponse("/")
    code = await promo_svc.user_has_code(db, user)
    if not code:
        return RedirectResponse("/")

    return templates.TemplateResponse("success.html", {
        "request": request,
        "code": code.raw_code,
        "user_name": user.name or "",
        "token": t,
    })


@router.get("/qr/{token}")
async def qr_image(token: str, db: AsyncSession = Depends(get_db)):
    try:
        phone = signer.loads(token, max_age=86400 * 30)
    except BadSignature:
        return Response(status_code=404)

    user = await promo_svc.get_user_by_phone(db, phone)
    if not user:
        return Response(status_code=404)
    code = await promo_svc.user_has_code(db, user)
    if not code:
        return Response(status_code=404)

    return Response(content=generate_qr_bytes(code.raw_code), media_type="image/png")


@router.get("/qr-download/{token}")
async def qr_download(token: str, db: AsyncSession = Depends(get_db)):
    try:
        phone = signer.loads(token, max_age=86400 * 30)
    except BadSignature:
        return Response(status_code=404)

    user = await promo_svc.get_user_by_phone(db, phone)
    if not user:
        return Response(status_code=404)
    code = await promo_svc.user_has_code(db, user)
    if not code:
        return Response(status_code=404)

    return Response(
        content=generate_qr_bytes(code.raw_code),
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=uppetit_qr.png"},
    )
