from pathlib import Path
from ingestors import get_ingestor
from processors import Chunker, CardGenerator, Linker
from output import ObsidianWriter
from config import METHODOLOGY, DEFAULT_OUTPUT

class Pipeline:
    def __init__(self, api_key=None, api_base=None, model=None, output_dir=None):
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.output_dir = Path(output_dir or DEFAULT_OUTPUT)
        self.active_cards = []
        self._load_existing_cards()

    def run(self, source_path, source_type=None, subtitle_path=None, use_llm=True):
        source_path = Path(source_path)
        if not source_type:
            source_type = self._detect_type(source_path)

        ingestor = get_ingestor(source_type)
        print(f"[ink] Ingesting: {source_path}")
        raw = ingestor.ingest(source_path)

        if source_type == "folder":
            results = []
            for child in raw["children"]:
                results.append(self._process_single(child, use_llm))
            return results
        else:
            return [self._process_single(raw, use_llm)]

    def _process_single(self, raw, use_llm):
        title = raw.get("title", "untitled")
        segments = raw.get("segments", [])
        screenshots = raw.get("screenshots")

        if not segments:
            print(f"[ink] No content found in: {title}")
            return {"title": title, "status": "skipped", "reason": "no content"}

        chunker = Chunker(self.api_key, self.api_base, self.model)
        concepts = chunker.chunk(segments, title, use_llm=use_llm)
        print(f"[ink] Chunked into {len(concepts)} concept(s)")

        gen = CardGenerator(self.api_key, self.api_base, self.model)
        cards = gen.generate(concepts, raw)
        print(f"[ink] Generated {len(cards)} card(s)")

        linker = Linker(self.api_key, self.api_base, self.model)
        for card in cards:
            links = linker.link(card, self.active_cards)
            if links:
                existing_links = card.get("links", [])
                existing_titles = {l if isinstance(l, str) else l.get("title", l) for l in existing_links}
                for link in links:
                    link_title = link if isinstance(link, str) else link.get("title", "")
                    if link_title and link_title not in existing_titles:
                        existing_links.append(link)
                card["links"] = existing_links
            self.active_cards.append(card)
        print(f"[ink] Linked cards")

        writer = ObsidianWriter(self.output_dir)
        vault_path = writer.write(cards, raw, screenshots)
        print(f"[ink] Written to: {vault_path}")

        return {"title": title, "status": "done", "cards": len(cards), "path": vault_path}

    def _detect_type(self, source_path):
        if source_path.is_dir():
            return "folder"
        ext = source_path.suffix.lower()
        if ext in (".mp4", ".mkv", ".webm"):
            return "video"
        elif ext == ".pdf":
            return "pdf"
        elif ext in (".md", ".txt", ".markdown"):
            return "markdown"
        return "markdown"

    def _load_existing_cards(self):
        if self.output_dir.exists():
            for card_file in self.output_dir.rglob("cards/*.md"):
                try:
                    content = card_file.read_text(encoding="utf-8")
                    title = card_file.stem
                    understanding = ""
                    gaps = ""
                    quote = ""
                    links = []
                    current_section = None
                    for line in content.split("\n"):
                        if line.strip() == "## 📝 我的理解":
                            current_section = "understanding"
                            continue
                        elif line.strip() == "## ❓ 还不太清楚":
                            current_section = "gaps"
                            continue
                        elif line.strip() == "## 📺 原文":
                            current_section = "quote"
                            continue
                        elif line.startswith("## 🔗"):
                            current_section = "links"
                            continue
                        elif line.startswith("##"):
                            current_section = None

                        if current_section == "understanding" and line.strip() and not line.startswith("_"):
                            understanding += line.strip() + " "
                        elif current_section == "gaps" and line.strip() and not line.startswith("_"):
                            gaps += line.strip() + " "
                        elif current_section == "quote" and line.strip().startswith("> "):
                            quote += line.strip()[2:] + " "
                        elif current_section == "links":
                            for match in __import__("re").findall(r"\[\[(.+?)\]\]", line):
                                links.append(match)

                    self.active_cards.append({
                        "title": title,
                        "my_understanding": understanding.strip(),
                        "gaps": gaps.strip(),
                        "original_quote": quote.strip(),
                        "links": links
                    })
                except:
                    pass
