import json
import re
from pathlib import Path
from datetime import datetime

class CardGenerator:
    def __init__(self, api_key=None, api_base=None, model=None):
        self.api_key = api_key
        self.api_base = api_base or "https://open.bigmodel.cn/api/paas/v4"
        self.model = model or "glm-4-flash"

    def generate(self, concepts, source_info):
        sections = []
        for i, concept in enumerate(concepts):
            if self.api_key:
                sec = self._llm_section(concept, source_info, i + 1)
            else:
                sec = self._template_section(concept, i + 1)
            sections.append(sec)
        return sections

    def _llm_section(self, concept, source_info, index):
        prompt_path = Path(__file__).parent.parent / "methodology" / "prompts" / "card.txt"
        prompt_template = prompt_path.read_text(encoding="utf-8")

        segment_text = concept.get("full_text") or concept.get("text", "")
        if isinstance(segment_text, list):
            segment_text = " ".join(segment_text)

        prompt = f"{prompt_template}\n\n{segment_text}"
        response = self._call_llm(prompt)
        return self._parse_section(response, concept, source_info, index)

    def _call_llm(self, prompt):
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4
        }
        resp = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _parse_section(self, response, concept, source_info, index):
        response = response.strip()
        title = concept.get("title", f"第{index}部分")

        heading_line = response.split("\n")[0].strip()
        if heading_line.startswith("#"):
            title = heading_line.lstrip("#").strip()
            body = "\n".join(response.split("\n")[1:]).strip()
        elif heading_line.startswith(("##", "##")):
            title = heading_line.lstrip("#").strip()
            body = "\n".join(response.split("\n")[1:]).strip()
        else:
            body = response

        return {
            "title": title,
            "content": body,
            "source": source_info.get("source", ""),
            "created": datetime.now().strftime("%Y-%m-%d"),
            "start": concept.get("start", ""),
            "end": concept.get("end", ""),
            "index": index
        }

    def _template_section(self, concept, index):
        text = concept.get("full_text") or concept.get("text", "")
        if isinstance(text, list):
            text = " ".join(text)
        return {
            "title": concept.get("title", f"第{index}部分"),
            "content": f"_{text}_\n\n写你的理解...",
            "source": "",
            "created": datetime.now().strftime("%Y-%m-%d"),
            "start": concept.get("start", ""),
            "end": concept.get("end", ""),
            "index": index
        }

    def combine_to_document(self, sections, title):
        lines = [f"# {title}", "", f"来源: {sections[0]['source'] if sections else ''}", "---", ""]
        for sec in sections:
            ts = f"`[{sec['start']} → {sec['end']}]`" if sec.get("start") else ""
            lines.append(f"## {sec['title']} {ts}".strip())
            lines.append("")
            lines.append(sec["content"])
            lines.append("")
            lines.append("---")
            lines.append("")
        return "\n".join(lines)
