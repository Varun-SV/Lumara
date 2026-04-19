// sidecar.rs — Spawns and manages the Python image-processing sidecar process.
// Exposes: launch(), wait_for_ready().

use anyhow::{Context, Result};
use std::time::{Duration, Instant};
use tauri::AppHandle;

const MAX_WAIT_MS: u64 = 15_000;
const POLL_INTERVAL_MS: u64 = 200;

/// Spawns `python/main.py` as a child process and waits until its HTTP health endpoint
/// responds. The sidecar port is read from the config passed at startup.
pub fn launch(_handle: &AppHandle, port: u16) -> Result<()> {
    log::info!("[sidecar] Launching Python sidecar on port {port}");

    let python_cmd = resolve_python();
    let script = resolve_script_path()?;

    let child = std::process::Command::new(&python_cmd)
        .arg(&script)
        .env("LUMARA_SIDECAR_PORT", port.to_string())
        .spawn()
        .with_context(|| {
            format!(
                "Failed to start Python sidecar: {} {}",
                python_cmd,
                script.display()
            )
        })?;

    log::info!("[sidecar] Spawned PID {}", child.id());

    wait_for_ready(port)?;
    log::info!("[sidecar] Python sidecar is ready on port {port}");

    Ok(())
}

/// Polls the sidecar's /health endpoint until it responds or the timeout elapses.
pub fn wait_for_ready(port: u16) -> Result<()> {
    let url = format!("http://127.0.0.1:{port}/health");
    let deadline = Instant::now() + Duration::from_millis(MAX_WAIT_MS);

    while Instant::now() < deadline {
        if let Ok(resp) = reqwest::blocking::get(&url) {
            if resp.status().is_success() {
                return Ok(());
            }
        }
        std::thread::sleep(Duration::from_millis(POLL_INTERVAL_MS));
    }

    anyhow::bail!(
        "Python sidecar did not become ready within {}ms",
        MAX_WAIT_MS
    )
}

fn resolve_python() -> String {
    // Prefer venv python, fall back to system python3 / python
    for candidate in &["python/venv/bin/python", "python3", "python"] {
        if std::process::Command::new(candidate)
            .arg("--version")
            .output()
            .is_ok()
        {
            return candidate.to_string();
        }
    }
    "python3".to_string()
}

fn resolve_script_path() -> Result<std::path::PathBuf> {
    let mut dir = std::env::current_exe()?;
    for _ in 0..8 {
        dir.pop();
        let candidate = dir.join("python").join("main.py");
        if candidate.exists() {
            return Ok(candidate);
        }
    }
    Ok(std::path::PathBuf::from("python/main.py"))
}
