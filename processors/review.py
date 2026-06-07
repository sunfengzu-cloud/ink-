class ReviewGenerator:
    def __init__(self, api_key=None, api_base=None, model=None):
        self.api_key = api_key
        self.api_base = api_base or "https://open.bigmodel.cn/api/paas/v4"
        self.model = model or "glm-4-flash"

    def generate_from_sections(self, sections, use_llm=True):
        if use_llm and self.api_key:
            return self._llm_review(sections)
        return self._simple_review(sections)

    def _simple_review(self, sections):
        review_cards = []
        for sec in sections:
            content = sec.get("content", "")
            title = sec.get("title", "")
            if not content or content.startswith("_"):
                continue

            sentences = [s.strip() for s in content.replace("。", ".").split(".") if s.strip()]
            if not sentences:
                continue

            key_sentence = next((s for s in sentences if len(s) > 15), sentences[0])
            review_cards.append({
                "question": f"请讲解：{title}",
                "answer": content[:500],
                "links": title
            })

            import re, random
            words = re.findall(r"[\w\u4e00-\u9fff]+", key_sentence)
            if len(words) >= 3:
                blank = random.choice([w for w in words if len(w) >= 2])
                if blank in key_sentence:
                    fill_q = key_sentence.replace(blank, "____", 1)
                    review_cards.append({
                        "question": f"填空：{fill_q}",
                        "answer": blank,
                        "links": title
                    })

        return review_cards

    def _llm_review(self, sections):
        import requests, json
        review_cards = []
        for sec in sections:
            title = sec.get("title", "")
            content = sec.get("content", "")
            if not content or content.startswith("_"):
                continue

            prompt = f"""根据以下课程笔记，生成 2 道复习题：

1. 一道概念理解题
2. 一道填空题（挖掉关键术语）

章节标题：{title}
笔记内容：{content[:600]}

输出 JSON 格式（不要代码块，纯 JSON）：
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
                content = content.strip().removeprefix("```json").removesuffix("```").strip()
                parsed = json.loads(content)
                for item in parsed:
                    item["links"] = title
                    review_cards.append(item)
            except:
                pass

        return review_cards if review_cards else self._simple_review(sections)
