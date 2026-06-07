from pathlib import Path

class MarkdownIngestor:
    def ingest(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = file_path.read_text(encoding="utf-8")
        lines = content.split("\n")

        segments = []
        current_section = {"start": 0, "text": ""}

        for i, line in enumerate(lines):
            if line.startswith("#"):
                if current_section["text"].strip():
                    current_section["end"] = i
                    segments.append(current_section)
                current_section = {"start": i, "text": line + "\n"}
            else:
                current_section["text"] += line + "\n"

        if current_section["text"].strip():
            current_section["end"] = len(lines)
            segments.append(current_section)

        return {
            "title": file_path.stem,
            "source": str(file_path),
            "type": "markdown",
            "segments": [{
                "start": f"L{s['start']+1}",
                "end": f"L{s.get('end', s['start']+1)}",
                "text": s["text"].strip()
            } for s in segments if s["text"].strip()],
            "line_count": len(lines)
        }
