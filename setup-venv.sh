#!/bin/bash

echo "🚀 Initializing Python project with uv..."

# Step 1: Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' is not installed. Please run: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Step 2: Create virtual environment and sync dependencies
echo "� Creating virtual environment and installing dependencies..."
uv sync

# Step 3: Activate virtual environment
echo "✅ Virtual environment created successfully!"
echo "� To activate the environment, run: source .venv/bin/activate"
echo "🚀 To run the application, use: uv run uvicorn app.main:app --reload"
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
