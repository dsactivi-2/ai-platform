#!/usr/bin/env python3
"""
Export skills in model-specific formats.

Generates separate files for Claude, OpenAI, and Gemini.

Usage:
    python export_for_models.py --skills ../output/skills --output ../output/exports
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters import (
    load_skills_from_directory,
    create_claude_skill,
    create_openai_skill,
    create_gemini_skill,
)


def export_skills(skills_dir: str, output_dir: str) -> dict[str, int]:
    """Export all skills in model-specific formats."""
    skills_dir = Path(skills_dir)
    output_dir = Path(output_dir)

    # Create output directories
    claude_dir = output_dir / "claude"
    openai_dir = output_dir / "openai"
    gemini_dir = output_dir / "gemini"

    for d in [claude_dir, openai_dir, gemini_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # Load all skills
    print(f"Loading skills from: {skills_dir}")
    skills = load_skills_from_directory(skills_dir)
    print(f"Loaded {len(skills)} skills")

    stats = {"claude": 0, "openai": 0, "gemini": 0}

    # Export each skill
    for skill_data in skills:
        skill_id = skill_data.get("id", "unknown")
        category = skill_data.get("category", "general")

        # Create category subdirectories
        (claude_dir / category).mkdir(exist_ok=True)
        (openai_dir / category).mkdir(exist_ok=True)
        (gemini_dir / category).mkdir(exist_ok=True)

        try:
            # Claude export
            claude_adapter = create_claude_skill(skill_data)
            claude_export = claude_adapter.to_anthropic_format()
            with open(claude_dir / category / f"{skill_id}.json", 'w', encoding='utf-8') as f:
                json.dump(claude_export, f, indent=2, ensure_ascii=False)
            stats["claude"] += 1

            # OpenAI export
            openai_adapter = create_openai_skill(skill_data)
            openai_export = openai_adapter.to_openai_format()
            with open(openai_dir / category / f"{skill_id}.json", 'w', encoding='utf-8') as f:
                json.dump(openai_export, f, indent=2, ensure_ascii=False)
            stats["openai"] += 1

            # Gemini export
            gemini_adapter = create_gemini_skill(skill_data)
            gemini_export = gemini_adapter.to_gemini_format()
            with open(gemini_dir / category / f"{skill_id}.json", 'w', encoding='utf-8') as f:
                json.dump(gemini_export, f, indent=2, ensure_ascii=False)
            stats["gemini"] += 1

        except Exception as e:
            print(f"Error exporting {skill_id}: {e}")
            continue

    # Create index files for each model
    for model, model_dir in [("claude", claude_dir), ("openai", openai_dir), ("gemini", gemini_dir)]:
        index = {
            "model": model,
            "exported_at": datetime.now().isoformat(),
            "total_skills": stats[model],
            "categories": {}
        }

        for category_dir in model_dir.iterdir():
            if category_dir.is_dir():
                skill_files = list(category_dir.glob("*.json"))
                index["categories"][category_dir.name] = len(skill_files)

        with open(model_dir / "index.json", 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Export Lyzr skills for different models")
    parser.add_argument(
        "--skills", "-s",
        default="../output/skills",
        help="Path to skills directory"
    )
    parser.add_argument(
        "--output", "-o",
        default="../output/exports",
        help="Output directory for model-specific exports"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("Lyzr Skills Model Exporter")
    print("=" * 50)

    stats = export_skills(args.skills, args.output)

    print(f"\nExport complete!")
    print(f"  Claude: {stats['claude']} skills")
    print(f"  OpenAI: {stats['openai']} skills")
    print(f"  Gemini: {stats['gemini']} skills")
    print(f"\nOutput written to: {args.output}")


if __name__ == "__main__":
    main()
