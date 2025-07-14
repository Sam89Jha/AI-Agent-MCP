#!/bin/bash

# Clean Repository Script
# Removes files and folders that should not be in version control

set -e

echo "🧹 Cleaning NavieTakieSimulation Repository"
echo "==========================================="

# Function to safely remove files/directories
safe_remove() {
    local path="$1"
    if [ -e "$path" ]; then
        echo "🗑️  Removing: $path"
        rm -rf "$path"
    fi
}

echo "📦 Removing Python cache files..."
# Remove __pycache__ directories
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Remove .pyc, .pyo files
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
find . -name "*.pyd" -delete 2>/dev/null || true

echo "🐍 Removing virtual environment..."
safe_remove "venv/"
safe_remove "env/"
safe_remove ".venv/"

echo "📦 Removing Node.js dependencies..."
safe_remove "frontend/dax-app/node_modules/"
safe_remove "frontend/pax-app/node_modules/"

echo "🏗️  Removing build directories..."
safe_remove "frontend/dax-app/build/"
safe_remove "frontend/pax-app/build/"
safe_remove "frontend/dax-app/dist/"
safe_remove "frontend/pax-app/dist/"

echo "☁️  Removing AWS/Terraform files..."
safe_remove ".terraform/"
safe_remove "*.tfstate"
safe_remove "*.tfstate.*"
safe_remove "*.tfplan"
safe_remove "terraform/lambda-functions.zip"

echo "💻 Removing IDE files..."
safe_remove ".vscode/"
safe_remove ".idea/"
safe_remove "*.swp"
safe_remove "*.swo"

echo "🖥️  Removing OS files..."
safe_remove ".DS_Store"
safe_remove "Thumbs.db"

echo "📝 Removing log files..."
find . -name "*.log" -delete 2>/dev/null || true
safe_remove "logs/"

echo "🔧 Removing environment files..."
safe_remove ".env"
safe_remove ".env.local"
safe_remove ".env.development.local"
safe_remove ".env.test.local"
safe_remove ".env.production.local"

echo "📦 Removing Python package files..."
safe_remove "*.egg-info/"
safe_remove "dist/"
safe_remove "build/"

echo "🧪 Removing test coverage files..."
safe_remove "htmlcov/"
safe_remove ".coverage"
safe_remove ".coverage.*"
safe_remove "coverage.xml"
safe_remove "*.cover"
safe_remove ".hypothesis/"
safe_remove ".pytest_cache/"

echo "📓 Removing Jupyter files..."
safe_remove ".ipynb_checkpoints"

echo "🔐 Removing sensitive files..."
safe_remove "secrets.json"
safe_remove "local_config.py"

echo "🗂️  Removing temporary files..."
find . -name "*.tmp" -delete 2>/dev/null || true
find . -name "*.temp" -delete 2>/dev/null || true
safe_remove "temp/"
safe_remove "tmp/"

echo ""
echo "✅ Repository cleaned successfully!"
echo ""
echo "📋 Files removed:"
echo "  - Python cache files (__pycache__, *.pyc, *.pyo)"
echo "  - Virtual environment (venv/)"
echo "  - Node.js dependencies (node_modules/)"
echo "  - Build directories (build/, dist/)"
echo "  - Terraform state files"
echo "  - IDE settings (.vscode/, .idea/)"
echo "  - OS files (.DS_Store, Thumbs.db)"
echo "  - Log files (*.log)"
echo "  - Environment files (.env*)"
echo "  - Python package files (*.egg-info/, dist/, build/)"
echo "  - Test coverage files"
echo "  - Temporary files"
echo ""
echo "🚀 You can now commit a clean repository to GitHub!"
echo ""
echo "💡 Next steps:"
echo "1. git add ."
echo "2. git commit -m 'Clean repository - remove ignored files'"
echo "3. git push"
echo ""
echo "🔄 After pushing, run: ./scripts/regenerate_files.sh" 