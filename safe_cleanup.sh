#!/bin/bash
# Safe System Cleanup Script
# This only deletes items that are 100% safe to remove

echo "🧹 Safe System Cleanup Script"
echo "============================="
echo ""
echo "This will clean up ~10 GB of definitely unused files."
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Track space before
BEFORE=$(df -h / | awk 'NR==2 {print $4}')
echo "Available space before: $BEFORE"
echo ""

# Python caches - 100% safe
echo "🐍 Cleaning Python caches..."
find ~/ComfyUI -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find ~/ComfyUI -name "*.pyc" -delete 2>/dev/null
find ~/ComfyUI -name "*.pyo" -delete 2>/dev/null
find ~/stable-diffusion-webui -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find ~/stable-diffusion-webui -name "*.pyc" -delete 2>/dev/null
find ~/stable-diffusion-webui -name "*.pyo" -delete 2>/dev/null
echo "  ✓ Python caches cleaned"

# Browser caches - safe to delete
echo "🌐 Cleaning browser caches..."
rm -rf ~/Library/Caches/Arc/* 2>/dev/null
rm -rf ~/Library/Caches/Comet/* 2>/dev/null
rm -rf ~/Library/Caches/Firefox/* 2>/dev/null
rm -rf ~/Library/Caches/com.spotify.client/* 2>/dev/null
echo "  ✓ Browser caches cleaned"

# Development caches - safe to delete
echo "💻 Cleaning development caches..."
rm -rf ~/Library/Caches/pip/* 2>/dev/null
rm -rf ~/Library/Caches/Homebrew/* 2>/dev/null
rm -rf ~/.cache/uv/* 2>/dev/null
rm -rf ~/.cache/puppeteer/* 2>/dev/null
rm -rf ~/Library/Caches/node-gyp/* 2>/dev/null
rm -rf ~/Library/Caches/claude-cli-nodejs/* 2>/dev/null
echo "  ✓ Development caches cleaned"

# Temp directories - safe to delete
echo "📁 Cleaning temp directories..."
rm -rf ~/.npm/_cacache/tmp/* 2>/dev/null
rm -rf ~/.docker/modules/tmp/* 2>/dev/null
rm -rf ~/.gemini/tmp/* 2>/dev/null
rm -rf ~/Library/Biome/tmp/* 2>/dev/null
echo "  ✓ Temp directories cleaned"

# Docker cleanup - safe
echo "🐳 Cleaning Docker..."
docker system prune -f 2>/dev/null || echo "  ! Docker not running"

# Cursor extension caches - safe
echo "📝 Cleaning Cursor caches..."
find ~/.cursor/extensions -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find ~/.cursor/extensions -name "*.pyc" -delete 2>/dev/null
echo "  ✓ Cursor caches cleaned"

# Track space after
AFTER=$(df -h / | awk 'NR==2 {print $4}')
echo ""
echo "✅ Cleanup complete!"
echo "Available space after: $AFTER"
echo "Space before: $BEFORE"
echo ""
echo "For additional cleanup, answer the questions in CLEANUP_REPORT.md"
