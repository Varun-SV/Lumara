# Lumara

A local-first, privacy-preserving AI photo editor for desktop. All processing happens on-device — no images or data ever leave your machine.

Built with **Tauri + React + TypeScript** (frontend) and a **Python FastAPI sidecar** (image processing + LLM communication). Uses vision-capable local LLMs via [Ollama](https://ollama.com), LM Studio, or llama.cpp.

---

## Features

- **Non-destructive editing** — original files are never modified; all edits live in `.lumara.json` sidecar files
- **Local AI suggestions** — vision LLM analyses each photo and proposes ranked edit suggestions
- **Natural language commands** — type "make it moodier" or "fix the skin tones"
- **Full tonal control** — exposure, tone curve, HSL, sharpening, noise reduction, vignette
- **RAW support** — CR2, NEF, ARW, DNG, RW2, ORF via rawpy
- **Portrait retouching** — skin smoothing, eye enhancement, teeth whitening
- **AI ops** — inpainting, outpainting, style transfer (requires GPU + diffusers)
- **Batch processing** — apply an edit stack to multiple images

---

## Requirements

### Runtime
- [Rust + Cargo](https://rustup.rs) (for Tauri)
- Node.js 18+
- Python 3.11+
- [Ollama](https://ollama.com) with a vision model (e.g. `ollama pull llava`)

### Python dependencies
```bash
cd python
pip install -r requirements.txt
```

---

## Getting started

```bash
# 1. Install frontend dependencies
npm install

# 2. Install Python sidecar dependencies
pip install -r python/requirements.txt

# 3. Pull a vision model (first time only)
ollama pull llava

# 4. Start in dev mode (launches Tauri + Vite + Python sidecar)
npm run tauri:dev
```

### Configuration

Copy and edit `config.json` to `config.local.json` for local overrides (git-ignored):

```json
{
  "sidecar": { "port": 7842 },
  "llm": { "model": "llava:latest", "port": 11434 }
}
```

---

## Project structure

```
lumara/
├── src/                  # React + TypeScript frontend
│   ├── components/       # UI components
│   ├── store/            # Zustand state (edit stack, session)
│   ├── hooks/            # Tauri IPC + LLM hooks
│   └── types/            # lumara.d.ts — all shared types
├── src-tauri/            # Tauri desktop shell (Rust)
│   └── src/              # main.rs, commands.rs, config.rs, sidecar.rs
├── python/               # Python image processing sidecar
│   ├── processors/       # Per-operation image modules
│   ├── ai/               # LLM client, prompt builder, response parser
│   └── formats/          # RAW + standard format loaders/exporters
├── docs/                 # Architecture, sidecar spec, system prompt
├── tests/                # Unit + integration tests
└── config.json           # Runtime configuration (ports, model names)
```

---

## Architecture

See [docs/architecture.md](docs/architecture.md) for a full system diagram.

## Sidecar file format

See [docs/sidecar_spec.md](docs/sidecar_spec.md) for the `.lumara.json` schema.

---

## Running tests

```bash
# Python sidecar tests
pip install pytest pytest-asyncio respx
pytest tests/python -v
```

---

## Git workflow

- Branch: `feature/<name>` or `fix/<name>`
- Commits: `feat(scope): description` — see project instructions for full format
- Never commit `*.lumara.json`, `.venv`, `node_modules`, or `target/`
