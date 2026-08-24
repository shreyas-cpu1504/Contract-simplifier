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

        # If there is no paragraph structure, detect whether
        # the document contains numbered contract clauses.
        if len(blocks) == 1:
            blocks = ClauseSegmentationService._split_flat_contract(
                blocks[0]
            )

        # Merge numbered headings with the content that follows
        # them when headings and content exist in separate blocks.
        blocks = ClauseSegmentationService._merge_numbered_headings(
            blocks
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
    def _split_into_blocks(text: str) -> list[str]:
        """
        Split text using blank lines.

        Example:

            1. Payment
            Payment text.

            2. Termination
            Termination text.

        becomes two blocks.
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

            # Bullet/list items belong to the preceding clause.
            if (
                re.match(r"^[-*•]\s+", block)
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
        Split contract text that contains numbered clauses but
        does not contain blank lines between clauses.

        Example:

            1. Payment
            The Customer shall pay the invoice within 30 days.
            2. Termination
            Either party may terminate this agreement upon written notice.
            3. Liability
            The Customer shall have unlimited liability for all losses.

        becomes:

            1. Payment
            The Customer shall pay the invoice within 30 days.

            2. Termination
            Either party may terminate this agreement upon written notice.

            3. Liability
            The Customer shall have unlimited liability for all losses.
        """

        text = text.strip()

        if not text:
            return []

        # Split immediately before a numbered clause heading.
        #
        # (?m) = multiline mode
        # ^    = beginning of a line
        # \d+  = clause number
        #
        # Supports:
        # 1. Payment
        # 2) Termination
        # 3 Liability
        # 1.1 Definitions
        parts = re.split(
            r"(?m)(?=^\d+(?:\.\d+)*[\.)]?\s+)",
            text,
        )

        blocks = [
            part.strip()
            for part in parts
            if part.strip()
        ]

        # If numbered structure wasn't detected,
        # use sentence-level segmentation.
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
        Merge a numbered heading with the following block.

        Example:

            Block 1:
                1. Payment

            Block 2:
                The Customer shall pay...

        becomes:

            1. Payment
            The Customer shall pay...
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

                # Short numbered heading.
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
        Fallback for unstructured text where no numbered
        contract structure exists.
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
            # Top-level numbered clause
            #
            # Example:
            #
            # 1. Payment
            # The Customer shall pay...
            #
            # We want:
            #
            # clause_number = "1"
            # title = "Payment"
            # text = "The Customer shall pay..."
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
            # Numbered clause without a separate heading
            #
            # Example:
            #
            # 1. The Customer shall pay...
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

        # Unnumbered clause.
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