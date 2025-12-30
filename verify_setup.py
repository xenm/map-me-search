"""
Quick setup verification script
Checks if all dependencies and configuration are in place
"""

import sys
import os


def check_python_version():
    """Check if Python version is 3.14+"""
    version = sys.version_info
    if version >= (3, 14):
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version {version.major}.{version.minor} is too old. Need 3.14+")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    required = ['google.adk']
    missing = []
    
    for package in required:
        try:
            if package == 'google.adk':
                import google.adk
                print(f"✅ google-adk installed")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} not installed")

    try:
        import dotenv
        print(f"✅ python-dotenv installed (optional)")
    except ImportError:
        print("⚠️  python-dotenv not installed (optional)")
    
    return len(missing) == 0, missing


def check_env_file():
    """Check if authentication is configured (Vertex AI ADC or API key)."""
    if os.path.exists('.env'):
        print("✅ .env file exists")
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            print("⚠️  python-dotenv not installed; skipping .env loading")
    else:
        print("⚠️  .env file not found (ok if using environment variables/ADC)")

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    api_key = os.environ.get("GOOGLE_API_KEY")

    if project and location:
        print("✅ Vertex AI env vars configured (GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION)")
        return True

    if api_key and api_key != "your_google_api_key_here":
        print("✅ GOOGLE_API_KEY is configured")
        return True

    print("❌ No valid authentication configuration found")
    print("   Configure one of the following:")
    print("   1) Vertex AI (recommended): set GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION and run `gcloud auth application-default login`")
    print("   2) Google AI Studio: set GOOGLE_API_KEY (e.g., in .env)")
    return False


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
        print("\n   Install missing packages: pip install google-adk")
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
