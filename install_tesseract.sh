#!/bin/bash
# Quick Tesseract Installation Script for macOS

echo "🔍 Checking for existing Tesseract installation..."

# Check if tesseract is already installed
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract is already installed!"
    tesseract --version
    exit 0
fi

echo "❌ Tesseract not found. Installing..."

# Check if Homebrew is available
if command -v brew &> /dev/null; then
    echo "🍺 Installing Tesseract via Homebrew..."
    brew install tesseract
    if [ $? -eq 0 ]; then
        echo "✅ Tesseract installed successfully via Homebrew!"
        tesseract --version
        exit 0
    else
        echo "❌ Homebrew installation failed"
    fi
fi

# Check if Conda is available
if command -v conda &> /dev/null; then
    echo "🐍 Installing Tesseract via Conda..."
    conda install -c conda-forge tesseract -y
    if [ $? -eq 0 ]; then
        echo "✅ Tesseract installed successfully via Conda!"
        tesseract --version
        exit 0
    else
        echo "❌ Conda installation failed"
    fi
fi

echo "⚠️  Neither Homebrew nor Conda found."
echo ""
echo "📋 Manual Installation Options:"
echo "1. Download from: https://github.com/UB-Mannheim/tesseract/wiki"
echo "2. Install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
echo "3. Install Conda: https://docs.conda.io/en/latest/miniconda.html"
echo ""
echo "After installation, run this script again to verify."
