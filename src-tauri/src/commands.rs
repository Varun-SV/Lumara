// commands.rs — Tauri IPC command handlers.
// Each command proxies a request to the Python sidecar over HTTP.
// Exposes: load_image, apply_edits, load_sidecar, save_sidecar, llm_analyse.

use crate::AppState;
use serde::{Deserialize, Serialize};
use tauri::State;

// ---------------------------------------------------------------------------
// Shared types (mirror of TypeScript types in lumara.d.ts)
// ---------------------------------------------------------------------------

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessImageRequest {
    pub image_path: String,
    pub edit_stack: serde_json::Value,
    pub output_format: Option<String>,
    pub output_quality: Option<u8>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessImageResponse {
    pub preview_data_url: String,
    pub warnings: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LoadedImage {
    pub id: String,
    pub file_path: String,
    pub file_name: String,
    pub format: String,
    pub width_px: u32,
    pub height_px: u32,
    pub preview_data_url: String,
    pub analysis: Option<serde_json::Value>,
    pub caption: Option<String>,
    pub tags: Option<Vec<String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SidecarData {
    pub version: u8,
    pub source_file: String,
    pub created_at: String,
    pub updated_at: String,
    pub edit_stack: serde_json::Value,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LLMAnalysisRequest {
    pub image_path: String,
    pub user_message: Option<String>,
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

fn sidecar_url(state: &AppState, path: &str) -> String {
    format!(
        "http://{}:{}{path}",
        state.config.sidecar.host, state.config.sidecar.port
    )
}

fn post<T: serde::de::DeserializeOwned>(url: &str, body: &impl Serialize) -> Result<T, String> {
    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(60))
        .build()
        .map_err(|e| e.to_string())?;

    let resp = client
        .post(url)
        .json(body)
        .send()
        .map_err(|e| format!("Sidecar request failed: {e}"))?;

    if !resp.status().is_success() {
        let status = resp.status();
        let body = resp.text().unwrap_or_default();
        return Err(format!("Sidecar error {status}: {body}"));
    }

    resp.json::<T>().map_err(|e| e.to_string())
}

// ---------------------------------------------------------------------------
// IPC commands
// ---------------------------------------------------------------------------

/// Load and decode an image file; returns metadata and a base64 preview.
#[tauri::command]
pub fn load_image(
    file_path: String,
    state: State<'_, AppState>,
) -> Result<LoadedImage, String> {
    let url = sidecar_url(&state, "/image/load");
    post(&url, &serde_json::json!({ "file_path": file_path }))
}

/// Apply the given edit stack and return an updated preview.
#[tauri::command]
pub fn apply_edits(
    request: ProcessImageRequest,
    state: State<'_, AppState>,
) -> Result<ProcessImageResponse, String> {
    let url = sidecar_url(&state, "/image/apply");
    post(&url, &request)
}

/// Load the .lumara.json sidecar for the given image path.
#[tauri::command]
pub fn load_sidecar(
    file_path: String,
    state: State<'_, AppState>,
) -> Result<SidecarData, String> {
    let url = sidecar_url(&state, "/sidecar/load");
    post(&url, &serde_json::json!({ "file_path": file_path }))
}

/// Persist the edit stack as a .lumara.json sidecar next to the source file.
#[tauri::command]
pub fn save_sidecar(
    file_path: String,
    edit_stack: serde_json::Value,
    state: State<'_, AppState>,
) -> Result<(), String> {
    let url = sidecar_url(&state, "/sidecar/save");
    post::<serde_json::Value>(
        &url,
        &serde_json::json!({ "file_path": file_path, "edit_stack": edit_stack }),
    )
    .map(|_| ())
}

/// Send the image to the LLM for analysis or a natural-language edit command.
#[tauri::command]
pub fn llm_analyse(
    request: LLMAnalysisRequest,
    state: State<'_, AppState>,
) -> Result<serde_json::Value, String> {
    let url = sidecar_url(&state, "/llm/analyse");
    post(&url, &request)
}
