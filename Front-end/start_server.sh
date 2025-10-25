#!/bin/bash

echo "🚀 Starting AIVA Frontend Server..."
echo ""

# 检查是否安装了 http-server
if command -v npx &> /dev/null; then
    echo "✅ Using npx http-server with proper CORS headers..."
    npx http-server -p 8080 --cors -H "Cross-Origin-Opener-Policy: same-origin" -H "Cross-Origin-Embedder-Policy: require-corp"
elif command -v python3 &> /dev/null; then
    echo "⚠️  Using Python server (limited CORS support)"
    echo "   For full video combining functionality, please install Node.js and npm"
    echo "   Then run: npm install -g http-server"
    echo ""
    echo "   Current server may not support video combining due to browser security restrictions."
    echo "   You can still use the manual download option."
    echo ""
    python3 -m http.server 8080
else
    echo "❌ Neither npx nor python3 found. Please install Node.js or Python."
    exit 1
fi 