import json
import re
from pathlib import Path

class Chunker:
    def __init__(self, api_key=None, api_base=None, model=None):
        self.api_key = api_key
        self.api_base = api_base or "https://open.bigmodel.cn/api/paas/v4"
        self.model = model or "glm-4-flash"

    def chunk(self, segments, source_title, use_llm=True):
        if not use_llm or not self.api_key:
            return self._simple_chunk(segments, source_title)
        return self._llm_chunk(segments, source_title)

    def _simple_chunk(self, segments, source_title):
        concepts = []
        current = {"title": source_title, "start": "", "end": "", "texts": []}

        for seg in segments:
            if not current["start"]:
                current["start"] = seg["start"]
            current["texts"].append(seg["text"])
            text = seg["text"]
            if text.rstrip().endswith((".", "!", "?", "。", "！", "？")):
                current["end"] = seg["end"]
                current["full_text"] = " ".join(current["texts"])
                current["segment_count"] = len(current["texts"])
                concepts.append(current)
                current = {"title": source_title, "start": "", "end": "", "texts": []}

        if current["texts"]:
            current["end"] = segments[-1]["end"]
            current["full_text"] = " ".join(current["texts"])
            current["segment_count"] = len(current["texts"])
            concepts.append(current)

        for i, c in enumerate(concepts):
            if len(concepts) > 1:
                c["title"] = f"{source_title} - 概念{i+1}"

        return concepts

    def _llm_chunk(self, segments, source_title):
        prompt_path = Path(__file__).parent.parent / "methodology" / "prompts" / "chunk.txt"
        prompt_template = prompt_path.read_text(encoding="utf-8")

        full_text = "\n".join(
            f"[{seg['start']} --> {seg['end']}] {seg['text']}"
            for seg in segments
        )

        prompt = prompt_template + "\n" + full_text
        response = self._call_llm(prompt)
        return self._parse_chunk_response(response, segments)

    def _call_llm(self, prompt):
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        resp = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _parse_chunk_response(self, response, segments):
        try:
            import yaml
            parsed = yaml.safe_load(response)
            if isinstance(parsed, list):
                return parsed
        except:
            pass

        concepts = []
        blocks = re.split(r"\n(?=\d+\.\s|\-\s)", response.strip())
        for block in blocks:
            if not block.strip():
                continue
            concepts.append({
                "title": block.strip()[:60],
                "text": block.strip()
            })
        return concepts if concepts else [{"title": source_title, "text": " ".join(s["text"] for s in segments)}]
