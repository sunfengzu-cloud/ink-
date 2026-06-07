class ReviewGenerator:
    def __init__(self, api_key=None, api_base=None, model=None):
        self.api_key = api_key
        self.api_base = api_base or "https://open.bigmodel.cn/api/paas/v4"
        self.model = model or "glm-4-flash"

    def generate(self, cards, use_llm=True):
        if use_llm and self.api_key:
            return self._llm_review(cards)
        return self._simple_review(cards)

    def _simple_review(self, cards):
        review_cards = []
        for card in cards:
            understanding = card.get("my_understanding", "")
            title = card.get("title", "")
            if not understanding or understanding.startswith("_"):
                continue

            sentences = [s.strip() for s in understanding.replace("。", ".").split(".") if s.strip()]
            if not sentences:
                continue

            key_sentence = sentences[0]
            review_cards.append({
                "question": f"请解释：{title}",
                "answer": understanding,
                "links": ", ".join(l if isinstance(l, str) else l.get("title", l) for l in card.get("links", []))
            })

            if len(sentences) > 1:
                import re
                words = re.findall(r"[\w\u4e00-\u9fff]+", key_sentence)
                if words:
                    import random
                    blank = random.choice(words)
                    fill_q = key_sentence.replace(blank, "____", 1) if blank in key_sentence else key_sentence
                    review_cards.append({
                        "question": f"填空：{fill_q}",
                        "answer": blank,
                        "links": title
                    })

        return review_cards

    def _llm_review(self, cards):
        import requests, json
        review_cards = []
        for card in cards:
            title = card.get("title", "")
            understanding = card.get("my_understanding", "")
            gaps = card.get("gaps", "")
            example = card.get("example", "")
            if not understanding or understanding.startswith("_"):
                continue

            prompt = f"""根据以下知识卡片，生成 2 道复习题：

1. 一道概念理解题（用自己的话解释）
2. 一道填空题（挖掉关键术语）

卡片标题：{title}
我的理解：{understanding}
盲区：{gaps}
例子：{example}

输出 JSON 格式：
[{{"type": "概念题", "question": "...", "answer": "..."}}, {{"type": "填空题", "question": "...", "answer": "..."}}]
"""
            try:
                resp = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"model": self.model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.4},
                    timeout=60
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                for item in parsed:
                    item["links"] = title
                    review_cards.append(item)
            except:
                pass

        return review_cards if review_cards else self._simple_review(cards)
