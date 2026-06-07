from pathlib import Path

class PdfIngestor:
    def ingest(self, pdf_path):
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        try:
            import fitz
        except ImportError:
            raise ImportError("PyMuPDF not installed. Run: pip install PyMuPDF")

        doc = fitz.open(str(pdf_path))
        result = {
            "title": pdf_path.stem,
            "source": str(pdf_path),
            "type": "pdf",
            "segments": [],
            "pages": len(doc)
        }

        for page_num, page in enumerate(doc):
            text = page.get_text().strip()
            if text:
                result["segments"].append({
                    "start": f"p{page_num + 1}",
                    "end": f"p{page_num + 1}",
                    "text": text,
                    "page": page_num + 1
                })

        doc.close()
        return result
