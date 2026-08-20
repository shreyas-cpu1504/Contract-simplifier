from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.file_ingestion_service import FileIngestionService


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "Contract Simplifier API"
    assert data["version"] == "0.1.0"


def test_text_ingestion_endpoint():
    response = client.post(
        "/api/v1/ingestion/text",
        json={
            "input_type": "text",
            "content": "Payment shall be made within 30 days.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Text received successfully."
    assert data["input_type"] == "text"
    assert data["character_count"] == len(
        "Payment shall be made within 30 days."
    )


def test_text_ingestion_rejects_empty_content():
    response = client.post(
        "/api/v1/ingestion/text",
        json={
            "input_type": "text",
            "content": "",
        },
    )

    assert response.status_code == 422


def test_clause_endpoints_return_404_for_unknown_file():
    file_id = "api-test-file-that-does-not-exist"

    endpoints = [
        f"/api/v1/clauses/{file_id}",
        f"/api/v1/clauses/{file_id}/analysis",
        f"/api/v1/clauses/{file_id}/relationships",
        f"/api/v1/clauses/{file_id}/summary",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Extracted document not found."
        )


def test_file_upload_endpoint():
    content = (
        b"1. Payment\n"
        b"The Customer shall pay the invoice within 30 days.\n\n"
        b"2. Termination\n"
        b"Either party may terminate this agreement upon written notice.\n"
    )

    response = client.post(
        "/api/v1/ingestion/file",
        files={
            "file": (
                "api_test_contract.txt",
                content,
                "text/plain",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["file_id"]
    assert data["filename"] == "api_test_contract.txt"
    assert data["file_type"] == "txt"
    assert data["size_bytes"] == len(content)
    assert data["character_count"] > 0
    assert "Payment" in data["extracted_text"]

    file_id = data["file_id"]

    extracted_path = (
        FileIngestionService.EXTRACTED_DIR
        / f"{file_id}.txt"
    )

    assert extracted_path.exists()

    uploaded_path = (
        FileIngestionService.UPLOAD_DIR
        / f"{file_id}.txt"
    )

    if uploaded_path.exists():
        uploaded_path.unlink()

    if extracted_path.exists():
        extracted_path.unlink()


def test_contract_analysis_pipeline():
    content = (
        b"1. Payment\n"
        b"The Customer shall pay 10,000 USD within 30 days.\n\n"
        b"2. Termination\n"
        b"Either party may terminate this agreement upon written notice.\n\n"
        b"3. Confidentiality\n"
        b"The receiving party shall keep all confidential information "
        b"strictly confidential.\n\n"
        b"4. Liability\n"
        b"The Customer shall have unlimited liability for all losses.\n"
    )

    upload_response = client.post(
        "/api/v1/ingestion/file",
        files={
            "file": (
                "pipeline_test_contract.txt",
                content,
                "text/plain",
            )
        },
    )

    assert upload_response.status_code == 200

    file_id = upload_response.json()["file_id"]

    try:
        # ----------------------------------------------------------
        # 1. Clause segmentation
        # ----------------------------------------------------------
        clauses_response = client.get(
            f"/api/v1/clauses/{file_id}"
        )

        assert clauses_response.status_code == 200

        clauses_data = clauses_response.json()

        assert clauses_data["file_id"] == file_id
        assert clauses_data["clause_count"] >= 4
        assert clauses_data["clauses"]

        # ----------------------------------------------------------
        # 2. Clause analysis
        # ----------------------------------------------------------
        analysis_response = client.get(
            f"/api/v1/clauses/{file_id}/analysis"
        )

        assert analysis_response.status_code == 200

        analysis_data = analysis_response.json()

        assert analysis_data["file_id"] == file_id
        assert analysis_data["analysis_count"] >= 4
        assert analysis_data["analyses"]

        # Verify risk analysis actually detects
        # the unlimited-liability clause.
        risk_levels = {
            analysis["risk_level"]
            for analysis in analysis_data["analyses"]
        }

        assert "HIGH" in risk_levels

        # ----------------------------------------------------------
        # 3. Clause relationships
        # ----------------------------------------------------------
        relationships_response = client.get(
            f"/api/v1/clauses/{file_id}/relationships"
        )

        assert relationships_response.status_code == 200

        relationships_data = relationships_response.json()

        assert relationships_data["file_id"] == file_id
        assert "relationship_count" in relationships_data
        assert "relationships" in relationships_data

        # ----------------------------------------------------------
        # 4. Contract summary
        # ----------------------------------------------------------
        summary_response = client.get(
            f"/api/v1/clauses/{file_id}/summary"
        )

        assert summary_response.status_code == 200

        summary_data = summary_response.json()

        assert summary_data["file_id"] == file_id
        assert summary_data["total_clauses"] >= 4

        assert summary_data["overall_risk"] in {
            "LOW",
            "MEDIUM",
            "HIGH",
        }

        assert summary_data["overall_risk"] == "HIGH"

        assert "risk_summary" in summary_data
        assert "summary_points" in summary_data

    finally:
        # ----------------------------------------------------------
        # Clean up uploaded/extracted files
        # ----------------------------------------------------------
        for directory in (
            FileIngestionService.UPLOAD_DIR,
            FileIngestionService.EXTRACTED_DIR,
        ):
            if directory.exists():
                for path in directory.glob(
                    f"{file_id}.*"
                ):
                    path.unlink()

        # ----------------------------------------------------------
        # Clean up stored clauses
        # ----------------------------------------------------------
        clauses_path = (
            Path("storage/clauses")
            / f"{file_id}.json"
        )

        if clauses_path.exists():
            clauses_path.unlink()