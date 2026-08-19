from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from app.services.ocr_service import OCRService


class TextExtractionService:

    @staticmethod
    def extract(
        filename: str,
        content: bytes,
    ) -> str:
        extension = Path(filename).suffix.lower()

        if extension == ".txt":
            return TextExtractionService._extract_txt(content)

        if extension == ".pdf":
            return TextExtractionService._extract_pdf(content)

        if extension == ".docx":
            return TextExtractionService._extract_docx(content)

        if extension in {".png", ".jpg", ".jpeg"}:
            return OCRService.extract_from_image(content)

        raise ValueError(
            f"Unsupported file type for text extraction: "
            f"{extension or 'unknown'}"
        )

    @staticmethod
    def _extract_txt(content: bytes) -> str:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode(
                "utf-8",
                errors="replace",
            )

        return text.strip()

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        reader = PdfReader(BytesIO(content))

        pages = []

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                pages.append(page_text)

        extracted_text = "\n\n".join(pages).strip()

        # Normal text-based PDF.
        if extracted_text:
            return extracted_text

        # Scanned/image-only PDF.
        return OCRService.extract_from_pdf(content)

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        document = Document(BytesIO(content))

        paragraphs = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs).strip()