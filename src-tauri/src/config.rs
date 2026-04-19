// config.rs — Reads Lumara's config.json (and optional config.local.json override).
// Exposes: LumaraConfig, SidecarConfig, LLMConfig, load_config().

use anyhow::Result;
use serde::Deserialize;
use std::path::PathBuf;

#[derive(Debug, Deserialize, Clone)]
pub struct SidecarConfig {
    pub host: String,
    pub port: u16,
    pub timeout_ms: u64,
}

#[derive(Debug, Deserialize, Clone)]
pub struct LLMConfig {
    pub backend: String,
    pub host: String,
    pub port: u16,
    pub model: String,
    pub timeout_s: u64,
    pub max_tokens: u32,
}

#[derive(Debug, Deserialize, Clone)]
pub struct EditingConfig {
    pub batch_adjustment_tolerance: f32,
    pub default_export_quality: u8,
    pub default_export_format: String,
}

#[derive(Debug, Deserialize, Clone)]
pub struct LumaraConfig {
    pub sidecar: SidecarConfig,
    pub llm: LLMConfig,
    pub editing: EditingConfig,
}

/// Loads config.json from the project root, then merges config.local.json if present.
pub fn load_config() -> Result<LumaraConfig> {
    let base_path = find_config_path("config.json")?;
    let base_content = std::fs::read_to_string(&base_path)?;
    let mut base: serde_json::Value = serde_json::from_str(&base_content)?;

    // Merge local overrides if they exist
    let local_path = base_path.parent().unwrap().join("config.local.json");
    if local_path.exists() {
        let local_content = std::fs::read_to_string(&local_path)?;
        let local: serde_json::Value = serde_json::from_str(&local_content)?;
        merge_json(&mut base, &local);
    }

    let config: LumaraConfig = serde_json::from_value(base)?;
    Ok(config)
}

fn find_config_path(name: &str) -> Result<PathBuf> {
    // Walk up from the executable location to find config.json
    let mut dir = std::env::current_exe()?;
    for _ in 0..8 {
        dir.pop();
        let candidate = dir.join(name);
        if candidate.exists() {
            return Ok(candidate);
        }
    }
    // Fallback: current working directory
    Ok(PathBuf::from(name))
}

/// Recursively merges `patch` into `base` (patch wins on conflict).
fn merge_json(base: &mut serde_json::Value, patch: &serde_json::Value) {
    if let (serde_json::Value::Object(b), serde_json::Value::Object(p)) = (base, patch) {
        for (k, v) in p {
            let entry = b.entry(k).or_insert(serde_json::Value::Null);
            merge_json(entry, v);
        }
    } else {
        *base = patch.clone();
    }
}
