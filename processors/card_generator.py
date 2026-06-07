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
        cards = []
        for concept in concepts:
            if self.api_key:
                card = self._llm_card(concept, source_info)
            else:
                card = self._template_card(concept, source_info)
            cards.append(card)
        return cards

    def _llm_card(self, concept, source_info):
        prompt_path = Path(__file__).parent.parent / "methodology" / "prompts" / "card.txt"
        prompt_template = prompt_path.read_text(encoding="utf-8")

        segment_text = concept.get("full_text") or concept.get("text", "")
        if isinstance(segment_text, list):
            segment_text = " ".join(segment_text)

        prompt = f"{prompt_template}\n\n{segment_text}"
        response = self._call_llm(prompt)
        return self._parse_card_response(response, concept, source_info)

    def _call_llm(self, prompt):
        import requests
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5
        }
        resp = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers, json=payload, timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def _parse_card_response(self, response, concept, source_info):
        parsed = self._try_parse_json(response) or self._try_parse_yaml(response)
        if parsed and isinstance(parsed, dict):
            card = parsed
            card.setdefault("title", concept.get("title", "Untitled"))
            card.setdefault("original_quote", concept.get("text", "")[:200] if isinstance(concept.get("text"), str) else " ".join(concept.get("texts", []))[:200])
            card.setdefault("my_understanding", "")
            card.setdefault("gaps", "")
            card.setdefault("links", [])
            card.setdefault("example", "")
            card.setdefault("thinking_questions", [])
            card["source"] = source_info.get("source", "")
            card["created"] = datetime.now().strftime("%Y-%m-%d")
            return card

        return {
            "title": concept.get("title", "Untitled"),
            "source": source_info.get("source", ""),
            "original_quote": (concept.get("text", "")[:200] if isinstance(concept.get("text"), str)
                               else " ".join(concept.get("texts", []))[:200]),
            "my_understanding": "",
            "gaps": "",
            "links": [],
            "example": "",
            "thinking_questions": [],
            "created": datetime.now().strftime("%Y-%m-%d")
        }

    def _try_parse_json(self, text):
        import re, json
        # Strip code fences
        text = re.sub(r"^```(?:json)?\n?|```$", "", text.strip(), flags=re.MULTILINE)
        # Try direct parse
        try:
            return json.loads(text)
        except:
            pass
        # Try find first { ... } block
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except:
                pass
        return None

    def _try_parse_yaml(self, text):
        import re, yaml
        text = re.sub(r"^```(?:yaml)?\n?|```$", "", text.strip(), flags=re.MULTILINE)
        try:
            parsed = yaml.safe_load(text)
            if isinstance(parsed, dict):
                return parsed
        except:
            pass
        return None

    def _template_card(self, concept, source_info):
        return {
            "title": concept.get("title", "Untitled"),
            "source": source_info.get("source", ""),
            "original_quote": (concept.get("full_text", "") or
                               concept.get("text", "") or
                               " ".join(concept.get("texts", []))),
            "my_understanding": "_Write your understanding here_",
            "gaps": "_What's still unclear?_",
            "links": [],
            "example": "_Add a concrete example_",
            "thinking_questions": ["_Reflect: why does this matter?_"],
            "created": datetime.now().strftime("%Y-%m-%d")
        }
