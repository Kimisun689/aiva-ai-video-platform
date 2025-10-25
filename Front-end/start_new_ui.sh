#!/bin/bash

echo "🚀 启动 AIVA 新版UI..."

# 检查是否安装了 Node.js
if command -v npx >/dev/null 2>&1; then
    echo "✅ 检测到 Node.js，使用 http-server"
    
    # 安装 http-server（如果没有安装）
    if ! command -v http-server >/dev/null 2>&1; then
        echo "📦 安装 http-server..."
        npm install -g http-server
    fi
    
    echo "🌐 启动前端服务器..."
    echo "📍 访问地址: http://localhost:8080/Generate_New.html"
    echo "🔧 服务器配置: CORS支持, SharedArrayBuffer支持"
    echo "⏹️  按 Ctrl+C 停止服务器"
    echo ""
    
    # 启动服务器，支持 CORS 和 SharedArrayBuffer
    http-server . -p 8080 -c-1 --cors -o Generate_New.html \
        -H "Cross-Origin-Opener-Policy: same-origin" \
        -H "Cross-Origin-Embedder-Policy: require-corp"
        
elif command -v python3 >/dev/null 2>&1; then
    echo "⚠️  未检测到 Node.js，使用 Python 服务器（功能有限）"
    echo "🌐 启动前端服务器..."
    echo "📍 访问地址: http://localhost:8080/Generate_New.html"
    echo "⚠️  注意: Python服务器不支持SharedArrayBuffer，视频合并功能可能受限"
    echo "⏹️  按 Ctrl+C 停止服务器"
    echo ""
    
    python3 -m http.server 8080
    
else
    echo "❌ 错误: 未检测到 Node.js 或 Python3"
    echo "请安装 Node.js: https://nodejs.org/"
    echo "或者安装 Python3: https://www.python.org/"
    exit 1
fi
