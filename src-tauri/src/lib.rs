mod python;

#[tauri::command]
fn generate_chart(params: String) -> Result<String, String> {
    python::run(&params)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![generate_chart])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
