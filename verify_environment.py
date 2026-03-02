#!/usr/bin/env python3
"""
Verify Virtual Environment Setup
Tests that all required packages are installed correctly
"""

import sys
import importlib
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version meets requirements"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (needs 3.9+)")
        return False


def check_venv():
    """Check if running in virtual environment"""
    print("\n📦 Checking virtual environment...")
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if in_venv:
        print(f"   ✅ Virtual environment active: {sys.prefix}")
        return True
    else:
        print(f"   ⚠️  Not in virtual environment")
        print(f"   💡 Run: source venv/bin/activate")
        return False


def check_package(package_name, import_name=None, optional=False):
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"   ✅ {package_name} ({version})")
        return True
    except ImportError as e:
        if optional:
            print(f"   ⚠️  {package_name} - not installed")
        else:
            print(f"   ❌ {package_name} - {e}")
        return False
    except (AttributeError, RuntimeError, Exception) as e:
        # Handle compatibility issues (e.g., ultralytics with opencv)
        error_msg = str(e)
        if optional:
            print(f"   ⚠️  {package_name} - {error_msg[:60]}...")
        else:
            print(f"   ⚠️  {package_name} - installed but has compatibility issues")
            print(f"       Error: {error_msg[:80]}...")
        return optional  # Optional packages can fail, required ones cannot


def check_core_packages():
    """Check core dependencies"""
    print("\n🔧 Checking core packages...")
    packages = [
        ('Flask', 'flask'),
        ('Flask-CORS', 'flask_cors'),
        ('requests', 'requests'),
        ('APScheduler', 'apscheduler'),
        ('python-dotenv', 'dotenv'),
        ('pydantic', 'pydantic'),
        ('colorlog', 'colorlog'),
    ]
    
    results = []
    for pkg_name, import_name in packages:
        results.append(check_package(pkg_name, import_name))
    
    return all(results)


def check_data_packages():
    """Check data processing packages"""
    print("\n📊 Checking data processing packages...")
    packages = [
        ('numpy', 'numpy'),
        ('Pillow', 'PIL'),
        ('python-dateutil', 'dateutil'),
    ]
    
    results = []
    for pkg_name, import_name in packages:
        results.append(check_package(pkg_name, import_name))
    
    return all(results)


def check_camera_ml():
    """Check camera and ML packages"""
    print("\n📷 Checking camera & ML packages...")
    
    # Check opencv first
    cv2_ok = check_package('opencv-python', 'cv2')
    
    # Check ultralytics separately with better error handling
    print("\n   Checking ultralytics (YOLO)...")
    try:
        # Try to check if ultralytics is installed via pip
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', 'ultralytics'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            # Package is installed, try to import
            try:
                import ultralytics
                version = getattr(ultralytics, '__version__', 'unknown')
                print(f"   ✅ ultralytics ({version})")
                yolo_ok = True
            except (ImportError, AttributeError) as e:
                print(f"   ⚠️  ultralytics - installed but import failed")
                print(f"       This may be due to opencv compatibility issues")
                print(f"       Error: {str(e)[:80]}...")
                yolo_ok = False
        else:
            print(f"   ❌ ultralytics - not installed")
            yolo_ok = False
    except Exception as e:
        print(f"   ⚠️  ultralytics - could not verify: {str(e)[:60]}")
        yolo_ok = False
    
    return cv2_ok  # Only require opencv, ultralytics is optional for now


def check_hardware():
    """Check hardware packages"""
    print("\n🔌 Checking hardware packages...")
    packages = [
        ('smbus2', 'smbus2'),
    ]
    
    # Optional packages
    optional = [
        ('RPi.GPIO', 'RPi.GPIO'),
        ('spidev', 'spidev'),
    ]
    
    results = []
    for pkg_name, import_name in packages:
        results.append(check_package(pkg_name, import_name))
    
    print("\n   Optional (Raspberry Pi only):")
    for pkg_name, import_name in optional:
        try:
            importlib.import_module(import_name)
            print(f"   ✅ {pkg_name}")
        except (ImportError, RuntimeError) as e:
            # RuntimeError occurs when RPi.GPIO is installed but not on Raspberry Pi
            if 'Raspberry Pi' in str(e):
                print(f"   ⚠️  {pkg_name} (installed but not on Raspberry Pi - will use mock)")
            else:
                print(f"   ⚠️  {pkg_name} (not installed - will use mock)")
    
    return all(results)


def check_conflicting_packages():
    """Check for packages that might cause conflicts"""
    print("\n⚠️  Checking for conflicting packages...")
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'list'],
            capture_output=True,
            text=True,
            check=True
        )
        
        conflicts = []
        for line in result.stdout.splitlines():
            if 'label-studio' in line.lower():
                conflicts.append(line.strip())
            if 'opencv-python-headless' in line.lower():
                conflicts.append(line.strip())
        
        if conflicts:
            print("   ⚠️  Found potentially conflicting packages:")
            for pkg in conflicts:
                print(f"      - {pkg}")
            print("   💡 See DEPENDENCY_CONFLICTS.md for solutions")
            return False
        else:
            print("   ✅ No conflicting packages found")
            return True
    except subprocess.CalledProcessError:
        print("   ⚠️  Could not check for conflicts")
        return True


def check_project_files():
    """Check that essential project files exist"""
    print("\n📁 Checking project files...")
    
    essential_files = [
        'main.py',
        'config.py',
        'hardware_control.py',
        'server.py',
        'requirements.txt',
        'setup_venv.sh',
    ]
    
    results = []
    for filename in essential_files:
        path = Path(filename)
        if path.exists():
            print(f"   ✅ {filename}")
            results.append(True)
        else:
            print(f"   ❌ {filename} not found")
            results.append(False)
    
    return all(results)


def check_opencv_ultralytics_compatibility():
    """Check for known opencv-ultralytics compatibility issues"""
    print("\n🔍 Checking opencv-ultralytics compatibility...")
    
    try:
        import cv2
        # Try the problematic attribute
        if hasattr(cv2, 'setNumThreads'):
            print("   ✅ OpenCV has setNumThreads (compatible)")
            return True
        else:
            print("   ⚠️  OpenCV missing setNumThreads (incompatible with ultralytics)")
            print("   💡 Solution:")
            print("      1. Uninstall opencv-python-headless: pip uninstall opencv-python-headless")
            print("      2. Reinstall opencv-python: pip install --force-reinstall opencv-python==4.8.1.78")
            return False
    except ImportError:
        print("   ❌ OpenCV not installed")
        return False
    except Exception as e:
        print(f"   ⚠️  Could not check compatibility: {e}")
        return False


def main():
    """Run all checks"""
    print("=" * 60)
    print("🔍 GrowUp IoT - Environment Verification")
    print("=" * 60)
    
    checks = [
        check_python_version(),
        check_venv(),
        check_core_packages(),
        check_data_packages(),
        check_opencv_ultralytics_compatibility(),
        check_camera_ml(),
        check_hardware(),
        check_conflicting_packages(),
        check_project_files(),
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("✅ All checks passed! Environment is ready.")
        print("\n💡 Next steps:")
        print("   python test_system.py    # Test system components")
        print("   python main.py --demo    # Run in demo mode")
        print("=" * 60)
        return 0
    else:
        print("❌ Some checks failed. Please review the output above.")
        print("\n💡 Common solutions:")
        print("   ./setup_venv.sh                      # Create clean environment")
        print("   source venv/bin/activate             # Activate environment")
        print("   pip install -r requirements/dev.txt  # Install dependencies")
        print("\n📚 Documentation:")
        print("   QUICKSTART.md             # Quick reference")
        print("   INSTALL.md                # Installation guide")
        print("   DEPENDENCY_CONFLICTS.md   # Conflict resolution")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
