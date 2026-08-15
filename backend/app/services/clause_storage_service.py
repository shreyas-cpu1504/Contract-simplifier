import json
from pathlib import Path

from app.schemas.clause import Clause


class ClauseStorageService:

    CLAUSES_DIR = Path("storage/clauses")

    @classmethod
    def save_clauses(
        cls,
        file_id: str,
        clauses: list[Clause],
    ) -> Path:

        cls.CLAUSES_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = cls.CLAUSES_DIR / f"{file_id}.json"

        data = {
            "file_id": file_id,
            "clause_count": len(clauses),
            "clauses": [
                clause.model_dump()
                for clause in clauses
            ],
        }

        output_path.write_text(
            json.dumps(
                data,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return output_path

    @classmethod
    def load_clauses(
        cls,
        file_id: str,
    ) -> list[Clause]:

        file_path = cls.CLAUSES_DIR / f"{file_id}.json"

        if not file_path.exists():
            return []

        data = json.loads(
            file_path.read_text(
                encoding="utf-8",
            )
        )

        return [
            Clause(**clause)
            for clause in data["clauses"]
        ]
