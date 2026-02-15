#!/usr/bin/env python3
"""
Lyzr Skills Generator

Converts awesome-chatgpt-prompts CSV to structured skills.json files.
Generates a folder collection of skills that can be shared internally.

Usage:
    python generate_skills.py --input ../awesome-chatgpt-prompts/prompts.csv --output ../output/skills
"""

import csv
import json
import os
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Any


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def extract_variables(prompt: str) -> list[dict[str, str]]:
    """Extract variables from prompt text like ${Variable:Default}."""
    variables = []
    # Pattern matches ${Variable:Default} or ${Variable}
    pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
    matches = re.findall(pattern, prompt)

    for match in matches:
        var_name = match[0].strip()
        default_value = match[1].strip() if match[1] else ""
        variables.append({
            "name": var_name,
            "default": default_value,
            "description": f"Input for {var_name}"
        })

    # Also match {variable} pattern
    simple_pattern = r'\{([^}$]+)\}'
    simple_matches = re.findall(simple_pattern, prompt)

    for var_name in simple_matches:
        if not any(v["name"].lower() == var_name.lower() for v in variables):
            variables.append({
                "name": var_name.strip(),
                "default": "",
                "description": f"Input for {var_name}"
            })

    return variables


def categorize_skill(act: str, prompt: str, for_devs: bool) -> str:
    """Categorize skill based on its name and content."""
    act_lower = act.lower()
    prompt_lower = prompt.lower()

    # Developer/Technical
    if for_devs or any(kw in act_lower for kw in ['developer', 'engineer', 'code', 'programming', 'terminal', 'console', 'devops', 'architect']):
        return "engineering"

    # Sales & Marketing
    if any(kw in act_lower for kw in ['advertiser', 'marketing', 'sales', 'copywriter', 'seo', 'social media', 'content']):
        return "sales-marketing"

    # HR
    if any(kw in act_lower for kw in ['recruiter', 'interviewer', 'hr', 'talent', 'career', 'resume', 'onboarding']):
        return "hr"

    # Customer Service
    if any(kw in act_lower for kw in ['support', 'customer', 'helpdesk', 'service']):
        return "customer-service"

    # BFSI
    if any(kw in act_lower for kw in ['financial', 'accountant', 'investment', 'banking', 'insurance', 'analyst']):
        return "bfsi"

    # Education
    if any(kw in act_lower for kw in ['teacher', 'tutor', 'instructor', 'professor', 'coach', 'mentor', 'educator']):
        return "education"

    # Creative
    if any(kw in act_lower for kw in ['writer', 'poet', 'storyteller', 'composer', 'artist', 'designer', 'creative']):
        return "creative"

    # Healthcare
    if any(kw in act_lower for kw in ['doctor', 'nurse', 'therapist', 'nutritionist', 'health', 'medical', 'psychologist']):
        return "healthcare"

    # Legal
    if any(kw in act_lower for kw in ['lawyer', 'attorney', 'legal', 'contract']):
        return "legal"

    # Language & Communication
    if any(kw in act_lower for kw in ['translator', 'language', 'english', 'speech', 'pronunciation']):
        return "language"

    # General/Other
    return "general"


def create_skill_json(row: dict[str, str], index: int) -> dict[str, Any]:
    """Create a skill JSON object from a CSV row."""
    act = row.get('act', '').strip()
    prompt = row.get('prompt', '').strip()
    for_devs = row.get('for_devs', 'FALSE').upper() == 'TRUE'
    prompt_type = row.get('type', 'TEXT').strip()
    contributor = row.get('contributor', '').strip()

    skill_id = slugify(act) or f"skill-{index}"
    category = categorize_skill(act, prompt, for_devs)
    variables = extract_variables(prompt)

    skill = {
        "id": skill_id,
        "name": act,
        "description": f"Act as {act}" if act else "Custom prompt skill",
        "version": "1.0.0",
        "category": category,
        "tags": [category, "prompt", "assistant"],
        "metadata": {
            "source": "awesome-chatgpt-prompts",
            "license": "CC0-1.0",
            "contributor": contributor,
            "for_developers": for_devs,
            "type": prompt_type,
            "created_at": datetime.now().isoformat(),
        },
        "prompt": {
            "system": prompt,
            "variables": variables,
        },
        "examples": [
            {
                "input": "Start the conversation",
                "context": "Initial interaction with the skill"
            }
        ],
        "compatibility": {
            "models": ["claude", "openai", "gemini"],
            "min_context_length": len(prompt) + 1000,
        }
    }

    # Add developer-specific tags
    if for_devs:
        skill["tags"].append("developer")
        skill["tags"].append("technical")

    return skill


def generate_skills_from_csv(input_path: str, output_dir: str) -> dict[str, int]:
    """Generate skills.json files from CSV."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)

    # Category directories
    categories = set()
    skills = []
    stats = {"total": 0, "by_category": {}}

    # Read CSV
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for index, row in enumerate(reader, start=1):
            if not row.get('act') or not row.get('prompt'):
                continue

            skill = create_skill_json(row, index)
            skills.append(skill)

            category = skill["category"]
            categories.add(category)
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            stats["total"] += 1

    # Create category directories and write individual skill files
    for category in categories:
        category_dir = output_dir / category
        category_dir.mkdir(exist_ok=True)

    # Write individual skill files
    for skill in skills:
        category = skill["category"]
        skill_file = output_dir / category / f"{skill['id']}.json"

        with open(skill_file, 'w', encoding='utf-8') as f:
            json.dump(skill, f, indent=2, ensure_ascii=False)

    # Write master index file
    index_data = {
        "name": "Lyzr Skills Collection",
        "version": "1.0.0",
        "description": "Skills collection derived from awesome-chatgpt-prompts (CC0 License)",
        "license": "CC0-1.0",
        "source": "https://github.com/f/awesome-chatgpt-prompts",
        "generated_at": datetime.now().isoformat(),
        "stats": stats,
        "categories": sorted(list(categories)),
        "skills": [
            {
                "id": s["id"],
                "name": s["name"],
                "category": s["category"],
                "path": f"{s['category']}/{s['id']}.json"
            }
            for s in skills
        ]
    }

    with open(output_dir / "index.json", 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    # Write category indices
    for category in categories:
        category_skills = [s for s in skills if s["category"] == category]
        category_index = {
            "category": category,
            "count": len(category_skills),
            "skills": [
                {"id": s["id"], "name": s["name"]}
                for s in category_skills
            ]
        }

        with open(output_dir / category / "index.json", 'w', encoding='utf-8') as f:
            json.dump(category_index, f, indent=2, ensure_ascii=False)

    return stats


def main():
    parser = argparse.ArgumentParser(description="Generate Lyzr skills from awesome-chatgpt-prompts")
    parser.add_argument(
        "--input", "-i",
        default="../awesome-chatgpt-prompts/prompts.csv",
        help="Path to prompts.csv file"
    )
    parser.add_argument(
        "--output", "-o",
        default="../output/skills",
        help="Output directory for skills"
    )

    args = parser.parse_args()

    print(f"Generating skills from: {args.input}")
    print(f"Output directory: {args.output}")
    print("-" * 50)

    stats = generate_skills_from_csv(args.input, args.output)

    print(f"\nGeneration complete!")
    print(f"Total skills: {stats['total']}")
    print(f"\nBy category:")
    for category, count in sorted(stats['by_category'].items()):
        print(f"  {category}: {count}")

    print(f"\nOutput written to: {args.output}")


if __name__ == "__main__":
    main()
