import re

from app.schemas.clause import Clause


class ClauseSegmentationService:

    NUMBER_PATTERN = re.compile(
        r"^(\d+(?:\.\d+)*)(?:[\.\)])?\s+(.*)$"
    )

    TOP_LEVEL_NUMBER_PATTERN = re.compile(
        r"(?m)^\s*(\d+)(?:[\.\)])\s+([^\n]+)"
    )

    @staticmethod
    def segment(text: str) -> list[Clause]:
        if not text or not text.strip():
            return []

        normalized_text = ClauseSegmentationService._normalize(text)

        # ---------------------------------------------------------
        # IMPORTANT:
        # For numbered contracts, use the numbered sections as
        # the primary segmentation structure.
        #
        # This prevents OCR-created blank lines from splitting
        # one contractual section into multiple clauses.
        # ---------------------------------------------------------

        numbered_sections = (
            ClauseSegmentationService._split_numbered_contract(
                normalized_text
            )
        )

        if numbered_sections:
            blocks = numbered_sections
        else:
            blocks = ClauseSegmentationService._split_into_blocks(
                normalized_text
            )

            if len(blocks) == 1:
                blocks = (
                    ClauseSegmentationService._split_into_sentences(
                        blocks[0]
                    )
                )

        clauses = []
        current_sections = {}

        for block in blocks:
            clause = ClauseSegmentationService._parse_block(
                block,
                len(clauses) + 1,
                current_sections,
            )

            if clause:
                clauses.append(clause)

                if (
                    clause.clause_number
                    and clause.title
                    and "." not in clause.clause_number
                ):
                    current_sections[
                        clause.clause_number
                    ] = clause.title

        return clauses

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalize extracted contract text while preserving
        meaningful line breaks.
        """

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        lines = [
            line.strip()
            for line in text.split("\n")
        ]

        normalized = "\n".join(lines)

        # Prevent excessive blank lines.
        normalized = re.sub(
            r"\n{3,}",
            "\n\n",
            normalized,
        )

        return normalized.strip()

    @staticmethod
    def _split_numbered_contract(text: str) -> list[str]:
        """
        Split a contract using top-level numbered headings.

        Example:

            Introduction...

            1. SCOPE OF SERVICES
            Company agrees...

            2. PAYMENT TERMS
            Client shall pay...

        becomes:

            Introduction...

            1. SCOPE OF SERVICES
            Company agrees...

            2. PAYMENT TERMS
            Client shall pay...
        """

        matches = list(
            ClauseSegmentationService.TOP_LEVEL_NUMBER_PATTERN.finditer(
                text
            )
        )

        # A single numbered item is not enough to confidently
        # treat the entire document as a numbered contract.
        if len(matches) < 2:
            return []

        blocks = []

        # Ignore introductory text before the first numbered section.
#
# Contract titles, parties, addresses, and execution language
# before section 1 are document-level information, not clauses.

        for index, match in enumerate(matches):
            start = match.start()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(text)

            block = text[start:end].strip()

            if block:
                blocks.append(block)

        return blocks

    @staticmethod
    def _split_into_blocks(text: str) -> list[str]:
        """
        Split unnumbered contract text using blank lines.
        """

        raw_blocks = re.split(
            r"\n\s*\n",
            text,
        )

        blocks = []

        for raw_block in raw_blocks:
            block = raw_block.strip()

            if not block:
                continue

            # OCR may represent bullets using unusual characters.
            # Bullet/list items belong to the preceding clause.
            if (
                re.match(
                    r"^[-*•â€¢°¢]\s+",
                    block,
                )
                and blocks
            ):
                blocks[-1] = (
                    f"{blocks[-1]}\n{block}"
                )
            else:
                blocks.append(block)

        return blocks

    @staticmethod
    def _split_flat_contract(text: str) -> list[str]:
        """
        Fallback for contracts where numbered headings occur
        without useful paragraph structure.
        """

        text = text.strip()

        if not text:
            return []

        parts = re.split(
            r"(?m)(?=^\d+(?:\.\d+)*[\.)]?\s+)",
            text,
        )

        blocks = [
            part.strip()
            for part in parts
            if part.strip()
        ]

        if len(blocks) <= 1:
            return ClauseSegmentationService._split_into_sentences(
                text
            )

        return blocks

    @staticmethod
    def _merge_numbered_headings(
        blocks: list[str],
    ) -> list[str]:
        """
        Merge numbered headings with the following block.

        Kept for compatibility with existing code/tests.
        """

        merged = []
        index = 0

        while index < len(blocks):
            block = blocks[index]

            lines = block.split("\n")
            first_line = lines[0].strip()

            match = ClauseSegmentationService.NUMBER_PATTERN.match(
                first_line
            )

            if (
                match
                and "." not in match.group(1)
                and len(lines) == 1
                and index + 1 < len(blocks)
            ):
                number = match.group(1)
                heading = match.group(2).strip()

                if (
                    len(heading) <= 100
                    and any(
                        char.isalpha()
                        for char in heading
                    )
                ):
                    next_block = blocks[index + 1].strip()

                    merged.append(
                        f"{number}. {heading}\n{next_block}"
                    )

                    index += 2
                    continue

            merged.append(block)
            index += 1

        return merged

    @staticmethod
    def _split_into_sentences(text: str) -> list[str]:
        """
        Fallback for unstructured text.
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

            # -------------------------------------------------
            # Top-level numbered section
            #
            # Example:
            #
            # 1. PAYMENT TERMS
            # The Client shall pay...
            #
            # becomes:
            #
            # title = PAYMENT TERMS
            # text = The Client shall pay...
            # -------------------------------------------------

            if (
                "." not in clause_number
                and len(lines) >= 2
            ):
                title = remainder

                clause_text = "\n".join(
                    lines[1:]
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
                    parent_clause=None,
                )

            # -------------------------------------------------
            # Numbered clause without separate heading
            # -------------------------------------------------

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
            and any(
                char.isalpha()
                for char in block
            )
        ):
            return None

        # Unnumbered clause / introductory content.
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