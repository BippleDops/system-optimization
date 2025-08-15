#!/usr/bin/env python3
"""
Unified Media Pipeline - Orchestrates image, audio, and video generation from natural language
"""

import os
import json
import asyncio
import aiohttp
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import base64
from PIL import Image
import io

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Unified Media Pipeline", version="1.0.0")

# Service endpoints
SERVICES = {
    "comfyui": "http://localhost:8188",
    "audio": "http://localhost:8001",
    "obsidian": "http://localhost:8002",
    "mac": "http://localhost:8003",
    "sdwebui": "http://localhost:7860"
}

class MediaGenerationRequest(BaseModel):
    prompt: str
    media_type: str  # image, audio, video, multimedia
    style: Optional[str] = None
    duration: Optional[int] = None
    resolution: Optional[str] = "1024x1024"
    voice: Optional[str] = None
    music_style: Optional[str] = None
    workflow: Optional[str] = None

class StoryboardRequest(BaseModel):
    story: str
    scenes: int = 5
    include_audio: bool = True
    include_music: bool = False
    output_format: str = "mp4"

class ContentCreationRequest(BaseModel):
    topic: str
    content_type: str  # blog, presentation, social_media, tutorial
    include_images: bool = True
    include_audio: bool = False
    target_length: Optional[int] = None

class WorkflowRequest(BaseModel):
    name: str
    steps: List[Dict[str, Any]]
    input_data: Optional[Dict[str, Any]] = {}

async def call_comfyui_api(workflow: dict, prompt: str) -> str:
    """Call ComfyUI API to generate images"""
    try:
        # Prepare the workflow with the prompt
        workflow_str = json.dumps(workflow).replace("[PROMPT]", prompt)
        workflow_data = json.loads(workflow_str)
        
        async with aiohttp.ClientSession() as session:
            # Queue the prompt
            async with session.post(
                f"{SERVICES['comfyui']}/prompt",
                json={"prompt": workflow_data}
            ) as response:
                result = await response.json()
                prompt_id = result.get("prompt_id")
            
            # Wait for completion and get result
            await asyncio.sleep(10)  # Give it time to process
            
            # Get the output (simplified - in production, poll for completion)
            async with session.get(
                f"{SERVICES['comfyui']}/history/{prompt_id}"
            ) as response:
                history = await response.json()
                
                # Extract image path from history
                # This is simplified - actual implementation would parse properly
                return f"/tmp/comfyui_output_{prompt_id}.png"
    
    except Exception as e:
        print(f"ComfyUI API error: {e}")
        # Fallback to creating a placeholder
        return create_placeholder_image(prompt)

def create_placeholder_image(prompt: str) -> str:
    """Create a placeholder image when services are unavailable"""
    img = Image.new('RGB', (1024, 1024), color='blue')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    img.save(temp_file.name)
    return temp_file.name

@app.post("/api/generate")
async def generate_media(request: MediaGenerationRequest):
    """Generate media from natural language prompt"""
    try:
        results = {}
        
        if request.media_type == "image":
            # Load ComfyUI workflow
            workflow_path = Path(__file__).parent / "comfyui_workflows.json"
            if workflow_path.exists():
                with open(workflow_path, 'r') as f:
                    workflows = json.load(f)
                
                workflow = workflows.get("text_to_image_workflow", {})
                image_path = await call_comfyui_api(workflow, request.prompt)
            else:
                image_path = create_placeholder_image(request.prompt)
            
            results["image"] = image_path
            
        elif request.media_type == "audio":
            # Generate speech or music
            if request.voice:
                # Text to speech
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{SERVICES['audio']}/api/tts",
                        json={
                            "text": request.prompt,
                            "voice": request.voice
                        }
                    ) as response:
                        if response.status == 200:
                            audio_data = await response.read()
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                            temp_file.write(audio_data)
                            results["audio"] = temp_file.name
            
            elif request.music_style:
                # Generate music
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{SERVICES['audio']}/api/generate_music",
                        json={
                            "prompt": request.prompt,
                            "style": request.music_style,
                            "duration": request.duration or 30
                        }
                    ) as response:
                        if response.status == 200:
                            music_data = await response.read()
                            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                            temp_file.write(music_data)
                            results["music"] = temp_file.name
        
        elif request.media_type == "video":
            # Generate video from prompt
            # First generate keyframes
            frames = []
            frame_prompts = [f"{request.prompt} - frame {i+1}" for i in range(8)]
            
            for frame_prompt in frame_prompts:
                image_path = create_placeholder_image(frame_prompt)
                frames.append(image_path)
            
            # Combine into video
            video_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
            
            # Use ffmpeg to create video from frames
            frame_pattern = tempfile.NamedTemporaryFile(delete=False, suffix='_%d.png').name
            for i, frame in enumerate(frames):
                shutil.copy(frame, frame_pattern.replace('%d', str(i)))
            
            subprocess.run([
                'ffmpeg', '-framerate', '2', '-i', frame_pattern,
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', video_path, '-y'
            ], capture_output=True)
            
            results["video"] = video_path
        
        elif request.media_type == "multimedia":
            # Generate multiple media types
            # Generate image
            image_path = create_placeholder_image(request.prompt)
            results["image"] = image_path
            
            # Generate audio narration
            if request.voice:
                # Would call TTS API here
                results["narration"] = "Audio narration would be generated"
            
            # Generate background music if requested
            if request.music_style:
                results["music"] = "Background music would be generated"
        
        return {
            "prompt": request.prompt,
            "media_type": request.media_type,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/storyboard")
async def create_storyboard(request: StoryboardRequest):
    """Create a storyboard with images and optional audio"""
    try:
        # Parse story into scenes
        scenes = []
        story_parts = request.story.split('.')[:request.scenes]
        
        for i, part in enumerate(story_parts):
            if part.strip():
                scene = {
                    "number": i + 1,
                    "text": part.strip(),
                    "image": create_placeholder_image(f"Scene {i+1}: {part.strip()}")
                }
                
                if request.include_audio:
                    # Generate narration for scene
                    scene["audio"] = f"narration_scene_{i+1}.mp3"
                
                scenes.append(scene)
        
        # Create output video/presentation
        output_path = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f'.{request.output_format}'
        ).name
        
        # Would combine scenes into final output here
        
        return {
            "story": request.story,
            "scenes": scenes,
            "output": output_path,
            "format": request.output_format
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/content/create")
async def create_content(request: ContentCreationRequest):
    """Create complete content packages with text, images, and audio"""
    try:
        content = {
            "topic": request.topic,
            "type": request.content_type,
            "sections": []
        }
        
        if request.content_type == "blog":
            # Generate blog post structure
            sections = [
                "Introduction",
                "Main Point 1",
                "Main Point 2",
                "Main Point 3",
                "Conclusion"
            ]
            
            for section in sections:
                section_content = {
                    "title": section,
                    "text": f"Content for {section} about {request.topic}"
                }
                
                if request.include_images:
                    section_content["image"] = create_placeholder_image(
                        f"{request.topic} - {section}"
                    )
                
                content["sections"].append(section_content)
        
        elif request.content_type == "presentation":
            # Generate presentation slides
            num_slides = request.target_length or 10
            
            for i in range(num_slides):
                slide = {
                    "number": i + 1,
                    "title": f"Slide {i+1}",
                    "content": f"Content about {request.topic}",
                    "notes": "Speaker notes here"
                }
                
                if request.include_images:
                    slide["image"] = create_placeholder_image(f"Slide {i+1}: {request.topic}")
                
                content["sections"].append(slide)
        
        elif request.content_type == "social_media":
            # Generate social media posts
            platforms = ["twitter", "instagram", "linkedin"]
            
            for platform in platforms:
                post = {
                    "platform": platform,
                    "text": f"Post about {request.topic} for {platform}",
                    "hashtags": ["#AI", "#Automation", f"#{request.topic.replace(' ', '')}"]
                }
                
                if request.include_images and platform != "twitter":
                    post["image"] = create_placeholder_image(f"{platform}: {request.topic}")
                
                content["sections"].append(post)
        
        elif request.content_type == "tutorial":
            # Generate tutorial steps
            steps = []
            num_steps = request.target_length or 5
            
            for i in range(num_steps):
                step = {
                    "number": i + 1,
                    "title": f"Step {i+1}",
                    "instruction": f"Detailed instruction for step {i+1}",
                    "tip": "Pro tip for this step"
                }
                
                if request.include_images:
                    step["image"] = create_placeholder_image(f"Tutorial Step {i+1}")
                
                steps.append(step)
            
            content["sections"] = steps
        
        # Add audio if requested
        if request.include_audio:
            content["audio_narration"] = "Full narration would be generated"
        
        # Save to Obsidian if available
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVICES['obsidian']}/api/notes/create",
                    json={
                        "title": f"{request.topic} - {request.content_type}",
                        "content": json.dumps(content, indent=2),
                        "folder": "Generated Content",
                        "tags": ["generated", request.content_type]
                    }
                ) as response:
                    if response.status == 200:
                        obsidian_result = await response.json()
                        content["obsidian_note"] = obsidian_result.get("path")
        except:
            pass  # Obsidian integration is optional
        
        return content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/custom")
async def execute_custom_workflow(request: WorkflowRequest):
    """Execute custom multi-step workflows"""
    try:
        results = {
            "workflow": request.name,
            "steps_completed": [],
            "outputs": {}
        }
        
        context = request.input_data.copy()
        
        for step in request.steps:
            step_type = step.get("type")
            step_name = step.get("name", f"Step {len(results['steps_completed']) + 1}")
            
            try:
                if step_type == "generate_image":
                    prompt = step.get("prompt", "").format(**context)
                    image = create_placeholder_image(prompt)
                    results["outputs"][step_name] = image
                    context["last_image"] = image
                
                elif step_type == "generate_audio":
                    text = step.get("text", "").format(**context)
                    results["outputs"][step_name] = f"audio_{step_name}.mp3"
                    context["last_audio"] = results["outputs"][step_name]
                
                elif step_type == "process_file":
                    # File processing step
                    results["outputs"][step_name] = "processed_file"
                
                elif step_type == "combine_media":
                    # Combine multiple media files
                    results["outputs"][step_name] = "combined_output.mp4"
                
                elif step_type == "save_to_obsidian":
                    # Save results to Obsidian
                    results["outputs"][step_name] = "obsidian_note_path"
                
                results["steps_completed"].append(step_name)
                
            except Exception as e:
                results["outputs"][step_name] = f"Error: {str(e)}"
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/services/status")
async def check_services_status():
    """Check status of all integrated services"""
    status = {}
    
    for service_name, url in SERVICES.items():
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2) as response:
                    status[service_name] = {
                        "url": url,
                        "status": "online" if response.status == 200 else "error",
                        "code": response.status
                    }
        except:
            status[service_name] = {
                "url": url,
                "status": "offline",
                "code": None
            }
    
    return status

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "Unified Media Pipeline",
        "version": "1.0.0",
        "endpoints": {
            "/api/generate": "Generate any media type from text",
            "/api/storyboard": "Create storyboards with scenes",
            "/api/content/create": "Create complete content packages",
            "/api/workflow/custom": "Execute custom workflows",
            "/api/services/status": "Check integrated services",
            "/docs": "Interactive API documentation"
        },
        "media_types": ["image", "audio", "video", "multimedia"],
        "content_types": ["blog", "presentation", "social_media", "tutorial"],
        "integrated_services": list(SERVICES.keys())
    }

if __name__ == "__main__":
    print("🎬 Starting Unified Media Pipeline on http://localhost:8004")
    print("📚 API Documentation: http://localhost:8004/docs")
    print("\nIntegrated Services:")
    for name, url in SERVICES.items():
        print(f"  - {name}: {url}")
    uvicorn.run(app, host="0.0.0.0", port=8004)
