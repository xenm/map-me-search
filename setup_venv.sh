#!/bin/bash

# Quick virtual environment setup script
# Use this if you get "externally-managed-environment" error

echo "🔧 Setting up virtual environment for AI Places Search"
echo "========================================================"
echo ""

# Create virtual environment
echo "1️⃣  Creating virtual environment..."
python3 -m venv venv
echo "   ✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "2️⃣  Activating virtual environment..."
source venv/bin/activate
echo "   ✅ Virtual environment activated"
echo ""

# Install dependencies
echo "3️⃣  Installing dependencies..."
python -m pip install -r requirements.txt
echo "   ✅ Dependencies installed"
echo ""

# Create .env file if needed
echo "4️⃣  Setting up .env file..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✅ .env file created from template"
    echo ""
    echo "   ⚠️  IMPORTANT: Edit .env and configure authentication"
    echo "   - Recommended: Vertex AI (ADC)"
    echo "   - Alternative: Google AI Studio (API key)"
else
    echo "   ✅ .env file already exists"
fi
echo ""

# Test imports
echo "5️⃣  Testing imports..."
python test_imports.py
echo ""

echo "========================================================"
echo "✅ Setup Complete!"
echo "========================================================"
echo ""
echo "🚀 To run the application:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "💡 To activate venv in the future:"
echo "   source venv/bin/activate"
echo ""
echo "🔍 To verify setup:"
echo "   python verify_setup.py"
echo ""
