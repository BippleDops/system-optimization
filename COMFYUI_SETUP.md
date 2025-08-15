# 🎨 ComfyUI Setup Guide

## ✅ Configuration Applied

The ComfyUI configurations have been set up with:
1. **Optimized settings** for performance
2. **Model path sharing** with Stable Diffusion WebUI
3. **Proper directory structure**

## 📁 Files Configured

- `~/ComfyUI/extra_model_paths.yaml` - Model sharing configuration
- `~/ComfyUI/user/default/comfyui.settings.json` - UI and performance settings

## 🚀 Quick Start Commands

### From system-optimization directory:
```bash
cd ~/system-optimization

# Copy configurations
cp ai-configs/comfyui-settings.json ~/ComfyUI/user/default/
cp ai-configs/comfyui-model-paths.yaml ~/ComfyUI/extra_model_paths.yaml
```

### From anywhere:
```bash
# Copy configurations with full paths
cp ~/system-optimization/ai-configs/comfyui-settings.json ~/ComfyUI/user/default/
cp ~/system-optimization/ai-configs/comfyui-model-paths.yaml ~/ComfyUI/extra_model_paths.yaml
```

## 🏃 Running ComfyUI

### Option 1: With virtual environment
```bash
cd ~/ComfyUI
source venv/bin/activate
python main.py --listen
```

### Option 2: With system Python
```bash
cd ~/ComfyUI
python3 main.py --listen
```

### Option 3: With custom settings
```bash
cd ~/ComfyUI
python3 main.py --listen --port 8188 --preview-method auto
```

## 🔧 Model Sharing

The configuration allows ComfyUI to use models from Stable Diffusion WebUI:
- Checkpoints from `~/stable-diffusion-webui/models/Stable-diffusion`
- VAE from `~/stable-diffusion-webui/models/VAE`
- LoRA from `~/stable-diffusion-webui/models/Lora`
- ControlNet from `~/stable-diffusion-webui/models/ControlNet`

## 📊 Performance Optimizations

The settings include:
- BuildKit enabled for faster node execution
- Smart caching for models
- Optimized preview settings
- UI improvements for workflow management

## 🧹 Cleanup Options

### Remove Python cache (safe):
```bash
find ~/ComfyUI -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find ~/ComfyUI -name "*.pyc" -delete 2>/dev/null
```

### Remove virtual environment (if not using):
```bash
# Only if you use system Python instead
rm -rf ~/ComfyUI/venv
```

## 🔍 Verification

Check if ComfyUI is properly configured:
```bash
# Check configuration files
ls -la ~/ComfyUI/*.yaml
ls -la ~/ComfyUI/user/default/*.json

# Check model directories
ls -la ~/ComfyUI/models/
```

## 📝 Notes

- **ObsidianTTRPGVault**: Avoiding modifications to `/Users/jongosussmango/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianTTRPGVault Experimental` as requested
- **Virtual Environment**: The venv exists but can be removed if you prefer system Python
- **Model Sharing**: Saves disk space by sharing models with SD-WebUI

## 🌐 Access ComfyUI

Once running, access at:
- Local: http://localhost:8188
- Network: http://[your-ip]:8188

## 🎯 Next Steps

1. Start ComfyUI with your preferred method
2. Install any missing custom nodes via Manager
3. Load example workflows from the UI
4. Configure additional model paths if needed
