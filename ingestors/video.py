import re
import subprocess
import tempfile
from pathlib import Path

class VideoIngestor:
    def ingest(self, video_path, subtitle_path=None):
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        result = {
            "title": video_path.stem,
            "source": str(video_path),
            "type": "video",
            "segments": [],
            "screenshots": []
        }

        if subtitle_path:
            subtitle_path = Path(subtitle_path)
            if not subtitle_path.exists():
                raise FileNotFoundError(f"Subtitle not found: {subtitle_path}")
            result["segments"] = self._parse_subtitle(subtitle_path)
            result["duration"] = self._get_duration(video_path)
            result["screenshots"] = self._extract_keyframes(video_path, result["segments"])

        return result

    def _parse_subtitle(self, sub_path):
        ext = sub_path.suffix.lower()
        content = sub_path.read_text(encoding="utf-8")
        if ext == ".vtt":
            return self._parse_vtt(content)
        elif ext == ".srt":
            return self._parse_srt(content)
        else:
            raise ValueError(f"Unsupported subtitle format: {ext}")

    def _parse_vtt(self, content):
        segments = []
        block_pattern = re.compile(
            r"(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})\s*\n(.+?)(?=\n\n|\Z)",
            re.DOTALL
        )
        for m in block_pattern.finditer(content):
            text = m.group(3).strip()
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\n+", " ", text)
            if text:
                segments.append({
                    "start": m.group(1),
                    "end": m.group(2),
                    "text": text
                })
        return segments

    def _parse_srt(self, content):
        segments = []
        block_pattern = re.compile(
            r"\d+\n(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})\s*\n(.+?)(?=\n\n|\Z)",
            re.DOTALL
        )
        for m in block_pattern.finditer(content):
            text = m.group(3).strip()
            text = re.sub(r"<[^>]+>", "", text)
            text = re.sub(r"\n+", " ", text)
            if text:
                segments.append({
                    "start": m.group(1).replace(",", "."),
                    "end": m.group(2).replace(",", "."),
                    "text": text
                })
        return segments

    def _get_duration(self, video_path):
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            str(video_path)
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return float(result.stdout.strip())
        except:
            return 0

    def _extract_keyframes(self, video_path, segments, max_frames=10):
        if not segments:
            return []
        screenshots = []
        interval = max(1, len(segments) // max_frames)
        for i, seg in enumerate(segments[::interval]):
            if len(screenshots) >= max_frames:
                break
            ts = seg["start"]
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                out_path = tmp.name
            cmd = [
                "ffmpeg", "-y", "-ss", ts,
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                out_path
            ]
            try:
                subprocess.run(cmd, capture_output=True, timeout=30)
                screenshots.append({
                    "timestamp": ts,
                    "path": out_path,
                    "caption": seg["text"][:80]
                })
            except:
                pass
        return screenshots
