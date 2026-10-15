use std::process::Command;
use std::sync::Mutex;
use std::time::Duration;
use tauri::{AppHandle, Manager};
use uuid::Uuid;

pub struct SidecarState {
    pub child_pid: Mutex<Option<u32>>,
    pub session_token: String,
    pub port: u16,
}

impl SidecarState {
    pub fn new() -> Self {
        let session_token = Uuid::new_v4().to_string();
        // 利用可能なランダムポートまたは固定ポート（デフォルト 54321）
        let port = 54321;
        Self {
            child_pid: Mutex::new(None),
            session_token,
            port,
        }
    }
}

/// Sidecar プロセスの安全な終了（ゾンビプロセス回収）
pub fn kill_sidecar(state: &SidecarState) {
    let mut pid_guard = state.child_pid.lock().unwrap();
    if let Some(pid) = *pid_guard {
        println!("[Sidecar] Terminating child process PID: {}", pid);
        #[cfg(unix)]
        unsafe {
            // まずは優しく SIGTERM を送信
            libc::kill(pid as i32, libc::SIGTERM);
            std::thread::sleep(Duration::from_millis(500));
            // 終了していなければ確実に SIGKILL で回収
            libc::kill(pid as i32, libc::SIGKILL);
        }
        #[cfg(windows)]
        {
            let _ = Command::new("taskkill")
                .args(&["/F", "/T", "/PID", &pid.to_string()])
                .output();
        }
        *pid_guard = None;
    }
}

/// Sidecar の死活監視・ヘルスチェックポーリング
pub async fn wait_for_health(port: u16, max_retries: u32) -> bool {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_millis(500))
        .build()
        .unwrap();

    let health_url = format!("http://127.0.0.1:{}/api/internal/health", port);

    for i in 0..max_retries {
        tokio::time::sleep(Duration::from_millis(200)).await;
        if let Ok(resp) = client.get(&health_url).send().await {
            if resp.status().is_success() {
                println!("[Sidecar] Health check PASSED on attempt {}", i + 1);
                return true;
            }
        }
    }
    eprintln!("[Sidecar] Health check FAILED after {} attempts", max_retries);
    false
}
