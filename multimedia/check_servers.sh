#!/bin/bash

# Check Status of All Servers

echo "📊 Server Status Check"
echo "====================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Function to check server
check_server() {
    local name=$1
    local port=$2
    local url=$3
    
    printf "%-25s Port %-5s: " "$name" "$port"
    
    if curl -s -f -o /dev/null "$url" 2>/dev/null; then
        echo -e "${GREEN}✅ Online${NC}"
    elif lsof -Pi :${port} -sTCP:LISTEN -t >/dev/null 2>/dev/null; then
        echo -e "${GREEN}🟡 Running (API not responding)${NC}"
    else
        echo -e "${RED}❌ Offline${NC}"
    fi
}

# Check each server
check_server "Audio Generation" 8001 "http://localhost:8001"
check_server "Obsidian Management" 8002 "http://localhost:8002"
check_server "Mac Automation" 8003 "http://localhost:8003"
check_server "Media Pipeline" 8004 "http://localhost:8004"
check_server "ComfyUI" 8188 "http://localhost:8188"
check_server "SD WebUI" 7860 "http://localhost:7860"

echo ""
echo "Quick Links:"
echo "  Audio API Docs:    http://localhost:8001/docs"
echo "  Obsidian API Docs: http://localhost:8002/docs"
echo "  Mac API Docs:      http://localhost:8003/docs"
echo "  Pipeline API Docs: http://localhost:8004/docs"
