import os
import shutil
import subprocess
import sys
import re
from pathlib import Path

# Setup paths based on the script location
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
DIST_DIR = PROJECT_ROOT / "dist"

def run_cmd(cmd, cwd=PROJECT_ROOT):
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(1)

def get_current_version():
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match:
        return match.group(1)
    return "Unknown"

def update_version(new_version):
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_content = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Updated pyproject.toml to version {new_version}")

def clean_dist():
    if DIST_DIR.exists():
        print(f"🧹 Cleaning old builds in {DIST_DIR}...")
        shutil.rmtree(DIST_DIR)
    print("✅ Cleaned old builds.")

def main():
    print("🚀 === PyPI Publishing Assistant === 🚀")
    
    current_version = get_current_version()
    print(f"📦 Current version in pyproject.toml: {current_version}")
    
    new_version = input("\n👉 Enter the NEW version number (or press Enter to keep current): ").strip()
    
    if new_version and new_version != current_version:
        update_version(new_version)
    else:
        print("⏭️ Keeping current version.")
    
    print("\n🔍 Step 1: Cleaning previous builds...")
    clean_dist()
    
    print("\n🔨 Step 2: Building package...")
    # Ensure build is installed
    run_cmd(f"{sys.executable} -m pip install --upgrade build twine")
    run_cmd(f"{sys.executable} -m build")
    
    print("\n✅ Build complete. Contents of dist/:")
    for f in DIST_DIR.iterdir():
        print(f"  - {f.name}")
    
    publish_choice = input("\n👉 Do you want to publish to PyPI now? (y/N): ").strip().lower()
    if publish_choice == 'y':
        print("\n🚀 Step 3: Uploading to PyPI...")
        run_cmd(f"{sys.executable} -m twine upload dist/*")
        print("\n🎉 Publish complete!")
    else:
        print("\n🛑 Publish cancelled. Your built package is ready in the 'dist/' directory.")

if __name__ == "__main__":
    main()
