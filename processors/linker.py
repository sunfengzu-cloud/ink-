from pathlib import Path

class Linker:
    def __init__(self, api_key=None, api_base=None, model=None):
        self.api_key = api_key
        self.api_base = api_base or "https://open.bigmodel.cn/api/paas/v4"
        self.model = model or "glm-4-flash"

    def link(self, new_card, existing_cards):
        if not existing_cards:
            return []

        if not self.api_key:
            return self._simple_link(new_card, existing_cards)

        return self._llm_link(new_card, existing_cards)

    def _simple_link(self, new_card, existing_cards):
        links = []
        new_title = new_card.get("title", "").lower()
        new_text = (new_card.get("my_understanding", "") + " " +
                    new_card.get("original_quote", "")).lower()
        new_words = set(new_text.split())

        for card in existing_cards:
            title = card.get("title", "")
            card_text = (card.get("my_understanding", "") + " " +
                         card.get("original_quote", "")).lower()
            overlap = len(new_words & set(card_text.split()))
            if overlap > 5:
                links.append({
                    "title": title,
                    "reason": f"共享 {overlap} 个关键词"
                })

        return links[:3]

    def _llm_link(self, new_card, existing_cards):
        prompt_path = Path(__file__).parent.parent / "methodology" / "prompts" / "link.txt"
        prompt_template = prompt_path.read_text(encoding="utf-8")

        existing_summary = "\n".join(
            f"- {c.get('title', '')}: {c.get('my_understanding', '')[:100]}"
            for c in existing_cards
        )

        prompt = prompt_template.format(
            title=new_card.get("title", ""),
            content=new_card.get("my_understanding", "")[:300],
            existing_cards=existing_summary
        )

        try:
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
                headers=headers, json=payload, timeout=60
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]

            import yaml
            parsed = yaml.safe_load(content)
            if isinstance(parsed, dict) and "links" in parsed:
                return parsed["links"]
        except:
            pass

        return []
