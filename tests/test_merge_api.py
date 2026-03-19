"""
Integration tests for the /v1/merge endpoint.

Happy-path success tests mock is_pdfa3b() and get_xml_from_pdf() because the test
corpus does not contain a PDF/A-3b file without embedded XML (all corpus PDF/A-3b
files are already Factur-X). Error-path tests use real corpus files.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

CORPUS = "tests/corpus/valid"

# Fixtures loaded once at module level
with open(f"{CORPUS}/EN16931_Einfach.xml", "rb") as f:
    VALID_XML = f.read()

with open(f"{CORPUS}/xrechnung_3.0_standard.xml", "rb") as f:
    XRECHNUNG_XML = f.read()

# Already a Factur-X PDF (has embedded XML) → triggers 409
with open(f"{CORPUS}/Facture_FR_MINIMUM.pdf", "rb") as f:
    FACTURX_PDF = f.read()

# Plain PDF without XMP metadata → triggers 422 (not PDF/A-3b)
with open(f"{CORPUS}/bare_invoice.pdf", "rb") as f:
    BARE_PDF = f.read()


# ── Error-path tests (real corpus files, no mocking) ───────────────────────

class TestMergeErrors:

    def test_merge_bad_pdf_magic(self):
        """400 when first file is not a real PDF."""
        response = client.post(
            "/v1/merge",
            files={
                "pdf": ("bad.pdf", b"this is not a pdf", "application/pdf"),
                "xml": ("factur-x.xml", VALID_XML, "application/xml"),
            },
        )
        assert response.status_code == 400
        assert "invalid_file_type" in response.json().get("type", "")

    def test_merge_bad_xml_magic(self):
        """400 when second file is not XML."""
        response = client.post(
            "/v1/merge",
            files={
                "pdf": ("invoice.pdf", BARE_PDF, "application/pdf"),
                "xml": ("not_xml.xml", b"this is not xml content", "application/xml"),
            },
        )
        assert response.status_code == 400
        assert "invalid_file_type" in response.json().get("type", "")

    def test_merge_pdf_already_facturx(self):
        """409 when PDF already contains embedded Factur-X XML."""
        response = client.post(
            "/v1/merge",
            files={
                "pdf": ("invoice.pdf", FACTURX_PDF, "application/pdf"),
                "xml": ("factur-x.xml", VALID_XML, "application/xml"),
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert "already_facturx" in data.get("type", "")

    def test_merge_non_pdfa3_input(self):
        """422 when PDF has no PDF/A-3b XMP declaration."""
        response = client.post(
            "/v1/merge",
            files={
                "pdf": ("invoice.pdf", BARE_PDF, "application/pdf"),
                "xml": ("factur-x.xml", VALID_XML, "application/xml"),
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert "not_pdfa3" in data.get("type", "")

    def test_merge_xml_wrong_namespace(self):
        """422 when XML has an unknown namespace (fails EN16931 validation)."""
        bad_xml = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<Invoice xmlns="http://unknown.example.com/ns/invoice">'
            b"<ID>FAKE-001</ID></Invoice>"
        )
        with patch("app.api.is_pdfa3b", return_value=True), \
             patch("app.api.get_xml_from_pdf", return_value=(None, None)):
            response = client.post(
                "/v1/merge",
                files={
                    "pdf": ("invoice.pdf", BARE_PDF, "application/pdf"),
                    "xml": ("bad.xml", bad_xml, "application/xml"),
                },
            )
        assert response.status_code == 422

    def test_merge_oversized_file(self):
        """413 when Content-Length exceeds the middleware limit."""
        big_size = 25 * 1024 * 1024
        response = client.post(
            "/v1/merge",
            headers={"Content-Length": str(big_size)},
            data=b"not big",
        )
        assert response.status_code == 413
        assert "File too large" in response.text


# ── Success-path tests (mock PDF/A-3b check + existing XML check) ────────────

class TestMergeSuccess:
    """
    Mocks is_pdfa3b → True and get_xml_from_pdf → (None, None) so that
    bare_invoice.pdf (a plain PDF without PDF/A metadata) can pass the gate checks.
    This lets us exercise the actual XML validation and embed logic with Saxon/XSD.
    """

    @patch("app.api.is_pdfa3b", return_value=True)
    @patch("app.api.get_xml_from_pdf", return_value=(None, None))
    def test_merge_success_with_valid_xml(self, _mock_get, _mock_pdfa3b):
        """200 — returns PDF with X-Facturx-Format and X-Facturx-Profile headers."""
        response = client.post(
            "/v1/merge",
            files={
                "pdf": ("invoice.pdf", BARE_PDF, "application/pdf"),
                "xml": ("factur-x.xml", VALID_XML, "application/xml"),
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content[:5] == b"%PDF-"
        assert "X-Facturx-Format" in response.headers
        assert "X-Facturx-Profile" in response.headers

    @patch("app.api.is_pdfa3b", return_value=True)
    @patch("app.api.get_xml_from_pdf", return_value=(None, None))
    def test_merge_xrechnung_xml(self, _mock_get, _mock_pdfa3b):
        """200 — XRechnung 3.0 CII XML is correctly detected and embedded."""
        response = client.post(
            "/v1/merge",
            files={
                "pdf": ("invoice.pdf", BARE_PDF, "application/pdf"),
                "xml": ("xrechnung.xml", XRECHNUNG_XML, "application/xml"),
            },
        )
        assert response.status_code == 200
        assert response.content[:5] == b"%PDF-"

    @patch("app.api.is_pdfa3b", return_value=True)
    @patch("app.api.get_xml_from_pdf", return_value=(None, None))
    def test_merge_content_disposition_header(self, _mock_get, _mock_pdfa3b):
        """Response includes a Content-Disposition attachment header."""
        response = client.post(
            "/v1/merge",
            files={
                "pdf": ("invoice.pdf", BARE_PDF, "application/pdf"),
                "xml": ("factur-x.xml", VALID_XML, "application/xml"),
            },
        )
        assert response.status_code == 200
        cd = response.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert "facturx_merged.pdf" in cd


# ── Unit tests for is_pdfa3b ────────────────────────────────────────────────

class TestIsPdfa3b:
    """Unit tests for the is_pdfa3b() heuristic helper."""

    def test_facturx_pdf_is_pdfa3b(self):
        """A genuine Factur-X PDF declares PDF/A-3b in its XMP metadata."""
        from app.services.pdf_utils import is_pdfa3b
        assert is_pdfa3b(FACTURX_PDF) is True

    def test_bare_pdf_is_not_pdfa3b(self):
        """A plain PDF without XMP metadata is not PDF/A-3b."""
        from app.services.pdf_utils import is_pdfa3b
        assert is_pdfa3b(BARE_PDF) is False

    def test_garbage_bytes_return_false(self):
        """Random bytes should never raise — returns False."""
        from app.services.pdf_utils import is_pdfa3b
        assert is_pdfa3b(b"not a pdf at all \x00\x01\x02") is False
