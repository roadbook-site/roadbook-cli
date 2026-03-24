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
INIT_PY_PATH = PROJECT_ROOT / "src" / "roadbook" / "__init__.py"
DIST_DIR = PROJECT_ROOT / "dist"
SKILLS_DIR = PROJECT_ROOT / "skills"

def run_cmd(cmd, cwd=PROJECT_ROOT):
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(1)

def get_current_version():
    current_version_py = "Unknown"
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if match:
        current_version_py = match.group(1)

    return current_version_py


def is_valid_version(v: str) -> bool:
    """Validate version string. Accepts simple semver-like versions such as 1.2.3,
    and allows additional dot/dash separated identifiers (e.g. 1.2.3-alpha).
    This is intentionally permissive but prevents obvious bad values.
    """
    if not v:
        return False
    # simple semver-ish: MAJOR.MINOR.PATCH optionally followed by -label or .label
    import re
    pattern = r'^\d+\.\d+\.\d+(?:[-\.][0-9A-Za-z]+(?:[-\.][0-9A-Za-z]+)*)?$'
    return re.match(pattern, v) is not None

def update_skill_versions(new_version):
    """Update version in all SKILL.md files in the skills directory."""
    if not SKILLS_DIR.exists():
        print(f"⚠️ Skills directory not found at {SKILLS_DIR}")
        return
    
    # Find all SKILL.md files
    skill_files = list(SKILLS_DIR.glob("*/SKILL.md"))
    
    if not skill_files:
        print("⚠️ No SKILL.md files found")
        return
    
    for skill_file in skill_files:
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Update version field in frontmatter (YAML block)
            # Match version: "X.Y.Z" or version: 'X.Y.Z' or version: X.Y.Z (unquoted)
            updated_content = re.sub(
                r'version:\s*["\']?[^\n,\]]+["\']?',
                f'version: "{new_version}"',
                content,
                flags=re.MULTILINE,
                count=1
            )

            # If version field is missing in frontmatter, insert it after name.
            if updated_content == content:
                updated_content = re.sub(
                    r'(^name:\s*[^\n]+\n)',
                    r'\1version: "' + new_version + '"\n',
                    content,
                    flags=re.MULTILINE,
                    count=1,
                )
            
            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(updated_content)
            
            print(f"✅ Updated {skill_file.relative_to(PROJECT_ROOT)} to version {new_version}")
        except Exception as e:
            print(f"❌ Failed to update {skill_file}: {e}")

def update_version(new_version):
    with open(PYPROJECT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update version in pyproject.toml
    new_content = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )
    
    with open(PYPROJECT_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"✅ Updated pyproject.toml to version {new_version}")

    # Also update SKILL.md files
    update_skill_versions(new_version)

    # No longer updating __init__.py as it dynamically reads from package metadata

def clean_dist():
    if DIST_DIR.exists():
        print(f"🧹 Cleaning old builds in {DIST_DIR}...")
        shutil.rmtree(DIST_DIR)
    print("✅ Cleaned old builds.")

def main():
    print("🚀 === PyPI Publishing Assistant === 🚀")
    
    current_version = get_current_version()
    print(f"📦 Current version in pyproject.toml: {current_version}")
    
    # Ensure the version read from pyproject is valid-looking
    if not is_valid_version(current_version):
        print(f"⚠️ The version in pyproject.toml ('{current_version}') doesn't look valid.")
        print("Please enter a valid version (e.g. 1.2.3 or 1.2.3-alpha).")

    # Prompt user for new version and validate format before updating
    while True:
        new_version = input("\n👉 Enter the NEW version number (or press Enter to keep current): ").strip()
        if not new_version:
            print("⏭️ Keeping current version.")
            break

        # validate format
        if not is_valid_version(new_version):
            print(f"❌ '{new_version}' 不是合法的版本格式。示例: 1.2.3 或 1.2.3-alpha，请重新输入。")
            continue

        # If provided and different, update
        if new_version != current_version:
            update_version(new_version)
        else:
            print("ℹ️ 新版本与当前 pyproject.toml 相同，跳过更新。")
        break
    
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
