import yaml
from pathlib import Path

METHODOLOGY = {
    "capture_rules": {
        "no_complete_sentences": True,
        "max_keywords_per_minute": 5,
        "mark_unclear_with": "[!]",
        "mark_connection_with": "→",
        "mark_question_with": "?"
    },
    "card_rules": {
        "one_concept_per_card": True,
        "always_include_source": True,
        "no_copy_paste": True,
        "always_link_at_least": 1,
        "max_card_length_chars": 2000
    },
    "review_rules": {
        "random_cards_per_session": 5,
        "schedule_hours": 24,
        "orphan_check_enabled": True,
        "stuck_mark": "#needs-review"
    }
}

TEMPLATES = {
    "concept": """\
# {title}

> 📺 **Source**: {source}

## Original
> {original_quote}

## My Understanding
{my_understanding}

## Knowledge Gaps
{gaps}

## Connections
{links}

## Example
{example}
""",
    "question": """\
# 🤔 {title}

## Question
{question}

## Context
{context}

## My Current Answer
{my_answer}

## Still Unsure
{unsure}
""",
    "reference": """\
# 📚 {title}

**Source**: {source}

## Key Points
{key_points}

## Why It Matters
{significance}

## Related
{links}
"""
}

DEFAULT_OUTPUT = "learn-notes"

PROMPT_DIR = Path(__file__).parent / "methodology" / "prompts"
CONFIG_DIR = Path(__file__).parent / "methodology"
