from pathlib import Path
from ingestors.video import VideoIngestor
from ingestors.pdf import PdfIngestor
from ingestors.markdown import MarkdownIngestor

SUPPORTED_EXTS = {
    ".mp4": VideoIngestor, ".mkv": VideoIngestor, ".webm": VideoIngestor,
    ".pdf": PdfIngestor,
    ".md": MarkdownIngestor, ".txt": MarkdownIngestor, ".markdown": MarkdownIngestor
}

SUBTITLE_EXTS = {".vtt", ".srt"}

class FolderIngestor:
    def ingest(self, folder_path):
        folder_path = Path(folder_path)
        if not folder_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {folder_path}")

        result = {
            "title": folder_path.stem,
            "source": str(folder_path),
            "type": "folder",
            "children": [],
            "total_segments": 0
        }

        files = sorted(f for f in folder_path.iterdir() if f.is_file())

        for f in files:
            ext = f.suffix.lower()
            if ext in SUBTITLE_EXTS:
                continue
            source_type = SUPPORTED_EXTS.get(ext)
            if not source_type:
                continue

            sub_path = self._find_subtitle(folder_path, f, files)
            ingestor = source_type()
            try:
                child = ingestor.ingest(f)
                if sub_path:
                    child["segments"] = ingestor._parse_subtitle(sub_path)
                result["children"].append(child)
                result["total_segments"] += len(child["segments"])
            except Exception as e:
                result["children"].append({
                    "title": f.stem,
                    "source": str(f),
                    "type": source_type,
                    "error": str(e)
                })

        return result

    def _find_subtitle(self, folder_path, video_file, all_files):
        stem = video_file.stem
        for sub_ext in (".vtt", ".srt"):
            candidates = [
                folder_path / f"{stem}{sub_ext}",
                folder_path / f"{stem}.zh{sub_ext}",
                folder_path / f"{stem}.en{sub_ext}",
            ]
            for c in candidates:
                if c.exists():
                    return c
        return None
