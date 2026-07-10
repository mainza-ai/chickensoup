from unittest.mock import patch, MagicMock
import src.main

from src.wiki.pdf_extract import extract_text_from_pdf, copy_pdf_to_raw


def _make_pdf(path: str, pages: int = 1):
    """Create a minimal valid PDF file at `path` with `pages` pages of extractable text."""
    from pypdf import PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    import io as _io

    packet = _io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    for i in range(pages):
        can.drawString(72, 720, f"Test PDF page {i + 1} — quantum cryptography research abstract.")
        can.showPage()
    can.save()
    packet.seek(0)
    reader_pkg = __import__("pypdf").PdfReader(packet)
    writer = PdfWriter()
    for page in reader_pkg.pages:
        writer.add_page(page)
    with open(path, "wb") as f:
        writer.write(f)


def test_extract_text_from_pdf(tmp_path):
    pdf = tmp_path / "hello.pdf"
    _make_pdf(str(pdf))
    text = extract_text_from_pdf(str(pdf))
    assert isinstance(text, str)
    assert len(text) > 0


def _make_blank_pdf(path: str, pages: int = 1):
    """Create a minimal valid PDF with blank pages (simulates scanned/image PDF)."""
    from pypdf import PdfWriter
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=72, height=72)
    with open(path, "wb") as f:
        writer.write(f)


def test_copy_pdf_to_raw_idempotent(tmp_path, monkeypatch):
    # Use a temp dir as the project root so WIKI_DIR resolves via settings
    pdf = tmp_path / "my-paper.pdf"
    _make_pdf(str(pdf))

    # Patch settings.WIKI_DATA_DIR to a temp location
    import src.config
    raw_target = tmp_path / "wiki_raw"
    raw_target.mkdir()
    monkeypatch.setattr(src.config.settings, "WIKI_DATA_DIR", str(raw_target))

    rel = copy_pdf_to_raw(str(pdf), "my-paper")
    assert rel is not None
    assert (raw_target / "raw" / "my-paper.pdf").exists()

    # Second call should skip copy (idempotent)
    rel2 = copy_pdf_to_raw(str(pdf), "my-paper")
    assert rel2 == rel


def test_pdf_folder_dry_run(client, tmp_path, monkeypatch):
    pdf = tmp_path / "test-paper.pdf"
    _make_pdf(str(pdf))

    mock_analysis = MagicMock()
    mock_page = MagicMock()
    mock_page.confidence = 0.9
    mock_page.page_type = "concepts"
    mock_page.title = "Test Concept"
    mock_page.body = "# Test Concept"
    mock_page.tags = ["test"]
    mock_page.sources = ["test-paper.pdf"]
    mock_page.related = []
    mock_analysis.suggested_pages = [mock_page]
    mock_analysis.confidence = 0.9

    with patch.object(src.main.ingest_agent, "analyze_content", return_value=mock_analysis), \
            patch("src.main.write_page") as mock_write, \
            patch("src.main.cross_reference_new_page"):
        response = client.post(
            "/ingest/pdf-folder",
            json={"folder_path": str(tmp_path), "dry_run": True, "skip_neo4j": True},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dry_run"] is True
    assert data["neo4j_bulk_triggered"] is False
    mock_write.assert_not_called()
    assert data["pdfs_processed"] == 1


def test_pdf_folder_ingest_writes_pages(client, tmp_path, monkeypatch):
    pdf = tmp_path / "test-paper.pdf"
    _make_pdf(str(pdf))

    mock_analysis = MagicMock()
    mock_page = MagicMock()
    mock_page.confidence = 0.9
    mock_page.page_type = "concepts"
    mock_page.title = "Written Concept"
    mock_page.body = "# Body"
    mock_page.tags = ["test"]
    mock_page.sources = ["test-paper.pdf"]
    mock_page.related = []
    mock_analysis.suggested_pages = [mock_page]
    mock_analysis.confidence = 0.9

    import src.main as _main_mod

    def _fake_analyze(text, filename=None):
        return mock_analysis

    with patch.object(_main_mod.ingest_agent, "analyze_content", side_effect=_fake_analyze), \
            patch("src.main.write_page", return_value=("written-concept", True)) as mock_write, \
            patch("src.main.cross_reference_new_page"):
        response = client.post(
            "/ingest/pdf-folder",
            json={"folder_path": str(tmp_path), "dry_run": False, "skip_neo4j": True},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["dry_run"] is False
    assert "Written Concept" in data["pages_created"], f"Got: {data['pages_created']}"
    assert mock_write.call_count >= 1


def test_pdf_folder_skips_scanned_pdfs(client, tmp_path, monkeypatch):
    # Create a PDF that pypdf will return empty text for (blank page — simulates scanned/image PDF)
    pdf = tmp_path / "scanned.pdf"
    _make_blank_pdf(str(pdf))

    response = client.post(
        "/ingest/pdf-folder",
        json={"folder_path": str(tmp_path), "dry_run": False, "skip_neo4j": True},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["failed_files"]) == 1
    assert data["failed_files"][0]["filename"] == "scanned.pdf"
