#!/usr/bin/env python3
"""
Cache Remover - Clear all Python cache files and directories
"""
import os
import shutil
import sys
from pathlib import Path


def remove_pycache_dirs(root_path: Path) -> int:
    """Remove all __pycache__ directories"""
    count = 0
    for pycache_dir in root_path.rglob("__pycache__"):
        if pycache_dir.is_dir():
            try:
                print(f"Removing directory: {pycache_dir}")
                shutil.rmtree(pycache_dir)
                count += 1
            except Exception as e:
                print(f"Error removing {pycache_dir}: {e}")
    return count


def remove_pyc_files(root_path: Path) -> int:
    """Remove all .pyc and .pyo files"""
    count = 0
    for pattern in ["*.pyc", "*.pyo"]:
        for pyc_file in root_path.rglob(pattern):
            if pyc_file.is_file():
                try:
                    print(f"Removing file: {pyc_file}")
                    pyc_file.unlink()
                    count += 1
                except Exception as e:
                    print(f"Error removing {pyc_file}: {e}")
    return count


def main():
    """Main function to clear Python cache"""
    print("🧹 Python Cache Remover")
    print("=" * 40)
    
    # Get the current directory or use provided path
    if len(sys.argv) > 1:
        root_path = Path(sys.argv[1])
    else:
        root_path = Path.cwd()
    
    if not root_path.exists():
        print(f"❌ Path does not exist: {root_path}")
        return 1
    
    print(f"📁 Scanning: {root_path.absolute()}")
    print()
    
    # Remove __pycache__ directories
    print("🗂️  Removing __pycache__ directories...")
    pycache_count = remove_pycache_dirs(root_path)
    
    print()
    
    # Remove .pyc and .pyo files
    print("📄 Removing .pyc and .pyo files...")
    pyc_count = remove_pyc_files(root_path)
    
    print()
    print("✅ Cache cleanup complete!")
    print(f"   • Removed {pycache_count} __pycache__ directories")
    print(f"   • Removed {pyc_count} bytecode files")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nPress Enter to exit...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        input("\nPress Enter to exit...")
        sys.exit(1)