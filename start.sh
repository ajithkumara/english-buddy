#!/bin/bash
echo ""
echo "============================================="
echo " English Buddy — Starting local server..."
echo "============================================="
echo ""
echo " Open this URL in Google Chrome:"
echo " http://localhost:8765/frontend/english_buddy.html"
echo ""
sleep 1
open "http://localhost:8765/frontend/english_buddy.html" 2>/dev/null || \
  xdg-open "http://localhost:8765/frontend/english_buddy.html" 2>/dev/null
python3 backend/server.py
