use std::fmt;
use std::process::{exit, Command};

use semver::{Version, VersionReq};

#[derive(Debug, Clone)]
struct PythonError;

impl std::error::Error for PythonError {}

impl fmt::Display for PythonError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Error while executing python command")
    }
}

fn get_python_version() -> Result<Version, PythonError> {
    // Get the current Python version

    let python_version = Command::new("cmd")
        .args(["/C", "python --version"])
        .output()
        .unwrap();

    if !python_version.status.success() {
        return Err(PythonError);
    }

    let string_output = String::from_utf8(python_version.stdout).unwrap();
    let full_version = string_output.split_whitespace().last().unwrap();

    let version = Version::parse(full_version).unwrap();

    Ok(version)
}

fn create_venv() {
    println!("Creating Python virtual environment ...");

    let python_venv = Command::new("cmd")
        .args(["/C", "python -m venv env"])
        .output()
        .unwrap();

    println!(
        "Venv stdout: {}",
        String::from_utf8(python_venv.stdout).unwrap()
    );
    if !python_venv.status.success() {
        println!(
            "Venv stderr: {}",
            String::from_utf8(python_venv.stderr).unwrap()
        );
    }
}

fn installing_packages(version: &Version) {
    println!("Installing packages for Python {}...", version);

    let minor_version;
    if version.minor < 10 {
        minor_version = format!("0{}", version.minor)
    } else {
        minor_version = format!("{}", version.minor)
    }

    let requirement = format!("requirement-{}{}.txt", version.major, minor_version);

    let command = format!(".\\env\\Scripts\\pip.exe install -r {}", requirement);

    println!("pip install commande is: {}", command);

    let pip_install = Command::new("cmd").args(["/C", &command]).output().unwrap();

    println!(
        "Install stdout: {}",
        String::from_utf8(pip_install.stdout).unwrap()
    );

    if !pip_install.status.success() {
        println!(
            "Install stderr: {}",
            String::from_utf8(pip_install.stderr).unwrap()
        );
    }
}

fn main() {
    let python_requirements = VersionReq::parse(">=3.9, <=3.11").unwrap();

    let python_version = match get_python_version() {
        Ok(version) => version,
        Err(PythonError) => {
            println!("Python isn't correctly installed or isn't in PATH");
            std::io::stdin().read_line(&mut String::new()).unwrap();
            exit(1)
        }
    };

    println!("Python version is: {}", python_version);

    if !python_requirements.matches(&python_version) {
        println!("The current Python version isn't supported.");
        std::io::stdin().read_line(&mut String::new()).unwrap();
        exit(1)
    }

    create_venv();
    installing_packages(&python_version);

    println!("Done, press enter to exit");
    std::io::stdin().read_line(&mut String::new()).unwrap();
}
