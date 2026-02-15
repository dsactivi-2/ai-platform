# Lyzr Skills Collection

Internal collection of AI agent skills (system prompts) for the Lyzr platform. This repository provides a structured, model-agnostic skills library that can be used across Claude, OpenAI, and Gemini models.

## What are Skills?

**Skills** are reusable system prompts that define how an AI agent should behave for a specific task or role. Instead of writing prompts from scratch, you can use pre-defined skills that have been tested and categorized.

**Example**: A "Linux Terminal" skill instructs the AI to act as a Linux terminal, responding only with terminal output in code blocks.

## Source & License

- **Source**: [awesome-chatgpt-prompts](https://github.com/f/awesome-chatgpt-prompts)
- **License**: **CC0 1.0 Universal (Public Domain)** - Free for commercial use, no attribution required
- **Total Skills**: 456 skills across 11 categories

---

## Project Structure

```
lyzr-skills/
├── scripts/
│   ├── generate_skills.py      # Convert CSV → skills.json
│   └── export_for_models.py    # Export for Claude/OpenAI/Gemini
├── adapters/
│   ├── base.py                 # Base adapter class
│   ├── claude_adapter.py       # Anthropic Claude adapter
│   ├── openai_adapter.py       # OpenAI GPT adapter
│   └── gemini_adapter.py       # Google Gemini adapter
├── output/
│   ├── skills/                 # Master skills collection
│   │   ├── index.json          # Master index with all skills
│   │   ├── engineering/        # Category: 78 skills
│   │   ├── hr/                 # Category: 8 skills
│   │   ├── sales-marketing/    # Category: 10 skills
│   │   ├── customer-service/   # Category: 4 skills
│   │   ├── bfsi/               # Category: 8 skills
│   │   ├── education/          # Category: 13 skills
│   │   ├── creative/           # Category: 15 skills
│   │   ├── healthcare/         # Category: 14 skills
│   │   ├── legal/              # Category: 2 skills
│   │   ├── language/           # Category: 7 skills
│   │   └── general/            # Category: 297 skills
│   └── exports/                # Model-specific exports
│       ├── claude/             # Ready for Anthropic API
│       ├── openai/             # Ready for OpenAI API
│       └── gemini/             # Ready for Google API
└── README.md
```

---

## Skill JSON Schema

Each skill is stored as a JSON file with the following schema:

### Full Schema

```json
{
  "id": "linux-terminal",
  "name": "Linux Terminal",
  "description": "Act as Linux Terminal",
  "version": "1.0.0",
  "category": "engineering",
  "tags": ["engineering", "developer", "technical", "prompt", "assistant"],
  "metadata": {
    "source": "awesome-chatgpt-prompts",
    "license": "CC0-1.0",
    "contributor": "f",
    "for_developers": true,
    "type": "TEXT",
    "created_at": "2025-01-15T10:30:00.000Z"
  },
  "prompt": {
    "system": "I want you to act as a linux terminal. I will type commands and you will reply with what the terminal should show. I want you to only reply with the terminal output inside one unique code block, and nothing else. Do not write explanations. Do not type commands unless I instruct you to do so. When I need to tell you something in english, I will do so by putting text inside curly brackets {like this}. My first command is pwd",
    "variables": [
      {
        "name": "command",
        "default": "pwd",
        "description": "Input for command"
      }
    ]
  },
  "examples": [
    {
      "input": "Start the conversation",
      "context": "Initial interaction with the skill"
    }
  ],
  "compatibility": {
    "models": ["claude", "openai", "gemini"],
    "min_context_length": 2000
  }
}
```

### Schema Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (URL-safe slug) |
| `name` | string | Yes | Human-readable name |
| `description` | string | Yes | Brief description of the skill |
| `version` | string | Yes | Semantic version (e.g., "1.0.0") |
| `category` | string | Yes | Category classification |
| `tags` | array | Yes | Searchable tags |
| `metadata` | object | Yes | Source and attribution info |
| `metadata.source` | string | Yes | Origin of the skill |
| `metadata.license` | string | Yes | License identifier |
| `metadata.contributor` | string | No | Original author |
| `metadata.for_developers` | boolean | No | Developer-focused skill flag |
| `metadata.type` | string | No | Prompt type (TEXT, CODE, etc.) |
| `metadata.created_at` | string | No | ISO timestamp |
| `prompt` | object | Yes | The actual prompt content |
| `prompt.system` | string | Yes | System prompt text |
| `prompt.variables` | array | No | Configurable variables |
| `examples` | array | No | Usage examples |
| `compatibility` | object | No | Model compatibility info |

### Variables Schema

Variables allow dynamic content injection into prompts:

```json
{
  "variables": [
    {
      "name": "Position",
      "default": "Software Developer",
      "description": "The job position for the interview"
    },
    {
      "name": "Language",
      "default": "English",
      "description": "Target language for translation"
    }
  ]
}
```

**Variable Patterns in Prompts**:
- `${Variable:Default}` - Variable with default value
- `${Variable}` - Variable without default
- `{variable}` - Simple variable placeholder

---

## Categories

| Category | Count | Description |
|----------|-------|-------------|
| `engineering` | 78 | Developer tools, coding, DevOps, architecture |
| `hr` | 8 | Recruiting, interviews, talent management |
| `sales-marketing` | 10 | Marketing, content, advertising, SEO |
| `customer-service` | 4 | Support, helpdesk, service |
| `bfsi` | 8 | Banking, finance, insurance, accounting |
| `education` | 13 | Teaching, tutoring, coaching, mentoring |
| `creative` | 15 | Writing, art, design, music, storytelling |
| `healthcare` | 14 | Medical, therapy, wellness, nutrition |
| `legal` | 2 | Law, contracts, compliance |
| `language` | 7 | Translation, communication, linguistics |
| `general` | 297 | Miscellaneous and multi-purpose skills |

---

## How to Use

### 1. Browse Skills

**View the master index:**
```bash
cat output/skills/index.json | jq '.stats'
```

**List skills in a category:**
```bash
ls output/skills/engineering/
cat output/skills/engineering/index.json | jq '.skills[].name'
```

### 2. Use Skills Directly (Copy/Paste)

Open any skill JSON and copy the `prompt.system` field:

```bash
cat output/skills/engineering/linux-terminal.json | jq -r '.prompt.system'
```

### 3. Use with Python Adapters

```python
import sys
sys.path.append('/path/to/lyzr-skills')

from adapters import load_skill, get_adapter

# Load a skill
skill = load_skill("output/skills/engineering/linux-terminal.json")

# Get adapter for your model
adapter = get_adapter(skill, "claude")  # or "openai", "gemini"

# Get the formatted system prompt
system_prompt = adapter.format_system_prompt()

# Create API-ready message
message = adapter.create_message("ls -la")
print(message)
```

### 4. Use with Claude (Anthropic)

```python
from anthropic import Anthropic
from adapters import load_skill, create_claude_skill

# Load and adapt skill
skill = load_skill("output/skills/engineering/linux-terminal.json")
adapter = create_claude_skill(skill)

# Call Claude API
client = Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=adapter.format_system_prompt(),
    messages=[{"role": "user", "content": "pwd"}]
)
print(response.content[0].text)
```

### 5. Use with OpenAI

```python
from openai import OpenAI
from adapters import load_skill, create_openai_skill

# Load and adapt skill
skill = load_skill("output/skills/engineering/linux-terminal.json")
adapter = create_openai_skill(skill)

# Call OpenAI API
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    max_tokens=4096,
    messages=[
        {"role": "system", "content": adapter.format_system_prompt()},
        {"role": "user", "content": "pwd"}
    ]
)
print(response.choices[0].message.content)
```

### 6. Use with Gemini

```python
import google.generativeai as genai
from adapters import load_skill, create_gemini_skill

# Load and adapt skill
skill = load_skill("output/skills/engineering/linux-terminal.json")
adapter = create_gemini_skill(skill)

# Call Gemini API
genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    system_instruction=adapter.format_system_prompt()
)
response = model.generate_content("pwd")
print(response.text)
```

### 7. Use Pre-exported Model Files

For convenience, skills are pre-exported in model-specific formats:

```bash
# Claude-ready files
cat output/exports/claude/engineering/linux-terminal.json

# OpenAI-ready files
cat output/exports/openai/engineering/linux-terminal.json

# Gemini-ready files
cat output/exports/gemini/engineering/linux-terminal.json
```

---

## Regenerating Skills

If you need to regenerate skills from the source CSV:

### 1. Generate Base Skills

```bash
cd scripts
python generate_skills.py \
    --input /path/to/awesome-chatgpt-prompts/prompts.csv \
    --output ../output/skills
```

### 2. Export for All Models

```bash
python export_for_models.py \
    --skills ../output/skills \
    --output ../output/exports
```

---

## Adding Custom Skills

### 1. Create a New Skill File

Create a JSON file following the schema:

```bash
cat > output/skills/hr/custom-recruiter.json << 'EOF'
{
  "id": "custom-recruiter",
  "name": "Custom Recruiter",
  "description": "Act as a technical recruiter for Lyzr",
  "version": "1.0.0",
  "category": "hr",
  "tags": ["hr", "recruiting", "lyzr", "custom"],
  "metadata": {
    "source": "lyzr-internal",
    "license": "Proprietary",
    "contributor": "your-name",
    "for_developers": false,
    "type": "TEXT",
    "created_at": "2025-01-15T00:00:00.000Z"
  },
  "prompt": {
    "system": "You are a technical recruiter for Lyzr, an AI agent platform company. Your role is to screen candidates for ${Position} roles. Be professional, friendly, and assess both technical skills and cultural fit.",
    "variables": [
      {
        "name": "Position",
        "default": "Software Engineer",
        "description": "The position being recruited for"
      }
    ]
  },
  "examples": [
    {
      "input": "Tell me about yourself",
      "context": "Opening interview question"
    }
  ],
  "compatibility": {
    "models": ["claude", "openai", "gemini"],
    "min_context_length": 1500
  }
}
EOF
```

### 2. Update Category Index

```bash
# Regenerate the category index
python scripts/generate_skills.py --input /dev/null --output output/skills
```

---

## Integration with Lyzr Platform

These skills can be integrated with:

1. **Global Contexts** - Use skills as context templates
2. **Agent Builder** - Pre-populate system prompts
3. **Blueprints** - Include skills in blueprint definitions
4. **CLI (lyzr-kit)** - Reference skills by ID

---

## Team

**Blueprint Track** - Lyzr Platform

For questions or contributions, contact the Blueprint team.
