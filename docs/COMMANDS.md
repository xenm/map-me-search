# 📋 Command Reference

## Installation Commands

### Install All Dependencies
```bash
pip install -r requirements.txt
```

Or install with pip3:
```bash
pip3 install -r requirements.txt
```

### Install Individual Packages
```bash
pip install google-adk
pip install python-dotenv
```

### Using Virtual Environment (Recommended)

**Create virtual environment**:
```bash
python3 -m venv venv
```

**Activate (macOS/Linux)**:
```bash
source venv/bin/activate
```

**Activate (Windows)**:
```bash
venv\Scripts\activate
```

**Install dependencies**:
```bash
pip install -r requirements.txt
```

**Deactivate**:
```bash
deactivate
```

## Setup Commands

### Create .env File
```bash
cp .env.example .env
```

Then edit `.env` with your favorite editor:
```bash
nano .env
# or
vim .env
# or
code .env
```

## Testing Commands

### Test Imports
```bash
python3 test_imports.py
```

### Verify Complete Setup
```bash
python3 verify_setup.py
```

## Running the Application

### Run Main Application
```bash
python3 main.py
```

### Run with Virtual Environment
```bash
source venv/bin/activate  # Activate first
python main.py            # Then run
```

## Development Commands

### Check Python Version
```bash
python3 --version
```

### List Installed Packages
```bash
pip list
```

### Update a Package
```bash
pip install --upgrade google-adk
```

### Check for Outdated Packages
```bash
pip list --outdated
```

## Troubleshooting Commands

### Reinstall Dependencies
```bash
pip uninstall google-adk python-dotenv
pip install google-adk python-dotenv
```

### Clear Python Cache
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```

### Check if .env File Exists
```bash
ls -la .env
```

### View .env File (Careful!)
```bash
cat .env
```

## Git Commands

### Initialize Git (if not done)
```bash
git init
```

### Check Git Status
```bash
git status
```

### Stage All Files
```bash
git add .
```

### Commit Changes
```bash
git commit -m "Initial commit: AI Places Search"
```

### View Git Ignored Files
```bash
git status --ignored
```

## File Management

### List Project Files
```bash
ls -lah
```

### View File Contents
```bash
cat main.py
cat requirements.txt
cat .env.example
```

### Search for Text in Files
```bash
grep -r "google_search" .
```

### Count Lines of Code
```bash
find . -name "*.py" -exec wc -l {} +
```

## Useful Aliases (Optional)

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
# Activate virtual environment
alias activate="source venv/bin/activate"

# Run main app
alias run-search="python3 main.py"

# Run verification
alias verify="python3 verify_setup.py"

# Quick test
alias test-imports="python3 test_imports.py"
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

## Quick Reference Card

| Task | Command |
|------|---------|
| Install deps | `pip install -r requirements.txt` |
| Create .env | `cp .env.example .env` |
| Test imports | `python3 test_imports.py` |
| Verify setup | `python3 verify_setup.py` |
| Run app | `python3 main.py` |
| Activate venv | `source venv/bin/activate` |

## Next Steps After Installation

1. ✅ Install dependencies
2. ✅ Create `.env` file with API key
3. ✅ Run `python3 verify_setup.py`
4. ✅ Run `python3 main.py`
5. ✅ Start searching for places!

---

💡 **Tip**: Bookmark this file for quick command reference!
