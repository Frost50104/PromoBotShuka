import io
import qrcode
from qrcode.image.styledpil import StyledPilImage


def generate_qr_bytes(code: str) -> bytes:
    """Генерировать QR-код и вернуть PNG как bytes."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(code)
    qr.make(fit=True)
    img = qr.make_image(image_factory=StyledPilImage)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
