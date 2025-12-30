#!/bin/bash

# AI Places Search - Installation Script
# This script automates the setup process

set -e  # Exit on error

echo "============================================================"
echo "🚀 AI-Powered Places Search - Installation"
echo "============================================================"
echo ""

# Check Python version
echo "1️⃣  Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    echo "   ✅ Python $PYTHON_VERSION found"

    if ! python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 14) else 1)"; then
        echo "   ❌ Python $PYTHON_VERSION detected. This project requires Python 3.14+"
        exit 1
    fi
else
    echo "   ❌ Python 3 not found. Please install Python 3.14 or higher."
    exit 1
fi
echo ""

# Check if pip is available for python3
echo "2️⃣  Checking pip..."
if python3 -m pip --version &> /dev/null; then
    echo "   ✅ pip available"
else
    echo "   ❌ pip not available for python3. Please install pip."
    exit 1
fi
echo ""

# Install dependencies (always in a local virtual environment)
echo "3️⃣  Installing dependencies (venv)..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "   📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install
echo "   📦 Installing dependencies in virtual environment..."
source venv/bin/activate
python -m pip install -r requirements.txt
echo "   ✅ Dependencies installed in virtual environment"
echo ""

# Create .env file if it doesn't exist
echo "4️⃣  Setting up environment file..."
if [ -f ".env" ]; then
    echo "   ⚠️  .env file already exists. Skipping creation."
else
    cp .env.example .env
    echo "   ✅ .env file created from template"
    echo ""
    echo "   ⚠️  IMPORTANT: Edit .env and configure authentication"
    echo "   - Recommended: Vertex AI (ADC)"
    echo "   - Alternative: Google AI Studio (API key)"
fi
echo ""

# Test imports
echo "5️⃣  Testing imports..."
python test_imports.py
echo ""

echo "============================================================"
echo "✅ Installation Complete!"
echo "============================================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Configure authentication (see .env.example):"
echo "   - Vertex AI (recommended): gcloud auth application-default login + set GOOGLE_CLOUD_PROJECT/GOOGLE_CLOUD_LOCATION"
echo "   - AI Studio: set GOOGLE_API_KEY"
echo ""
echo "2. Edit the .env file to match your choice:"
echo "   nano .env"
echo ""
echo "3. Verify your setup:"
echo "   source venv/bin/activate"
echo "   python verify_setup.py"
echo ""

echo "4. Run the application:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""

echo "📚 Documentation:"
echo "   - Quick Start: docs/QUICKSTART.md"
echo ""
echo "🎉 Happy searching!"
echo ""
