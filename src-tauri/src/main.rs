// main.rs — Tauri application entry point for Lumara.
// Registers IPC commands and starts the Python sidecar process.
// Exposes: load_image, apply_edits, load_sidecar, save_sidecar, llm_analyse.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod config;
mod sidecar;

use std::sync::Mutex;
use tauri::Manager;

/// Shared application state available to all IPC commands.
pub struct AppState {
    pub config: config::LumaraConfig,
    pub sidecar_process: Mutex<Option<std::process::Child>>,
}

fn main() {
    env_logger::init();

    let cfg = config::load_config().expect("Failed to load config.json");
    let sidecar_port = cfg.sidecar.port;

    tauri::Builder::default()
        .manage(AppState {
            config: cfg,
            sidecar_process: Mutex::new(None),
        })
        .setup(move |app| {
            // Launch the Python sidecar
            let handle = app.handle();
            std::thread::spawn(move || {
                if let Err(e) = sidecar::launch(&handle, sidecar_port) {
                    log::error!("Failed to start Python sidecar: {e}");
                }
            });
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::load_image,
            commands::apply_edits,
            commands::load_sidecar,
            commands::save_sidecar,
            commands::llm_analyse,
        ])
        .run(tauri::generate_context!())
        .expect("error while running Lumara");
}
