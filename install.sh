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
else
    echo "   ❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi
echo ""

# Check if pip3 is available
echo "2️⃣  Checking pip..."
if command -v pip3 &> /dev/null; then
    echo "   ✅ pip3 found"
else
    echo "   ❌ pip3 not found. Please install pip."
    exit 1
fi
echo ""

# Install dependencies
echo "3️⃣  Installing dependencies..."
pip3 install -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Create .env file if it doesn't exist
echo "4️⃣  Setting up environment file..."
if [ -f ".env" ]; then
    echo "   ⚠️  .env file already exists. Skipping creation."
else
    cp .env.example .env
    echo "   ✅ .env file created from template"
    echo ""
    echo "   ⚠️  IMPORTANT: Edit .env and add your GOOGLE_API_KEY"
    echo "   Get your API key from: https://aistudio.google.com/app/apikey"
fi
echo ""

# Test imports
echo "5️⃣  Testing imports..."
python3 test_imports.py
echo ""

echo "============================================================"
echo "✅ Installation Complete!"
echo "============================================================"
echo ""
echo "📝 Next Steps:"
echo ""
echo "1. Get your Google API key from:"
echo "   https://aistudio.google.com/app/apikey"
echo ""
echo "2. Edit the .env file and add your API key:"
echo "   nano .env"
echo ""
echo "3. Verify your setup:"
echo "   python3 verify_setup.py"
echo ""
echo "4. Run the application:"
echo "   python3 main.py"
echo ""
echo "📚 Documentation:"
echo "   - Quick Start: QUICKSTART.md"
echo "   - Full Setup: SETUP.md"
echo "   - Commands: COMMANDS.md"
echo ""
echo "🎉 Happy searching!"
echo ""
