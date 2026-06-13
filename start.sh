#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo "============================================="
echo " English Buddy — Starting local server..."
echo "============================================="
echo ""

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY not set!"
    echo ""
    echo "Set it permanently:"
    echo "  echo 'export ANTHROPIC_API_KEY=sk-ant-your-key' >> ~/.zshrc"
    echo "  source ~/.zshrc"
    echo ""
    exit 1
fi

echo "API key found: ${ANTHROPIC_API_KEY:0:8}..."
echo "Opening: http://localhost:8765/english_buddy.html"
echo "Use Google Chrome only"
echo ""

sleep 1
open "http://localhost:8765/english_buddy.html" 2>/dev/null || \
  xdg-open "http://localhost:8765/english_buddy.html" 2>/dev/null &

python3 backend/server.py
