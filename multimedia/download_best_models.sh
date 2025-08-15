#!/bin/bash

# Download and Configure Best Video/Image Generation Models
# This script sets up the recommended models for optimal performance

echo "🚀 Setting Up Best Video & Image Generation Models"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Base directories
COMFYUI_DIR="$HOME/ComfyUI"
SD_WEBUI_DIR="$HOME/stable-diffusion-webui"
MODEL_DIR="$HOME/system-optimization/multimedia/models"
CACHE_DIR="$HOME/.cache/huggingface"

# Create directories
mkdir -p "$MODEL_DIR/video"
mkdir -p "$MODEL_DIR/image"
mkdir -p "$MODEL_DIR/checkpoints"
mkdir -p "$CACHE_DIR"

echo -e "${BLUE}📦 Installing required Python packages...${NC}"
pip3 install -q huggingface-hub diffusers transformers accelerate opencv-python-headless

# Function to download from HuggingFace
download_hf_model() {
    local repo=$1
    local name=$2
    local type=$3
    
    echo -e "${BLUE}Downloading $name from HuggingFace...${NC}"
    
    # Check if already exists
    if [ -d "$MODEL_DIR/$type/$name" ]; then
        echo -e "${YELLOW}  ⚠️  $name already exists, skipping${NC}"
        return
    fi
    
    # Download using huggingface-cli
    if command -v huggingface-cli &> /dev/null; then
        huggingface-cli download "$repo" \
            --local-dir "$MODEL_DIR/$type/$name" \
            --local-dir-use-symlinks False \
            2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✅ $name downloaded successfully${NC}"
        else
            echo -e "${RED}  ❌ Failed to download $name${NC}"
        fi
    else
        echo -e "${RED}  ❌ huggingface-cli not found. Install with: pip install huggingface-hub${NC}"
    fi
}

# Function to pull Ollama models
pull_ollama_model() {
    local model=$1
    local description=$2
    
    echo -e "${BLUE}Pulling Ollama model: $model...${NC}"
    
    # Check if Ollama is running
    if ! pgrep -x "ollama" > /dev/null; then
        echo -e "${YELLOW}  ⚠️  Starting Ollama service...${NC}"
        ollama serve &
        sleep 3
    fi
    
    # Pull the model
    ollama pull "$model"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}  ✅ $model pulled successfully - $description${NC}"
    else
        echo -e "${RED}  ❌ Failed to pull $model${NC}"
    fi
}

# Function to setup ComfyUI models
setup_comfyui_model() {
    local url=$1
    local name=$2
    local target_dir=$3
    
    echo -e "${BLUE}Setting up ComfyUI model: $name...${NC}"
    
    if [ ! -d "$COMFYUI_DIR" ]; then
        echo -e "${YELLOW}  ⚠️  ComfyUI not found at $COMFYUI_DIR${NC}"
        return
    fi
    
    mkdir -p "$target_dir"
    
    # Download the model
    if [ ! -f "$target_dir/$name" ]; then
        echo -e "  Downloading $name..."
        curl -L "$url" -o "$target_dir/$name" --progress-bar
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}  ✅ $name downloaded to ComfyUI${NC}"
        else
            echo -e "${RED}  ❌ Failed to download $name${NC}"
        fi
    else
        echo -e "${YELLOW}  ⚠️  $name already exists${NC}"
    fi
}

echo ""
echo "════════════════════════════════════════"
echo "     🎬 VIDEO GENERATION MODELS"
echo "════════════════════════════════════════"

# 1. Download VideoCrafter (smaller, good quality)
echo -e "\n${BLUE}1. VideoCrafter - Zeroscope v2${NC}"
echo "   High-quality video generation (1024x576)"
download_hf_model "cerspense/zeroscope_v2_576w" "zeroscope_v2" "video"

# 2. Setup AnimateDiff for ComfyUI
echo -e "\n${BLUE}2. AnimateDiff for ComfyUI${NC}"
echo "   Animate still images with motion"
if [ -d "$COMFYUI_DIR" ]; then
    ANIMATEDIFF_DIR="$COMFYUI_DIR/models/animatediff"
    mkdir -p "$ANIMATEDIFF_DIR"
    
    # Download AnimateDiff motion modules
    setup_comfyui_model \
        "https://huggingface.co/guoyww/animatediff/resolve/main/mm_sd_v15_v2.ckpt" \
        "mm_sd_v15_v2.ckpt" \
        "$ANIMATEDIFF_DIR"
else
    echo -e "${YELLOW}  ⚠️  ComfyUI not found, skipping AnimateDiff${NC}"
fi

# 3. Stable Video Diffusion
echo -e "\n${BLUE}3. Stable Video Diffusion${NC}"
echo "   Image-to-video generation"
download_hf_model "stabilityai/stable-video-diffusion-img2vid-xt" "stable-video-diffusion" "video"

echo ""
echo "════════════════════════════════════════"
echo "     🖼️ IMAGE GENERATION MODELS"
echo "════════════════════════════════════════"

# 4. SDXL Models for ComfyUI/SD-WebUI
echo -e "\n${BLUE}4. SDXL Models${NC}"
if [ -d "$COMFYUI_DIR" ] || [ -d "$SD_WEBUI_DIR" ]; then
    CHECKPOINT_DIR="$COMFYUI_DIR/models/checkpoints"
    [ ! -d "$CHECKPOINT_DIR" ] && CHECKPOINT_DIR="$SD_WEBUI_DIR/models/Stable-diffusion"
    
    # Download SDXL base (smaller version)
    setup_comfyui_model \
        "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0_0.9vae.safetensors" \
        "sdxl_base_1.0.safetensors" \
        "$CHECKPOINT_DIR"
    
    # Download SDXL Turbo (fast generation)
    setup_comfyui_model \
        "https://huggingface.co/stabilityai/sdxl-turbo/resolve/main/sd_xl_turbo_1.0_fp16.safetensors" \
        "sdxl_turbo_1.0.safetensors" \
        "$CHECKPOINT_DIR"
else
    echo -e "${YELLOW}  ⚠️  Neither ComfyUI nor SD-WebUI found${NC}"
fi

# 5. Download smaller FLUX model (if space permits)
echo -e "\n${BLUE}5. FLUX Schnell (Fast version)${NC}"
echo "   Black Forest Labs' fast image model"
# Note: FLUX models are large, only download if requested
echo -e "${YELLOW}  ℹ️  FLUX models are large (10-20GB). Download manually if needed:${NC}"
echo "     huggingface-cli download black-forest-labs/FLUX.1-schnell"

echo ""
echo "════════════════════════════════════════"
echo "     🤖 VISION LLM MODELS (Ollama)"
echo "════════════════════════════════════════"

# 6. Pull vision-capable Ollama models
echo -e "\n${BLUE}6. Vision-capable LLMs for Ollama${NC}"

# LLaVA - Best for image understanding
pull_ollama_model "llava:7b" "Vision-language model for image understanding"

# BakLLaVA - Alternative vision model
pull_ollama_model "bakllava:7b" "High-quality vision model"

# Moondream - Lightweight vision model
pull_ollama_model "moondream:latest" "Lightweight vision model (1.8B params)"

echo ""
echo "════════════════════════════════════════"
echo "     📊 MODEL SETUP SUMMARY"
echo "════════════════════════════════════════"

# Check what was successfully installed
echo -e "\n${GREEN}✅ Checking installed models:${NC}"

# Check video models
echo -e "\n${BLUE}Video Models:${NC}"
[ -d "$MODEL_DIR/video/zeroscope_v2" ] && echo -e "  ✅ VideoCrafter/Zeroscope"
[ -f "$COMFYUI_DIR/models/animatediff/mm_sd_v15_v2.ckpt" ] && echo -e "  ✅ AnimateDiff"
[ -d "$MODEL_DIR/video/stable-video-diffusion" ] && echo -e "  ✅ Stable Video Diffusion"

# Check image models
echo -e "\n${BLUE}Image Models:${NC}"
[ -f "$COMFYUI_DIR/models/checkpoints/sdxl_base_1.0.safetensors" ] || \
[ -f "$SD_WEBUI_DIR/models/Stable-diffusion/sdxl_base_1.0.safetensors" ] && echo -e "  ✅ SDXL Base"
[ -f "$COMFYUI_DIR/models/checkpoints/sdxl_turbo_1.0.safetensors" ] || \
[ -f "$SD_WEBUI_DIR/models/Stable-diffusion/sdxl_turbo_1.0.safetensors" ] && echo -e "  ✅ SDXL Turbo"

# Check Ollama models
echo -e "\n${BLUE}Vision LLMs (Ollama):${NC}"
ollama list 2>/dev/null | grep -q "llava" && echo -e "  ✅ LLaVA"
ollama list 2>/dev/null | grep -q "bakllava" && echo -e "  ✅ BakLLaVA"
ollama list 2>/dev/null | grep -q "moondream" && echo -e "  ✅ Moondream"

echo ""
echo "════════════════════════════════════════"
echo -e "${GREEN}🎉 Model Setup Complete!${NC}"
echo "════════════════════════════════════════"
echo ""
echo "📝 Next Steps:"
echo "  1. Start the video generation server:"
echo "     python3 video_generation_server.py"
echo ""
echo "  2. Test video generation:"
echo "     curl -X POST http://localhost:8006/api/video/generate \\"
echo "       -H 'Content-Type: application/json' \\"
echo "       -d '{\"prompt\": \"A serene mountain landscape\", \"model\": \"videocrafter1\"}'"
echo ""
echo "  3. For large models (HunyuanVideo, FLUX full):"
echo "     These require 20-40GB each. Download manually if you have space:"
echo "     - huggingface-cli download Tencent/HunyuanVideo"
echo "     - huggingface-cli download black-forest-labs/FLUX.1-dev"
echo ""
echo "  4. Configure ComfyUI workflows:"
echo "     The models are now available in ComfyUI/SD-WebUI"
echo ""
echo "════════════════════════════════════════"
