import os
import shutil
from pathlib import Path

def refactor_project(project_name: str = "png_tools"):
    """Refactors an existing project into a standard pyproject.toml structure."""
    
    # Determine the root directory (assuming this script is in utils/)
    root_dir = Path(__file__).resolve().parent.parent
    print(f"Refactoring project at: {root_dir}\n")
    
    # 1. Parse existing requirements.txt for dependencies
    req_file = root_dir / "requirements.txt"
    dependencies = []
    if req_file.exists():
        with open(req_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    dependencies.append(f'"{line}"')
        print(f"Found requirements: {', '.join(dependencies)}")
        
    deps_str = ",\n    ".join(dependencies)
    if deps_str:
        deps_str = f"\n    {deps_str}\n"

    # 2. Create standard directories
    directories = [
        f"src/{project_name}",
        "tests",
        ".github/workflows",
        "utils"
    ]
    
    for directory in directories:
        path = root_dir / directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {directory}")

    # Make them proper packages
    (root_dir / f"src/{project_name}/__init__.py").touch(exist_ok=True)
    (root_dir / "tests/__init__.py").touch(exist_ok=True)

    # 3. Move existing Python scripts to the src package
    py_scripts = list(root_dir.glob("*.py"))
    moved_scripts = []
    for script in py_scripts:
        # Skip setup/refactor scripts or anything in subdirectories
        if script.name in ["setup.py", "refactor_to_pyproject.py"] or script.is_dir():
            continue
            
        target = root_dir / f"src/{project_name}" / script.name
        shutil.move(str(script), str(target))
        moved_scripts.append(script.name)
        print(f"Moved script: {script.name} -> src/{project_name}/{script.name}")

    # 4. Generate pyproject.toml
    pyproject_content = f"""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{project_name}"
version = "0.1.0"
description = "PNG processing tools for Pac-Man project"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [{deps_str}]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
]
"""
    pyproject_path = root_dir / "pyproject.toml"
    if not pyproject_path.exists():
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(pyproject_content)
        print("Created pyproject.toml")
    else:
        print("pyproject.toml already exists, skipping creation.")

    # 5. Create .gitignore if it doesn't exist
    gitignore_path = root_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_content = "# Environments\n.env\n.venv\nenv/\nvenv/\n\n# Byte-compiled / optimized / DLL files\n__pycache__/\n*.py[cod]\n\n# Testing\n.pytest_cache/\n.coverage\n\n# IDEs\n.vscode/\n.idea/\n"
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(gitignore_content)
        print("Created .gitignore")

    # 6. Update shell scripts to point to new script locations
    sh_scripts = list(root_dir.glob("*.sh"))
    for sh_script in sh_scripts:
        content = sh_script.read_text()
        modified = False
        for script_name in moved_scripts:
            if script_name in content:
                content = content.replace(script_name, f"src/{project_name}/{script_name}")
                modified = True
        
        if modified:
            sh_script.write_text(content)
            print(f"Updated paths in {sh_script.name}")

    # 7. Rename old requirements.txt since it's now in pyproject.toml
    if req_file.exists():
        req_file.rename(root_dir / "requirements.txt.bak")
        print("Renamed requirements.txt to requirements.txt.bak")

    print("\nRefactor complete! Your project is now pyproject compatible.")

if __name__ == "__main__":
    refactor_project("png_tools")