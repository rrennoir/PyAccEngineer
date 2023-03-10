use std::process::{exit, Command};

fn check_python() -> bool {
    // Check if python is installed

    let output = Command::new("cmd")
        .args(["/C", "python --version"])
        .output()
        .unwrap();

    output.stderr.len() == 0
}

fn get_python_version() -> String {
    const VERSIONS: [&str; 2] = ["3.9", "3.11"];

    loop {
        println!("Select the python version you have installed [3.9, 3.11]");

        let mut input = String::new();
        std::io::stdin()
            .read_line(&mut input)
            .expect("Failed to read stdin");

        let version = input.trim();

        if VERSIONS.contains(&version) {
            return version.to_string();
        }
    }
}

fn create_venv(version: &String) {
    println!("Creating virtual environment for Python {}...", version);

    let output = Command::new("cmd")
        .args(["/C", "python -m venv env"])
        .output()
        .unwrap();

    println!("Venv stdout: {}", String::from_utf8(output.stdout).unwrap());
    println!("Venv stderr: {}", String::from_utf8(output.stderr).unwrap());
}

fn installing_packages(version: &String) {
    println!("Installing packages for Python {}...", version);

    let req_version = if version == "3.9" { "309" } else { "311" };

    let command = format!(
        ".\\env\\Scripts\\pip.exe install -r requirement-{}.txt",
        req_version
    );

    println!("{}", command);

    let output = Command::new("cmd").args(["/C", &command]).output().unwrap();

    println!(
        "Install stdout: {}",
        String::from_utf8(output.stdout).unwrap()
    );
    println!(
        "Install stderr: {}",
        String::from_utf8(output.stderr).unwrap()
    );
}

fn main() {
    if !check_python() {
        println!("Python isn't correctly installed, not found in PATH !");
        exit(1)
    }

    let version = get_python_version();

    create_venv(&version);
    installing_packages(&version);

    println!("Done, press enter to exit");
    std::io::stdin().read_line(&mut String::new()).unwrap();
}
