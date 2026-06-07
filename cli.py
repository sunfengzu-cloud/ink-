#!/usr/bin/env python3
import argparse
import os
from pathlib import Path
from pipeline import Pipeline

def main():
    parser = argparse.ArgumentParser(
        description="ink - Ingest knowledge into structured notes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  ink video lesson.mp4 --sub lesson.vtt
  ink paper.pdf
  ink notes/ --output my-vault
  ink video.mp4 --api-key YOUR_KEY --no-llm
"""
    )
    parser.add_argument("source", help="Path to video, PDF, markdown file, or folder")
    parser.add_argument("--sub", help="Subtitle file (SRT/VTT) for videos")
    parser.add_argument("--type", choices=["video", "pdf", "markdown", "folder"],
                        help="Force source type (auto-detect by default)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output directory for Obsidian vault")
    parser.add_argument("--api-key", default=None,
                        help="LLM API key (or set INK_API_KEY env var)")
    parser.add_argument("--api-base", default=None,
                        help="LLM API base URL")
    parser.add_argument("--model", default="glm-4-flash",
                        help="LLM model name")
    parser.add_argument("--no-llm", action="store_true",
                        help="Skip LLM processing, use template cards only")

    args = parser.parse_args()
    api_key = args.api_key or os.environ.get("INK_API_KEY")

    pipe = Pipeline(api_key=api_key, api_base=args.api_base,
                    model=args.model, output_dir=args.output)
    results = pipe.run(args.source, source_type=args.type,
                       subtitle_path=args.sub, use_llm=not args.no_llm)

    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for r in results:
        status = "[OK]" if r["status"] == "done" else "[!]"
        print(f"{status} {r.get('title')}: {r.get('status')} ({r.get('cards', 0)} cards)")

if __name__ == "__main__":
    main()
