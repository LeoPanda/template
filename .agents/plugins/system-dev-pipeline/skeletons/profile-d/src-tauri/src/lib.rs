pub mod sidecar;
pub mod commands;

use sidecar::SidecarState;
use tauri::{AppHandle, Manager, RunEvent};

pub fn run() {
    let sidecar_state = SidecarState::new();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_store::Builder::default().build())
        .manage(sidecar_state)
        .invoke_handler(tauri::generate_handler![commands::get_app_config])
        .setup(|app| {
            println!("[Tauri] App setup initialized.");
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while running tauri application")
        .run(|app_handle, event| {
            if let RunEvent::ExitRequested { .. } = event {
                println!("[Tauri] Exit requested. Cleaning up sidecar processes...");
                let state = app_handle.state::<SidecarState>();
                sidecar::kill_sidecar(&state);
            }
        });
}
