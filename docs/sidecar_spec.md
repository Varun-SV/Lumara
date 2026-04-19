# Lumara Sidecar File Specification

**Version:** 1  
**File extension:** `.lumara.json`  
**Location:** Same directory as the source image, named `<image_stem>.lumara.json`

---

## Purpose

Lumara never modifies original image files. All edits are stored in a `.lumara.json`
sidecar file placed next to the source image. The sidecar is a plain JSON file containing
the ordered edit stack — the complete sequence of operations needed to reproduce the
edited result from the original.

---

## Schema

```json
{
  "version": 1,
  "source_file": "/absolute/path/to/photo.cr2",
  "created_at": "2026-04-19T10:00:00.000Z",
  "updated_at": "2026-04-19T10:45:00.000Z",
  "edit_stack": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "parametric",
      "description": "User adjusted exposure to +0.7",
      "parameters": {
        "exposure": 0.7
      },
      "layer_name": "Adjust exposure",
      "reversible": true,
      "timestamp": "2026-04-19T10:10:00.000Z"
    },
    {
      "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
      "type": "code",
      "description": "AI-generated inpainting to remove object",
      "parameters": {
        "mask_region": [120, 80, 300, 250]
      },
      "code": "def apply_edit(image, params):\n    ...\n    return image",
      "layer_name": "Remove object (inpainting)",
      "reversible": true,
      "timestamp": "2026-04-19T10:20:00.000Z"
    }
  ]
}
```

---

## Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | integer | ✓ | Schema version (currently `1`) |
| `source_file` | string | ✓ | Absolute path to the original image file |
| `created_at` | ISO 8601 string | ✓ | UTC timestamp when the sidecar was first created |
| `updated_at` | ISO 8601 string | ✓ | UTC timestamp of the last save |
| `edit_stack` | array | ✓ | Ordered list of edit layer objects |

### Edit layer object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID string | ✓ | Unique identifier for this layer |
| `type` | `"parametric"` \| `"code"` | ✓ | Edit type |
| `description` | string | ✓ | Human-readable description of what this layer does |
| `parameters` | object | ✓ | Edit parameter dict (see Edit Parameter Schema in `system_prompt.md`) |
| `code` | string | only if `type === "code"` | Self-contained Python `apply_edit` function string |
| `layer_name` | string | ✓ | Display name shown in the History panel |
| `reversible` | boolean | ✓ | Always `true` unless the layer is a destructive export step |
| `timestamp` | ISO 8601 string | ✓ | UTC timestamp when this layer was added |

---

## Rules

1. **Never modify the original file.** The sidecar is the only persistent artifact of editing.
2. **The edit stack is ordered.** Layers are applied in array order (index 0 first).
3. **All values must be JSON-serialisable.** No class instances, functions, or circular refs.
4. **Code strings** must define `apply_edit(image: PIL.Image.Image, params: dict) -> PIL.Image.Image`.
5. **Sidecar files are git-ignored** (`*.lumara.json`) and must never be committed.
6. **Version field** must be checked on load; unknown versions should warn and refuse to apply.

---

## Versioning

If the schema needs to change in a backwards-incompatible way, `version` will be incremented.
The sidecar loader (`python/main.py`) checks `version` and will refuse to process sidecars
with a version number higher than its own supported version, returning a warning instead.
