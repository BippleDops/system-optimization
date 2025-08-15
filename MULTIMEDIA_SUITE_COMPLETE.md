# 🎬 Multimedia Generation Suite - Complete Setup

## ✅ What's Been Created

### 1. **Audio Generation Server** (Port 8001)
- Text-to-Speech using Mac's native voices
- Music generation from text prompts  
- Audio effects processing (reverb, echo, pitch shift)
- Multi-track audio mixing

### 2. **Obsidian Management Server** (Port 8002)
- Smart note creation with templates
- Advanced search (content, tags, backlinks)
- Knowledge graph generation
- Automated workflows (daily notes, weekly reviews)
- **Respects your excluded vault**: ObsidianTTRPGVault Experimental

### 3. **Mac Automation Server** (Port 8003)
- System monitoring (CPU, memory, disk)
- File organization by rules
- Desktop cleanup automation
- App management (launch, quit, list)
- Clipboard management
- Apple Shortcuts integration

### 4. **Unified Media Pipeline** (Port 8004)
- Orchestrates all services
- Generate images, audio, video from text
- Create storyboards with narration
- Auto-generate content (blogs, presentations)
- Custom multi-step workflows

### 5. **Local LLM Server** (Port 8005)
- **Integrated with YOUR Ollama installation**
- Chat, completion, and embeddings
- RAG (Retrieval-Augmented Generation)
- Function calling simulation
- WebSocket streaming

### 6. **ComfyUI Integration** (Port 8188)
- Text-to-image workflows
- Image-to-video animation
- Style transfer
- AI upscaling

## 🚀 Quick Start

```bash
# Start all servers at once
cd ~/system-optimization/multimedia
./start_all_servers.sh

# Or start individually
python3 audio_generation_server.py      # Port 8001
python3 obsidian_server.py              # Port 8002
python3 mac_automation_server.py        # Port 8003
python3 unified_media_pipeline.py       # Port 8004
python3 local_llm_server.py             # Port 8005
```

## 🤖 Your Ollama Models

Your Ollama is already running with these models ready to use:

| Model | Size | Best For |
|-------|------|----------|
| **llama3.1:8b** | 4.9 GB | General purpose, default model |
| **mistral:7b-instruct** | 4.4 GB | Chat and instruction following |
| **deepseek-coder:6.7b-instruct** | 3.8 GB | Code generation and debugging |
| **qwen2:7b-instruct** | 4.4 GB | Multilingual tasks |
| **llama3.2:3b** | 2.0 GB | Fast responses, lightweight |
| **phi3:mini** | 2.2 GB | Quick tasks, low memory |
| **gpt-oss:20b** | 13 GB | Complex reasoning, advanced tasks |

## 🎯 Example Workflows

### Generate Blog Post with Images
```bash
curl -X POST "http://localhost:8004/api/content/create" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Future of AI",
    "content_type": "blog",
    "include_images": true
  }'
```

### Create Daily Note in Obsidian
```bash
curl -X POST "http://localhost:8002/api/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_type": "daily_note",
    "parameters": {}
  }'
```

### Generate Code with DeepSeek
```bash
curl -X POST "http://localhost:8005/api/completion" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-coder:6.7b-instruct",
    "prompt": "Write a Python web scraper for news articles",
    "temperature": 0.3
  }'
```

### Text to Speech
```bash
curl -X POST "http://localhost:8001/api/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Welcome to your multimedia generation suite",
    "voice": "Samantha"
  }'
```

### Clean Downloads Folder
```bash
curl -X POST "http://localhost:8003/api/automation/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "cleanup_downloads",
    "parameters": {"days_old": 30, "dry_run": false}
  }'
```

## 📊 Service Status Check

```bash
cd ~/system-optimization/multimedia
./check_servers.sh
```

## 🛠️ API Documentation

Each server has interactive API docs:
- Audio: http://localhost:8001/docs
- Obsidian: http://localhost:8002/docs
- Mac: http://localhost:8003/docs
- Pipeline: http://localhost:8004/docs
- LLM: http://localhost:8005/docs

## 💡 Natural Language Examples

### "Create a video about space exploration"
```python
import requests

# Generate video with narration
response = requests.post("http://localhost:8004/api/generate", json={
    "prompt": "A journey through the cosmos exploring distant galaxies",
    "media_type": "video",
    "duration": 30
})
```

### "Organize my desktop and create a summary"
```python
# Clean desktop
requests.post("http://localhost:8003/api/automation/execute", json={
    "action": "organize_desktop",
    "parameters": {"dry_run": False}
})

# Generate summary with LLM
requests.post("http://localhost:8005/api/chat", json={
    "model": "llama3.1:8b",
    "messages": [
        {"role": "user", "content": "Summarize what was organized on my desktop"}
    ]
})
```

## 🔮 Advanced Features

### Custom Workflow Chains
Create complex multi-step workflows that combine all services:
1. Generate content with LLM
2. Create images with ComfyUI
3. Add narration with TTS
4. Save to Obsidian
5. Organize files

### RAG with Local Documents
```python
# Use your documents as context
response = requests.post("http://localhost:8005/api/rag", json={
    "query": "What are the key points from my meeting notes?",
    "context": ["meeting note content here..."],
    "model": "llama3.1:8b"
})
```

## 🚫 Respecting Boundaries

The system respects your request to avoid:
- `/Users/jongosussmango/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianTTRPGVault Experimental`

## 📈 Performance Tips

- Use **llama3.2:3b** or **phi3:mini** for fast responses
- Use **deepseek-coder** specifically for code tasks
- Use **gpt-oss:20b** for complex reasoning (slower but more capable)
- Run `./stop_all_servers.sh` when not in use to free resources

## 🎉 You're All Set!

Your multimedia generation suite is ready to:
- Generate any type of media from text
- Automate your Mac and Obsidian workflows
- Use your local Ollama models for AI tasks
- Create complex content pipelines
- All running locally on your machine!

---

GitHub Repository: https://github.com/BippleDops/system-optimization
