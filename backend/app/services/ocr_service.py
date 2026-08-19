from io import BytesIO

import pymupdf
import pytesseract
from PIL import Image


class OCRService:
    """OCR service for images and scanned PDF pages."""

    @staticmethod
    def extract_from_image(content: bytes) -> str:
        if not content:
            raise ValueError("Image content is empty.")

        try:
            image = Image.open(BytesIO(content))
            text = pytesseract.image_to_string(image)
        except Exception as exc:
            raise ValueError(
                f"Failed to perform OCR on image: {exc}"
            ) from exc

        return text.strip()

    @staticmethod
    def extract_from_pdf(content: bytes) -> str:
        if not content:
            raise ValueError("PDF content is empty.")

        try:
            document = pymupdf.open(
                stream=content,
                filetype="pdf",
            )

            pages = []

            try:
                for page in document:
                    pixmap = page.get_pixmap(
                        matrix=pymupdf.Matrix(2, 2),
                        alpha=False,
                    )

                    image = Image.frombytes(
                        "RGB",
                        [pixmap.width, pixmap.height],
                        pixmap.samples,
                    )

                    text = pytesseract.image_to_string(image).strip()

                    if text:
                        pages.append(text)
            finally:
                document.close()

        except Exception as exc:
            raise ValueError(
                f"Failed to perform OCR on PDF: {exc}"
            ) from exc

        return "\n\n".join(pages).strip()