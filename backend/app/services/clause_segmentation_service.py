import re

from app.schemas.clause import Clause


class ClauseSegmentationService:

    NUMBER_PATTERN = re.compile(
        r"^(\d+(?:\.\d+)*)(?:[\.\)])?\s+(.*)$"
    )

    @staticmethod
    def segment(text: str) -> list[Clause]:
        if not text or not text.strip():
            return []

        normalized_text = ClauseSegmentationService._normalize(text)

        blocks = ClauseSegmentationService._split_into_blocks(
            normalized_text
        )

        # If the document has no paragraph/numbered structure and
        # everything arrived as one block, fall back to sentence-level
        # segmentation. This is useful for extracted text from PDFs,
        # DOCX files, OCR, and simple text input where line breaks
        # may have been lost.
        if len(blocks) == 1:
            blocks = ClauseSegmentationService._split_into_sentences(
                blocks[0]
            )

        clauses = []

        current_sections = {}

        for block in blocks:

            # Check whether this block is a numbered section.
            section_match = (
                ClauseSegmentationService.NUMBER_PATTERN.match(
                    block.split("\n")[0]
                )
            )

            if section_match:
                number = section_match.group(1)
                remainder = section_match.group(2).strip()

                # A top-level number such as:
                # 1. PAYMENT
                if (
                    "." not in number
                    and len(block.split("\n")) == 1
                ):
                    if (
                        len(remainder) <= 100
                        and remainder.upper() == remainder
                    ):
                        current_sections[number] = remainder
                        continue

            clause = ClauseSegmentationService._parse_block(
                block,
                len(clauses) + 1,
                current_sections,
            )

            if clause:
                clauses.append(clause)

        return clauses

    @staticmethod
    def _normalize(text: str) -> str:
        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        lines = [
            line.strip()
            for line in text.split("\n")
        ]

        normalized = "\n".join(lines)

        normalized = re.sub(
            r"\n{3,}",
            "\n\n",
            normalized,
        )

        return normalized.strip()

    @staticmethod
    def _split_into_blocks(text: str) -> list[str]:
        blocks = re.split(
            r"\n\s*\n",
            text,
        )

        return [
            block.strip()
            for block in blocks
            if block.strip()
        ]

    @staticmethod
    def _split_into_sentences(text: str) -> list[str]:
        """
        Split a flat block of contract text into sentence-level units.

        This is a fallback only. Structured paragraphs and numbered
        clauses are handled before reaching this method.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+(?=[A-Z])",
            text.strip(),
        )

        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

    @staticmethod
    def _parse_block(
        block: str,
        order: int,
        current_sections: dict[str, str],
    ) -> Clause | None:

        lines = block.split("\n")

        if not lines:
            return None

        first_line = lines[0].strip()

        match = ClauseSegmentationService.NUMBER_PATTERN.match(
            first_line
        )

        if match:
            clause_number = match.group(1)
            remainder = match.group(2).strip()

            # Top-level heading such as:
            # 1. PAYMENT
            if (
                "." not in clause_number
                and len(lines) == 1
            ):
                if (
                    len(remainder) <= 100
                    and remainder.upper() == remainder
                ):
                    return None

            parent_clause = (
                ClauseSegmentationService._get_parent(
                    clause_number
                )
            )

            title = (
                current_sections.get(parent_clause)
                if parent_clause
                else None
            )

            # Remove "1.1 " from the actual clause text.
            if len(lines) == 1:
                clause_text = remainder
            else:
                remaining_lines = lines[1:]

                clause_text = "\n".join(
                    [remainder] + remaining_lines
                ).strip()

            if not clause_text:
                return None

            return Clause(
                clause_id=f"clause-{order}",
                title=title,
                text=clause_text,
                order=order,
                character_count=len(clause_text),
                clause_number=clause_number,
                parent_clause=parent_clause,
            )

        # Ignore standalone uppercase document titles.
        if (
            len(block) <= 100
            and block.upper() == block
            and any(char.isalpha() for char in block)
        ):
            return None

        return Clause(
            clause_id=f"clause-{order}",
            title=None,
            text=block,
            order=order,
            character_count=len(block),
            clause_number=None,
            parent_clause=None,
        )

    @staticmethod
    def _get_parent(
        clause_number: str,
    ) -> str | None:

        parts = clause_number.split(".")

        if len(parts) <= 1:
            return None

        return ".".join(parts[:-1])
