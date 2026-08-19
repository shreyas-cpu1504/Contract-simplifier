import io

from PIL import Image, ImageDraw

from app.services.ocr_service import OCRService


def _create_test_image(text: str) -> bytes:
    image = Image.new("RGB", (1000, 250), "white")
    draw = ImageDraw.Draw(image)

    draw.text(
        (40, 80),
        text,
        fill="black",
    )

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def test_extract_from_image():
    content = _create_test_image(
        "Payment shall be made within 30 days."
    )

    result = OCRService.extract_from_image(content)

    normalized = " ".join(result.split()).lower()

    assert "payment" in normalized
    assert "30 days" in normalized


def test_extract_from_image_rejects_empty_content():
    try:
        OCRService.extract_from_image(b"")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "empty" in str(exc).lower()


def test_extract_from_pdf_rejects_empty_content():
    try:
        OCRService.extract_from_pdf(b"")
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "empty" in str(exc).lower()