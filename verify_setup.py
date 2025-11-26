"""
Quick setup verification script
Checks if all dependencies and configuration are in place
"""

import sys
import os


def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is too old. Need 3.8+")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    required = ['dotenv', 'google.adk']
    missing = []
    
    for package in required:
        try:
            if package == 'dotenv':
                import dotenv
                print(f"✅ python-dotenv installed")
            elif package == 'google.adk':
                import google.adk
                print(f"✅ google-adk installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} not installed")
    
    return len(missing) == 0, missing


def check_env_file():
    """Check if .env file exists and has API key"""
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("   Create it by copying .env.example: cp .env.example .env")
        return False
    
    print("✅ .env file exists")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print("⚠️  GOOGLE_API_KEY not set or using placeholder")
        print("   Edit .env and add your real API key")
        return False
    
    print("✅ GOOGLE_API_KEY is configured")
    return True


def main():
    """Run all verification checks"""
    print("=" * 60)
    print("🔍 SETUP VERIFICATION")
    print("=" * 60 + "\n")
    
    checks_passed = []
    
    # Check Python version
    checks_passed.append(check_python_version())
    print()
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    checks_passed.append(deps_ok)
    if not deps_ok:
        print(f"\n   Install missing packages: pip install {' '.join(missing)}")
    print()
    
    # Check .env file
    checks_passed.append(check_env_file())
    print()
    
    # Summary
    print("=" * 60)
    if all(checks_passed):
        print("✅ ALL CHECKS PASSED! You're ready to run main.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
