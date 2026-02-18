"""QR code generation service."""

import io
from typing import BinaryIO

import qrcode
from qrcode.image.pil import PilImage

from app.utils.logging import get_logger

logger = get_logger(__name__)


class QRService:
    """Service for QR code generation."""

    @staticmethod
    def generate_qr_code(data: str) -> BinaryIO:
        """
        Generate QR code as PNG image.

        Args:
            data: Data to encode in QR code

        Returns:
            Binary IO object containing PNG image
        """
        logger.info("Generating QR code", data_length=len(data))

        # Create QR code
        qr = qrcode.QRCode(
            version=1,  # Auto-adjust size
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(data)
        qr.make(fit=True)

        # Create image
        img: PilImage = qr.make_image(fill_color="black", back_color="white")

        # Save to bytes buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        logger.debug("QR code generated successfully")

        return buffer
