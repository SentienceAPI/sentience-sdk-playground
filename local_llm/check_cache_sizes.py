#!/usr/bin/env python3
"""
Check cache sizes on Mac before cleanup
Shows what's taking up space without deleting anything
"""
import os
import subprocess
import shutil
from pathlib import Path


def get_dir_size(path):
    """Get directory size in bytes"""
    if not os.path.exists(path):
        return 0

    total = 0
    try:
        for entry in os.scandir(path):
            if entry.is_file(follow_symlinks=False):
                total += entry.stat().st_size
            elif entry.is_dir(follow_symlinks=False):
                total += get_dir_size(entry.path)
    except (PermissionError, OSError):
        pass
    return total


def format_size(bytes_size):
    """Convert bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def check_path(path, description, can_delete=True):
    """Check if path exists and show size"""
    path_obj = Path(path).expanduser()

    if not path_obj.exists():
        print(f"  ❌ {description}")
        print(f"     Not found: {path_obj}")
        return 0

    size = get_dir_size(str(path_obj))

    if size == 0:
        print(f"  ⚪ {description}")
        print(f"     Location: {path_obj}")
        print(f"     Size: Empty")
        return 0

    delete_msg = "✅ Can delete" if can_delete else "⚠️  Be careful"
    print(f"  {delete_msg} {description}")
    print(f"     Location: {path_obj}")
    print(f"     Size: {format_size(size)}")

    return size


def run_command(cmd, description):
    """Run command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def main():
    """Main function"""
    print("=" * 70)
    print(" " * 20 + "MAC CACHE SIZE CHECKER")
    print("=" * 70)
    print("\nThis script shows what's taking up space WITHOUT deleting anything.")
    print()

    total_size = 0
    home = str(Path.home())

    # 1. Conda
    print("\n" + "=" * 70)
    print("1. CONDA CACHE")
    print("=" * 70)

    conda_paths = [
        (f"{home}/.conda/pkgs", "Conda packages cache", True),
        (f"{home}/.conda/envs", "Conda environments", False),
        (f"{home}/anaconda3/pkgs", "Anaconda packages cache", True),
        (f"{home}/miniconda3/pkgs", "Miniconda packages cache", True),
    ]

    for path, desc, can_delete in conda_paths:
        total_size += check_path(path, desc, can_delete)

    if shutil.which("conda"):
        print("\n  💡 To clean conda cache, run:")
        print("     conda clean --all -y")

    # 2. Pip
    print("\n" + "=" * 70)
    print("2. PIP CACHE")
    print("=" * 70)

    pip_cache = run_command("pip cache dir 2>/dev/null || echo ''", "Get pip cache dir")
    if pip_cache:
        total_size += check_path(pip_cache, "Pip cache", True)
    else:
        total_size += check_path(f"{home}/Library/Caches/pip", "Pip cache (fallback)", True)

    print("\n  💡 To clean pip cache, run:")
    print("     pip cache purge")

    # 3. Hugging Face
    print("\n" + "=" * 70)
    print("3. HUGGING FACE / ML MODEL CACHE")
    print("=" * 70)

    hf_paths = [
        (f"{home}/.cache/huggingface", "Hugging Face models cache", False),
        (f"{home}/.cache/torch", "PyTorch cache", True),
        (f"{home}/.cache/transformers", "Transformers cache (old)", True),
    ]

    for path, desc, can_delete in hf_paths:
        total_size += check_path(path, desc, can_delete)

    print("\n  ⚠️  WARNING: Only delete Hugging Face cache if you want to re-download models!")

    # 4. NPM
    print("\n" + "=" * 70)
    print("4. NPM CACHE")
    print("=" * 70)

    npm_cache = run_command("npm config get cache 2>/dev/null || echo ''", "Get npm cache dir")
    if npm_cache:
        total_size += check_path(npm_cache, "NPM cache", True)

    print("\n  💡 To clean npm cache, run:")
    print("     npm cache clean --force")

    # 5. Homebrew
    print("\n" + "=" * 70)
    print("5. HOMEBREW CACHE")
    print("=" * 70)

    brew_cache = run_command("brew --cache 2>/dev/null || echo ''", "Get brew cache dir")
    if brew_cache:
        total_size += check_path(brew_cache, "Homebrew cache", True)

    if shutil.which("brew"):
        print("\n  💡 To clean Homebrew cache, run:")
        print("     brew cleanup -s")

    # 6. System caches
    print("\n" + "=" * 70)
    print("6. APPLICATION CACHES")
    print("=" * 70)

    app_caches = [
        (f"{home}/Library/Caches/Google/Chrome", "Google Chrome cache", True),
        (f"{home}/Library/Caches/Firefox", "Firefox cache", True),
        (f"{home}/Library/Caches/com.apple.Safari", "Safari cache", True),
        (f"{home}/Library/Caches/com.microsoft.VSCode", "VS Code cache", True),
        (f"{home}/Library/Caches/com.apple.dt.Xcode", "Xcode cache", True),
        (f"{home}/Library/Developer/Xcode/DerivedData", "Xcode derived data", True),
        (f"{home}/Library/Caches/com.docker.docker", "Docker cache", True),
    ]

    for path, desc, can_delete in app_caches:
        total_size += check_path(path, desc, can_delete)

    # 7. Development caches
    print("\n" + "=" * 70)
    print("7. DEVELOPMENT CACHES")
    print("=" * 70)

    dev_caches = [
        (f"{home}/.gradle/caches", "Gradle cache", True),
        (f"{home}/.m2/repository", "Maven cache", False),
        (f"{home}/.cargo/registry", "Rust/Cargo cache", True),
        (f"{home}/go/pkg", "Go packages", False),
    ]

    for path, desc, can_delete in dev_caches:
        total_size += check_path(path, desc, can_delete)

    # 8. Logs
    print("\n" + "=" * 70)
    print("8. LOGS")
    print("=" * 70)

    total_size += check_path(f"{home}/Library/Logs", "Application logs", True)

    print("\n  💡 To clean old logs (>30 days), run:")
    print("     find ~/Library/Logs -type f -mtime +30 -delete")

    # 9. Trash
    print("\n" + "=" * 70)
    print("9. TRASH")
    print("=" * 70)

    total_size += check_path(f"{home}/.Trash", "Trash", True)

    print("\n  💡 To empty trash:")
    print("     rm -rf ~/.Trash/*")

    # 10. Docker
    print("\n" + "=" * 70)
    print("10. DOCKER")
    print("=" * 70)

    if shutil.which("docker"):
        docker_info = run_command(
            "docker system df 2>/dev/null || echo 'Docker not running'",
            "Docker system usage"
        )
        print(f"\n{docker_info}")
        print("\n  💡 To clean Docker:")
        print("     docker system prune -a --volumes")
    else:
        print("  ❌ Docker not installed")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nTotal cache size found: {format_size(total_size)}")

    # Show disk usage
    print("\nCurrent disk usage:")
    disk_usage = run_command("df -h / | tail -1", "Disk usage")
    print(f"  {disk_usage}")

    print("\n" + "=" * 70)
    print("RECOMMENDED CLEANUP STEPS")
    print("=" * 70)
    print("""
1. Safe to clean (will free space, no data loss):
   - conda clean --all -y
   - pip cache purge
   - npm cache clean --force
   - brew cleanup -s
   - rm -rf ~/.Trash/*

2. Clean if you want to re-download models:
   - rm -rf ~/.cache/huggingface

3. Clean application caches (apps will rebuild):
   - Quit all browsers first, then delete browser caches

4. Clean development caches (will rebuild on next use):
   - rm -rf ~/.gradle/caches
   - rm -rf ~/.cargo/registry

5. Use the cleanup script:
   - bash cleanup_mac_cache.sh
""")

    print("\n" + "=" * 70)
    print("TO FIND LARGE FILES")
    print("=" * 70)
    print("""
Run these commands to find what's taking up space:

1. Find large files (>100MB):
   find ~ -type f -size +100M -exec ls -lh {} \\; 2>/dev/null | head -20

2. Find largest directories:
   du -sh ~/* | sort -hr | head -20

3. Install and use ncdu (visual disk usage):
   brew install ncdu
   ncdu ~
""")


if __name__ == "__main__":
    main()
