from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


class FileIngestionService:
    ALLOWED_EXTENSIONS = {
        ".txt",
        ".pdf",
        ".docx",
    }

    BASE_STORAGE_DIR = Path("storage")
    UPLOAD_DIR = BASE_STORAGE_DIR / "uploads"
    EXTRACTED_DIR = BASE_STORAGE_DIR / "extracted"

    @staticmethod
    def validate_extension(filename: str) -> str:
        extension = Path(filename).suffix.lower()

        if extension not in FileIngestionService.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {extension or 'unknown'}"
            )

        return extension

    @staticmethod
    async def read_file(file: UploadFile) -> tuple[str, bytes]:
        if not file.filename:
            raise ValueError("Filename is required.")

        extension = FileIngestionService.validate_extension(
            file.filename
        )

        content = await file.read()

        if not content:
            raise ValueError("Uploaded file is empty.")

        settings = get_settings()
        max_file_size = settings.max_upload_size_mb * 1024 * 1024

        if len(content) > max_file_size:
            raise ValueError(
                f"File size exceeds the {settings.max_upload_size_mb} MB limit."
            )

        file_id = str(uuid4())

        FileIngestionService.UPLOAD_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        stored_filename = f"{file_id}{extension}"
        stored_path = (
            FileIngestionService.UPLOAD_DIR / stored_filename
        )

        stored_path.write_bytes(content)

        return file_id, content

    @staticmethod
    def save_extracted_text(
        file_id: str,
        extracted_text: str,
    ) -> Path:
        FileIngestionService.EXTRACTED_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        extracted_path = (
            FileIngestionService.EXTRACTED_DIR
            / f"{file_id}.txt"
        )

        extracted_path.write_text(
            extracted_text,
            encoding="utf-8",
        )

        return extracted_path