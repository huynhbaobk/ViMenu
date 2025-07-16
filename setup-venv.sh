#!/bin/bash

echo "🚀 Initializing Python project with uv..."

# Step 1: Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' is not installed. Please run: pip install uv"
    exit 1
fi

# Step 2: Initialize pyproject.toml if not present
if [ ! -f pyproject.toml ]; then
    echo "📄 Creating pyproject.toml..."
    uv init
fi

# Step 3: Read requirements.txt and add packages to pyproject.toml
if [ -f requirements.txt ]; then
    echo "📦 Adding packages from requirements.txt to pyproject.toml..."
    xargs uv add < requirements.txt
else
    echo "⚠️ No requirements.txt found, skipping dependency addition."
fi

# Step 4: Create virtual environment and install
echo "📂 Creating virtual environment..."
uv venv
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# echo "📥 Installing dependencies from pyproject.toml..."
# uv pip install --project

# Step 5: Create quick activation file
cat > activate.sh << 'EOF'
#!/bin/bash
echo "🍜 Activating Menu Analyzer environment..."
source .venv/bin/activate
echo "✅ Environment activated! Run 'python -m app.main' to start"
echo "💡 For mock mode: './run-mock.sh'"
EOF

chmod +x activate.sh

echo ""
echo "✅ Setup complete!"
echo "🎯 Run:"
echo "   source activate.sh"
echo "   python -m app.main"
