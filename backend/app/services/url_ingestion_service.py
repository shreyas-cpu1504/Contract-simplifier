from pathlib import Path
from urllib.parse import urlparse

import httpx


class URLIngestionService:
    """Download contract files from HTTP/HTTPS URLs."""

    ALLOWED_EXTENSIONS = {
        ".txt",
        ".pdf",
        ".docx",
        ".png",
        ".jpg",
        ".jpeg",
    }

    MAX_DOWNLOAD_SIZE = 20 * 1024 * 1024

    @classmethod
    async def download(
        cls,
        url: str,
    ) -> tuple[str, bytes]:

        url = url.strip()

        if not url:
            raise ValueError("URL is required.")

        parsed = urlparse(url)

        if parsed.scheme not in {"http", "https"}:
            raise ValueError(
                "Only HTTP and HTTPS URLs are supported."
            )

        if not parsed.netloc:
            raise ValueError("Invalid URL.")

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=30.0,
            ) as client:

                response = await client.get(url)

                response.raise_for_status()

                content = response.content

        except httpx.HTTPStatusError as exc:
            raise ValueError(
                f"Failed to download URL: HTTP {exc.response.status_code}."
            ) from exc

        except httpx.RequestError as exc:
            raise ValueError(
                f"Failed to download URL: {exc}"
            ) from exc

        if not content:
            raise ValueError(
                "The URL returned an empty file."
            )

        if len(content) > cls.MAX_DOWNLOAD_SIZE:
            raise ValueError(
                "Downloaded file exceeds the 20 MB limit."
            )

        extension = cls._detect_extension(
            url=url,
            content_type=response.headers.get(
                "content-type",
                "",
            ),
        )

        if extension not in cls.ALLOWED_EXTENSIONS:
            raise ValueError(
                "Unsupported contract file type. "
                "Supported types: TXT, PDF, DOCX, PNG, JPG, JPEG."
            )

        filename = cls._build_filename(
            url=url,
            extension=extension,
        )

        return filename, content

    @classmethod
    def _detect_extension(
        cls,
        url: str,
        content_type: str,
    ) -> str:

        parsed = urlparse(url)

        extension = Path(
            parsed.path
        ).suffix.lower()

        if extension in cls.ALLOWED_EXTENSIONS:
            return extension

        content_type = (
            content_type
            .split(";")[0]
            .strip()
            .lower()
        )

        content_type_map = {
            "text/plain": ".txt",
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "image/png": ".png",
            "image/jpeg": ".jpg",
        }

        return content_type_map.get(
            content_type,
            "",
        )

    @staticmethod
    def _build_filename(
        url: str,
        extension: str,
    ) -> str:

        parsed = urlparse(url)

        filename = Path(
            parsed.path
        ).name

        if filename:
            existing_extension = Path(
                filename
            ).suffix.lower()

            if existing_extension in URLIngestionService.ALLOWED_EXTENSIONS:
                return filename

        return f"downloaded_contract{extension}"