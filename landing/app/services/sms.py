import httpx
from app.config import settings


async def send_otp_sms(phone: str, code: str) -> bool:
    """Отправить OTP-код через SMSC.ru. Возвращает True при успехе."""
    url = "https://smsc.ru/sys/send.php"
    params = {
        "login": settings.SMSC_LOGIN,
        "psw": settings.SMSC_PASSWORD,
        "phones": phone,
        "mes": f"Ваш код подтверждения UPPETIT: {code}",
        "fmt": 3,         # JSON-ответ
        "charset": "utf-8",
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params)
            data = response.json()
            return "error" not in data
    except Exception:
        return False
