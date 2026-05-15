use std::io::Write;
use std::process::{Command, Stdio};
use std::path::PathBuf;

fn resources_dir() -> PathBuf {
    let exe = std::env::current_exe().unwrap();
    let mut dir = exe.parent().unwrap().to_path_buf();
    // In development: ../python/
    // In production (bundled): ../../../Resources/python/
    if cfg!(debug_assertions) {
        dir.pop(); // remove MacOS/
        dir.pop(); // remove ../../
        dir.push("python");
    } else {
        dir.pop(); // remove MacOS/
        dir.push("Resources");
        dir.push("python");
    }
    dir
}

fn find_python(python_dir: &PathBuf) -> String {
    let candidates = [
        python_dir.join("portable").join("bin").join("python3"),
        python_dir.join("portable").join("bin").join("python3.11"),
    ];
    for p in &candidates {
        if p.exists() {
            return p.to_string_lossy().to_string();
        }
    }
    // fallback to system
    for cmd in &["python3.13", "python3.12", "python3.11", "python3"] {
        if Command::new(cmd)
            .arg("--version")
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status()
            .is_ok()
        {
            return cmd.to_string();
        }
    }
    "python3".to_string()
}

pub fn run(params: &str) -> Result<String, String> {
    let python_dir = resources_dir();
    let python = find_python(&python_dir);
    let script = python_dir.join("main.py");

    if !script.exists() {
        return Err(format!(
            "Python script not found at: {}",
            script.display()
        ));
    }

    let mut child = Command::new(&python)
        .arg(&script)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start Python: {}", e))?;

    if let Some(mut stdin) = child.stdin.take() {
        stdin
            .write_all(params.as_bytes())
            .map_err(|e| format!("Failed to write stdin: {}", e))?;
    }

    let output = child
        .wait_with_output()
        .map_err(|e| format!("Process error: {}", e))?;

    if output.status.success() {
        let stdout =
            String::from_utf8_lossy(&output.stdout).to_string();
        Ok(stdout)
    } else {
        let stderr =
            String::from_utf8_lossy(&output.stderr).to_string();
        Err(stderr)
    }
}
