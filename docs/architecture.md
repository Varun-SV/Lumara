# Lumara Architecture

## Overview

Lumara is a local-first, privacy-preserving desktop photo editor. All processing
happens on-device. No images or metadata ever leave the user's machine.

```
┌─────────────────────────────────────────────────────────┐
│                     Tauri Shell (Rust)                   │
│  ┌──────────────────────────────────────────────────┐   │
│  │          React + TypeScript Frontend              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌─────────────────┐  │   │
│  │  │  History  │ │  Canvas  │ │  Edit + Suggest  │  │   │
│  │  │  Panel   │ │  (view)  │ │      Panels      │  │   │
│  │  └──────────┘ └──────────┘ └─────────────────┘  │   │
│  │       Zustand stores: editStore, sessionStore    │   │
│  └─────────────────┬────────────────────────────────┘   │
│                    │ Tauri IPC (invoke)                  │
│  ┌─────────────────▼────────────────────────────────┐   │
│  │           Rust IPC Commands                       │   │
│  │  load_image · apply_edits · load/save_sidecar    │   │
│  │  llm_analyse                                      │   │
│  └────────────┬─────────────────────────────────────┘   │
└───────────────│─────────────────────────────────────────┘
                │ HTTP (localhost only)
┌───────────────▼─────────────────────────────────────────┐
│              Python Sidecar (FastAPI + uvicorn)          │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │                  Route handlers                   │    │
│  │  /image/load  /image/apply  /sidecar/*  /llm/*  │    │
│  └──────────┬──────────────────────────┬────────────┘   │
│             │                          │                  │
│  ┌──────────▼──────────┐  ┌───────────▼──────────────┐  │
│  │  Image Processors   │  │      AI / LLM Layer       │  │
│  │  basic · wb · hsl   │  │  OllamaClient             │  │
│  │  detail · geometry  │  │  prompt_builder           │  │
│  │  portrait · ai_ops  │  │  response_parser          │  │
│  └──────────┬──────────┘  └───────────┬──────────────┘  │
│             │                          │                  │
│  ┌──────────▼──────────┐  ┌───────────▼──────────────┐  │
│  │  formats/loader     │  │  Ollama / LM Studio       │  │
│  │  formats/exporter   │  │  (local LLM backend)      │  │
│  └─────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Data flow — opening an image

1. User clicks "Open" → Tauri dialog → file path selected
2. `useImageProcessor.openImage()` calls `invoke("load_image", { filePath })`
3. Rust command POSTs to Python sidecar `/image/load`
4. Sidecar decodes the file (rawpy for RAW, Pillow for standard formats)
5. Returns metadata + base64 JPEG preview to Rust → forwarded to React
6. React stores image in `sessionStore`, renders preview in `PhotoCanvas`
7. `useLLMSuggestions.analyseImage()` calls `invoke("llm_analyse", ...)`
8. Sidecar sends base64 image to Ollama with the system prompt
9. LLM returns structured JSON → `response_parser` validates it
10. React populates `SuggestionCard` with 3–5 HIGH/MEDIUM/LOW suggestions

## Data flow — applying an edit

1. User moves a slider in `EditPanel` or clicks "Apply" on a suggestion
2. `editStore.pushEdit()` adds a new layer to the stack
3. `useImageProcessor.applyEdits()` sends the full active stack to the sidecar
4. Sidecar replays all layers on the original image in order
5. Returns updated base64 preview → `sessionStore.setPreview()` → canvas re-renders

## Non-destructive guarantee

Original files are **never written to**. The edit stack lives in memory (Zustand)
and is optionally persisted to a `.lumara.json` sidecar file. Exporting triggers
a separate path through `formats/exporter.py` to a user-chosen output location.

## LLM backend compatibility

The `OllamaClient` is written against the Ollama `/api/generate` API.
LM Studio exposes a compatible endpoint; set `llm.port` to LM Studio's port (default 1234)
in `config.local.json`. llama.cpp server can be pointed to similarly.

## Port configuration

All ports are read from `config.json` (or `config.local.json` for local overrides).
No ports are hardcoded anywhere in the codebase. Environment variable
`LUMARA_SIDECAR_PORT` overrides the sidecar port for process isolation.
