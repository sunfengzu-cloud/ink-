from .video import VideoIngestor
from .pdf import PdfIngestor
from .markdown import MarkdownIngestor
from .folder import FolderIngestor

INGESTORS = {
    "video": VideoIngestor,
    "pdf": PdfIngestor,
    "markdown": MarkdownIngestor,
    "folder": FolderIngestor,
}

def get_ingestor(source_type):
    cls = INGESTORS.get(source_type)
    if not cls:
        raise ValueError(f"Unknown source type: {source_type}, choose from {list(INGESTORS.keys())}")
    return cls()
