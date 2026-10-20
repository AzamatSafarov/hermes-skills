# Fast ASCII Format Example (demo-project)

> Dense, scannable README for tools, scripts, and internal projects without custom visuals.

---

```markdown
# ⚡ Demo Project

<div align="center">

```
╔═══════════════════════════════════════════════════╗
║   FastQuery → Cache → Transform → Respond         ║
║   CLI tool for quick data pipeline prototyping    ║
╚═══════════════════════════════════════════════════╝
```

[![GitHub](https://img.shields.io/badge/GitHub-OWNER%2Fdemo--project-161b22?style=flat-square&logo=github)](https://github.com/OWNER/demo-project)
[![Status](https://img.shields.io/badge/status-active-success?style=flat-square)](#)
[![Stack](https://img.shields.io/badge/stack-Python%20%2B%20SQLite-blue?style=flat-square)](#)
[![Version](https://img.shields.io/badge/version-0.3.0-yellow?style=flat-square)](#)

> *Process CSV files in 3 commands. No config files, no dependencies beyond Python standard library.*

</div>

## What it does

Reads CSV, applies transforms, outputs JSON or SQL inserts. Designed for ad-hoc data tasks where spinning up a full ETL pipeline is overkill.

## Architecture

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌──────────┐
│  input  │───→│  parser  │───→│ transform│───→│  output  │
│  .csv   │    │  (csv)   │    │  (jinja) │    │ .json    │
└─────────┘    └──────────┘    └─────────┘    └──────────┘
```

## Structure

```
demo-project/
├── 📖 README.md           ← you are here
├── 📜 CHANGELOG.md        ← version history
│
├── ⚙️ src/                ← source code
│   ├── __init__.py
│   ├── parser.py          ← CSV reading
│   ├── transform.py       ← data transforms
│   └── output.py          ← JSON/SQL writers
│
├── 🧪 tests/              ← pytest suite
│   └── test_pipeline.py
│
└── 📋 examples/           ← sample CSV files
    └── sample.csv
```

## Status

| Feature | Status | Notes |
|---------|--------|-------|
| CSV parsing | ✅ Done | Handles UTF-8, quotes, newlines |
| JSON output | ✅ Done | Pretty-printed or compact |
| SQL output | ✅ Done | INSERT statements |
| Jinja transforms | 🟡 Partial | Basic filters only |
| Excel input | ❌ No plans | Use `xlsx2csv` first |
| Streaming | ❌ Blocked | Memory constraints |

## Install

```bash
git clone https://github.com/OWNER/demo-project.git
cd demo-project
python -m pip install -e .
```

## Quick start

```bash
# CSV → JSON
python -m demo_project input.csv --format json

# CSV → SQL inserts
python -m demo_project input.csv --format sql --table users

# With custom transform
python -m demo_project input.csv --transform uppercase
```

## Where things live

| Layer | What | Where |
|-------|------|-------|
| Core | CSV parser | `src/parser.py` |
| Core | Transforms | `src/transform.py` |
| CLI | argparse entry | `src/__main__.py` |
| Tests | pytest | `tests/` |
| Docs | This README | `README.md` |

## License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

**Built for the open-source community**

</div>
```

---

## Key elements of this example

| Element | Where | Why |
|---------|-------|-----|
| ASCII banner | Below title | Instant understanding of what this does |
| Shields row | Under ASCII | Status, stack, version — one glance |
| Italic pitch | Under shields | 15 words explaining "why this exists" |
| Emoji tree | `## Structure` | Visual file navigation |
| Status table | `## Status` | ✅🟡❌ — scannable in 2 seconds |
| Where table | `## Where things live` | Code vs tests vs docs |
| Author footer | Bottom | Attribution |

## Badge color codes

- `success` = green, works
- `blue` = info, stack
- `yellow` = warning, partial
- `red` = broken / no API
- `lightgrey` = archive / not planned

## Anti-slop example

Bad: "As you can see, the system works well. It is important to note that..."
Good: "CSV parsing works. Excel input does not — use xlsx2csv first."
