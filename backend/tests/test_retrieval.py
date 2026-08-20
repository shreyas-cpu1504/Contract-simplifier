from app.schemas.clause import Clause
from app.services.retrieval_service import RetrievalService


def make_clause(
    clause_id: str,
    number: str,
    text: str,
) -> Clause:
    return Clause(
        clause_id=clause_id,
        clause_number=number,
        title=None,
        text=text,
        order=int(number),
        character_count=len(text),
    )


def test_retrieves_payment_clause():
    clauses = [
        make_clause(
            "c1",
            "1",
            "The Customer shall pay the invoice within 30 days.",
        ),
        make_clause(
            "c2",
            "2",
            "Either party may terminate the agreement.",
        ),
    ]

    results = RetrievalService.retrieve(
        "When must the customer pay the invoice?",
        clauses,
    )

    assert results
    assert results[0].clause_id == "c1"


def test_retrieves_termination_clause():
    clauses = [
        make_clause(
            "c1",
            "1",
            "The Customer shall pay the invoice within 30 days.",
        ),
        make_clause(
            "c2",
            "2",
            "Either party may terminate the agreement upon written notice.",
        ),
    ]

    results = RetrievalService.retrieve(
        "How can the agreement be terminated?",
        clauses,
    )

    assert results
    assert results[0].clause_id == "c2"


def test_empty_question_returns_no_results():
    clauses = [
        make_clause(
            "c1",
            "1",
            "The Customer shall pay the invoice.",
        ),
    ]

    results = RetrievalService.retrieve(
        "",
        clauses,
    )

    assert results == []


def test_no_relevant_clause_returns_empty():
    clauses = [
        make_clause(
            "c1",
            "1",
            "The Customer shall pay the invoice.",
        ),
    ]

    results = RetrievalService.retrieve(
        "What is the intellectual property ownership?",
        clauses,
    )

    assert results == []