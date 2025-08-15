# 🎬 Multimedia Generation & Automation Suite

A comprehensive suite of local servers for generating images, audio, video, and managing your Mac and Obsidian vault through natural language.

## 🚀 Quick Start

```bash
# Start all servers
./start_all_servers.sh

# Check server status
./check_servers.sh

# Stop all servers
./stop_all_servers.sh
```

## 🎨 Services Overview

### 1. **Audio Generation Server** (Port 8001)
- **Text-to-Speech**: Convert text to natural speech using Mac's built-in voices
- **Music Generation**: Create procedural music from text descriptions
- **Audio Processing**: Apply effects (reverb, echo, pitch shift, time stretch)
- **Audio Mixing**: Combine multiple audio tracks
- **API Docs**: http://localhost:8001/docs

### 2. **Obsidian Management Server** (Port 8002)
- **Smart Note Creation**: Create notes with templates and metadata
- **Advanced Search**: Search by content, title, tags, or backlinks
- **Knowledge Graph**: Generate visual representations of note connections
- **Automated Workflows**: Daily notes, weekly reviews, project setup
- **AI Assistance**: Summarize, expand, connect notes (hooks for AI integration)
- **API Docs**: http://localhost:8002/docs

### 3. **Mac Automation Server** (Port 8003)
- **System Monitoring**: CPU, memory, disk usage, running processes
- **File Organization**: Auto-organize files by rules and patterns
- **Automation Workflows**: Clean downloads, organize desktop, backup configs
- **App Management**: List, launch, quit applications
- **Task Scheduling**: Create recurring tasks with launchd
- **Clipboard Management**: Get, set, clear clipboard
- **Shortcuts Integration**: Run Apple Shortcuts programmatically
- **API Docs**: http://localhost:8003/docs

### 4. **Unified Media Pipeline** (Port 8004)
- **Multi-Modal Generation**: Create images, audio, and video from text
- **Storyboarding**: Generate visual storyboards with narration
- **Content Creation**: Auto-generate blogs, presentations, social media posts
- **Custom Workflows**: Chain multiple generation steps
- **Service Orchestration**: Coordinates all other services
- **API Docs**: http://localhost:8004/docs

### 5. **ComfyUI** (Port 8188)
- **Image Generation**: Text-to-image with SDXL models
- **Image-to-Video**: Animate still images
- **Style Transfer**: Apply artistic styles
- **Upscaling**: AI-powered image enhancement
- **Custom Workflows**: Load from `comfyui_workflows.json`

### 6. **Stable Diffusion WebUI** (Port 7860)
- **Advanced Image Generation**: Full SD capabilities
- **Model Management**: Switch between checkpoints
- **Extensions**: Additional features via extensions

## 📡 API Examples

### Generate an Image
```bash
curl -X POST "http://localhost:8004/api/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A futuristic city at sunset",
    "media_type": "image",
    "resolution": "1024x1024"
  }'
```

### Text to Speech
```bash
curl -X POST "http://localhost:8001/api/tts" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of the audio system",
    "voice": "Samantha",
    "speed": 1.0
  }'
```

### Create Obsidian Note
```bash
curl -X POST "http://localhost:8002/api/notes/create" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Meeting Notes",
    "content": "Discussion points from today",
    "folder": "Meetings",
    "tags": ["work", "important"]
  }'
```

### Organize Desktop
```bash
curl -X POST "http://localhost:8003/api/automation/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "organize_desktop",
    "parameters": {"dry_run": false}
  }'
```

### Create a Storyboard
```bash
curl -X POST "http://localhost:8004/api/storyboard" \
  -H "Content-Type: application/json" \
  -d '{
    "story": "A robot discovers a garden. It learns to care for plants. The garden flourishes.",
    "scenes": 3,
    "include_audio": true
  }'
```

## 🔧 Configuration

### ComfyUI Workflows
Edit `comfyui_workflows.json` to customize image generation workflows:
- `text_to_image_workflow`: Basic text-to-image
- `image_to_video_workflow`: Animate images
- `style_transfer_workflow`: Apply artistic styles
- `upscale_enhance_workflow`: Improve image quality

### Service Endpoints
Modify the `SERVICES` dictionary in `unified_media_pipeline.py` if your services run on different ports.

### Obsidian Vault Path
Update `OBSIDIAN_VAULT_PATH` in `obsidian_server.py` to point to your vault location.

## 🧩 Integration with Natural Language

### Example: "Create a blog post about AI with images"
```python
import requests

response = requests.post("http://localhost:8004/api/content/create", json={
    "topic": "The Future of AI",
    "content_type": "blog",
    "include_images": True,
    "include_audio": False
})

print(response.json())
```

### Example: "Generate a video from this story"
```python
response = requests.post("http://localhost:8004/api/generate", json={
    "prompt": "A time-lapse of a flower blooming in a magical forest",
    "media_type": "video",
    "duration": 10
})
```

## 🛠️ Requirements

### System Requirements
- macOS (for Mac automation features)
- Python 3.8+
- ffmpeg (for audio/video processing)
- ComfyUI (optional, for advanced image generation)
- Stable Diffusion WebUI (optional, for additional image generation)

### Python Dependencies
```bash
pip install fastapi uvicorn aiohttp psutil python-frontmatter Pillow pydantic
```

### Install ffmpeg
```bash
brew install ffmpeg
```

## 🔍 Troubleshooting

### Port Already in Use
If a port is already in use, either:
1. Stop the conflicting service
2. Change the port in the server script
3. The start script will skip already-running services

### Server Won't Start
Check the logs:
```bash
tail -f multimedia/logs/[service_name].log
```

### ComfyUI/SD WebUI Not Starting
Ensure they're installed in the expected locations:
- ComfyUI: `~/ComfyUI`
- SD WebUI: `~/stable-diffusion-webui`

## 🎯 Use Cases

### Content Creation Pipeline
1. Generate blog post structure with AI
2. Create images for each section
3. Add audio narration
4. Save to Obsidian vault
5. Export as presentation

### Daily Automation
1. Create daily note in Obsidian
2. Clean up Downloads folder
3. Organize Desktop
4. Generate summary of tasks
5. Create audio briefing

### Media Generation Workflow
1. Text prompt → Image generation
2. Image → Animation/video
3. Add generated music
4. Combine with narration
5. Export final video

## 📚 Advanced Features

### Custom Workflows
Create complex multi-step workflows:
```json
{
  "name": "podcast_episode",
  "steps": [
    {"type": "generate_audio", "text": "Introduction"},
    {"type": "generate_music", "style": "ambient"},
    {"type": "combine_media", "format": "mp3"}
  ]
}
```

### Batch Processing
Process multiple items:
```python
for topic in topics:
    generate_content(topic)
```

### Scheduled Tasks
Automate recurring workflows:
```bash
curl -X POST "http://localhost:8003/api/schedule/task" \
  -d '{"name": "daily_cleanup", "command": "cleanup.sh", "schedule": "daily"}'
```

## 🔐 Security Notes

- All servers run locally (localhost only by default)
- No authentication implemented (add if exposing to network)
- File operations restricted to user directories
- Respects the excluded ObsidianTTRPGVault directory

## 🚀 Future Enhancements

- [ ] Integration with local LLMs (Ollama, LM Studio)
- [ ] Advanced video generation with Stable Video Diffusion
- [ ] Real-time collaboration features
- [ ] Mobile app integration
- [ ] Voice command interface
- [ ] Automated content distribution
- [ ] AI model fine-tuning interface
- [ ] Performance monitoring dashboard

## 📝 License

This project is part of the system-optimization toolkit.

## 🤝 Contributing

Feel free to extend and customize these servers for your needs!
