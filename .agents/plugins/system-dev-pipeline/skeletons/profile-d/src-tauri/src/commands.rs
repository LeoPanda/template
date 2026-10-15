use tauri::State;
use crate::sidecar::SidecarState;
use serde::Serialize;

#[derive(Serialize)]
pub struct AppConfigResponse {
    pub session_token: String,
    pub api_port: u16,
    pub platform: String,
}

#[tauri::command]
pub fn get_app_config(state: State<'_, SidecarState>) -> AppConfigResponse {
    let platform = if cfg!(target_os = "macos") {
        "macos"
    } else if cfg!(target_os = "windows") {
        "windows"
    } else {
        "linux"
    };

    AppConfigResponse {
        session_token: state.session_token.clone(),
        api_port: state.port,
        platform: platform.to_string(),
    }
}
