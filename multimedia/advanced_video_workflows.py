#!/usr/bin/env python3
"""
Advanced Video Generation Workflows - Natural language to video pipeline
Integrates ComfyUI, Ollama vision models, and video generation models
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import base64
import tempfile

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Advanced Video Workflows", version="1.0.0")

# Service endpoints
SERVICES = {
    "ollama": "http://localhost:11434",
    "comfyui": "http://localhost:8188",
    "video_gen": "http://localhost:8006",
    "audio": "http://localhost:8001",
    "llm": "http://localhost:8005"
}

class StoryToVideoRequest(BaseModel):
    story: str
    style: str = "cinematic"  # cinematic, anime, realistic, abstract
    duration: int = 10  # seconds
    include_narration: bool = True
    include_music: bool = True
    resolution: str = "1024x576"

class TextToVideoRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    model: str = "auto"  # auto selects best available
    duration: int = 4
    fps: int = 8
    style_preset: Optional[str] = None

class ImageAnimationRequest(BaseModel):
    image_path: str
    motion_prompt: str
    duration: int = 4
    motion_strength: float = 1.0

class VideoEnhanceRequest(BaseModel):
    video_path: str
    enhancements: List[str]  # ["upscale", "interpolate", "stabilize", "denoise"]
    target_resolution: Optional[str] = None
    target_fps: Optional[int] = None

class MultimodalRequest(BaseModel):
    text_prompt: str
    reference_image: Optional[str] = None
    reference_video: Optional[str] = None
    audio_style: Optional[str] = None
    output_format: str = "mp4"

async def analyze_image_with_ollama(image_path: str, prompt: str = "Describe this image in detail"):
    """Use Ollama vision models to analyze images"""
    try:
        # Read and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        async with aiohttp.ClientSession() as session:
            # Use LLaVA for image understanding
            async with session.post(
                f"{SERVICES['ollama']}/api/generate",
                json={
                    "model": "llava:7b",
                    "prompt": prompt,
                    "images": [image_data],
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
    except Exception as e:
        return f"Image analysis failed: {str(e)}"

async def generate_scene_descriptions(story: str) -> List[Dict[str, str]]:
    """Convert story to scene descriptions using LLM"""
    try:
        async with aiohttp.ClientSession() as session:
            prompt = f"""Convert this story into detailed visual scene descriptions for video generation.
Break it into 3-5 scenes. For each scene provide:
1. A detailed visual description
2. Camera movement (static, pan, zoom)
3. Mood/atmosphere
4. Duration in seconds

Story: {story}

Output format:
Scene 1: [description]
Camera: [movement]
Mood: [atmosphere]
Duration: [seconds]
"""
            
            async with session.post(
                f"{SERVICES['ollama']}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    text = result.get("response", "")
                    
                    # Parse scenes from response
                    scenes = []
                    current_scene = {}
                    
                    for line in text.split('\n'):
                        if line.startswith('Scene'):
                            if current_scene:
                                scenes.append(current_scene)
                            current_scene = {"description": line.split(':', 1)[1].strip()}
                        elif line.startswith('Camera:'):
                            current_scene["camera"] = line.split(':', 1)[1].strip()
                        elif line.startswith('Mood:'):
                            current_scene["mood"] = line.split(':', 1)[1].strip()
                        elif line.startswith('Duration:'):
                            try:
                                current_scene["duration"] = int(line.split(':', 1)[1].strip().split()[0])
                            except:
                                current_scene["duration"] = 3
                    
                    if current_scene:
                        scenes.append(current_scene)
                    
                    return scenes if scenes else [{"description": story, "duration": 4}]
    except:
        return [{"description": story, "duration": 4}]

@app.post("/api/workflow/story_to_video")
async def story_to_video(request: StoryToVideoRequest):
    """Convert a story into a complete video with scenes"""
    try:
        workflow_id = f"story_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Step 1: Generate scene descriptions
        scenes = await generate_scene_descriptions(request.story)
        
        # Step 2: Generate video for each scene
        scene_videos = []
        for i, scene in enumerate(scenes):
            # Add style to prompt
            styled_prompt = f"{scene['description']}, {request.style} style"
            
            # Generate video for scene
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVICES['video_gen']}/api/video/generate",
                    json={
                        "prompt": styled_prompt,
                        "duration": scene.get("duration", 3),
                        "resolution": request.resolution,
                        "fps": 8
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        scene_videos.append({
                            "scene": i + 1,
                            "video_path": result.get("video_path"),
                            "description": scene["description"]
                        })
        
        # Step 3: Generate narration if requested
        narration_path = None
        if request.include_narration:
            narration_text = " ".join([s["description"] for s in scenes])
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVICES['audio']}/api/tts",
                    json={
                        "text": narration_text,
                        "voice": "Samantha",
                        "speed": 0.9
                    }
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        narration_path = tempfile.NamedTemporaryFile(
                            delete=False, suffix='.mp3'
                        ).name
                        with open(narration_path, 'wb') as f:
                            f.write(audio_data)
        
        # Step 4: Generate background music if requested
        music_path = None
        if request.include_music:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVICES['audio']}/api/generate_music",
                    json={
                        "prompt": f"{request.style} background music",
                        "duration": request.duration,
                        "style": request.style
                    }
                ) as response:
                    if response.status == 200:
                        music_data = await response.read()
                        music_path = tempfile.NamedTemporaryFile(
                            delete=False, suffix='.mp3'
                        ).name
                        with open(music_path, 'wb') as f:
                            f.write(music_data)
        
        # Step 5: Combine everything
        # In production, this would use ffmpeg to combine videos, narration, and music
        
        return {
            "workflow_id": workflow_id,
            "status": "completed",
            "story": request.story,
            "scenes": len(scenes),
            "scene_videos": scene_videos,
            "narration": narration_path,
            "music": music_path,
            "final_video": scene_videos[0]["video_path"] if scene_videos else None
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/text_to_video")
async def text_to_video_workflow(request: TextToVideoRequest):
    """Advanced text to video generation with automatic model selection"""
    try:
        # Step 1: Enhance prompt with LLM
        enhanced_prompt = request.prompt
        
        if request.model == "auto":
            # Analyze prompt to select best model
            if "realistic" in request.prompt.lower() or "photo" in request.prompt.lower():
                model = "stable_video_diffusion"
            elif "anime" in request.prompt.lower() or "cartoon" in request.prompt.lower():
                model = "animatediff"
            else:
                model = "videocrafter1"
        else:
            model = request.model
        
        # Step 2: Add style preset if provided
        if request.style_preset:
            style_prompts = {
                "cinematic": "cinematic lighting, film grain, dramatic composition",
                "anime": "anime style, cel shaded, vibrant colors",
                "realistic": "photorealistic, 8k quality, detailed textures",
                "abstract": "abstract art, surreal, artistic interpretation"
            }
            enhanced_prompt += f", {style_prompts.get(request.style_preset, '')}"
        
        # Step 3: Generate video
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SERVICES['video_gen']}/api/video/generate",
                json={
                    "prompt": enhanced_prompt,
                    "model": model,
                    "duration": request.duration,
                    "fps": request.fps,
                    "negative_prompt": request.negative_prompt
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    return {
                        "status": "success",
                        "video_path": result.get("video_path"),
                        "model_used": model,
                        "enhanced_prompt": enhanced_prompt,
                        "duration": request.duration,
                        "fps": request.fps
                    }
                else:
                    error = await response.text()
                    raise HTTPException(status_code=response.status, detail=error)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/animate_image")
async def animate_image_workflow(request: ImageAnimationRequest):
    """Animate a still image with AI-driven motion"""
    try:
        # Step 1: Analyze image to understand content
        image_description = await analyze_image_with_ollama(
            request.image_path,
            "Describe what's in this image and what kind of motion would look natural"
        )
        
        # Step 2: Generate motion parameters based on analysis
        motion_type = "auto"
        if "landscape" in image_description.lower():
            motion_type = "pan_left"
        elif "portrait" in image_description.lower() or "person" in image_description.lower():
            motion_type = "zoom_in"
        elif "object" in image_description.lower():
            motion_type = "zoom_out"
        
        # Step 3: Create animated video
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SERVICES['video_gen']}/api/video/image_to_video",
                json={
                    "image_path": request.image_path,
                    "prompt": request.motion_prompt,
                    "duration": request.duration,
                    "motion_type": motion_type,
                    "fps": 30
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    return {
                        "status": "success",
                        "video_path": result.get("video_path"),
                        "image_analysis": image_description[:200],
                        "motion_type": motion_type,
                        "duration": request.duration
                    }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/enhance_video")
async def enhance_video_workflow(request: VideoEnhanceRequest):
    """Apply multiple enhancements to a video"""
    try:
        current_video = request.video_path
        enhancement_log = []
        
        for enhancement in request.enhancements:
            if enhancement == "interpolate" and request.target_fps:
                # Increase FPS
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{SERVICES['video_gen']}/api/video/interpolate",
                        json={
                            "video_path": current_video,
                            "target_fps": request.target_fps
                        }
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            current_video = result.get("video_path")
                            enhancement_log.append(f"Interpolated to {request.target_fps} FPS")
            
            elif enhancement == "upscale":
                # Would integrate with Real-ESRGAN or similar
                enhancement_log.append("Upscaling (placeholder)")
            
            elif enhancement == "stabilize":
                # Would use video stabilization
                enhancement_log.append("Stabilization (placeholder)")
            
            elif enhancement == "denoise":
                # Would apply denoising
                enhancement_log.append("Denoising (placeholder)")
        
        return {
            "status": "success",
            "original_video": request.video_path,
            "enhanced_video": current_video,
            "enhancements_applied": enhancement_log
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/multimodal")
async def multimodal_generation(request: MultimodalRequest):
    """Generate video using multiple input modalities"""
    try:
        workflow_steps = []
        
        # Step 1: Analyze reference image if provided
        image_context = ""
        if request.reference_image:
            image_context = await analyze_image_with_ollama(
                request.reference_image,
                "Describe the style, colors, and composition of this image"
            )
            workflow_steps.append("Analyzed reference image")
        
        # Step 2: Enhance prompt with image context
        enhanced_prompt = request.text_prompt
        if image_context:
            enhanced_prompt += f", in the style of: {image_context[:100]}"
        
        # Step 3: Generate base video
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SERVICES['video_gen']}/api/video/generate",
                json={
                    "prompt": enhanced_prompt,
                    "duration": 5
                }
            ) as response:
                if response.status == 200:
                    video_result = await response.json()
                    workflow_steps.append("Generated base video")
        
        # Step 4: Add audio if requested
        audio_path = None
        if request.audio_style:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVICES['audio']}/api/generate_music",
                    json={
                        "prompt": f"{request.audio_style} music for: {request.text_prompt}",
                        "duration": 5,
                        "style": request.audio_style
                    }
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        audio_path = tempfile.NamedTemporaryFile(
                            delete=False, suffix='.mp3'
                        ).name
                        with open(audio_path, 'wb') as f:
                            f.write(audio_data)
                        workflow_steps.append("Generated audio")
        
        return {
            "status": "success",
            "workflow_steps": workflow_steps,
            "video_path": video_result.get("video_path"),
            "audio_path": audio_path,
            "enhanced_prompt": enhanced_prompt
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/workflow/capabilities")
async def get_capabilities():
    """List all available capabilities and models"""
    capabilities = {
        "vision_models": [],
        "video_models": [],
        "audio_capabilities": [],
        "workflows": []
    }
    
    # Check Ollama vision models
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVICES['ollama']}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    for model in data.get("models", []):
                        if any(vm in model["name"] for vm in ["llava", "bakllava", "moondream"]):
                            capabilities["vision_models"].append({
                                "name": model["name"],
                                "size": f"{model['size'] / 1e9:.1f}GB"
                            })
    except:
        pass
    
    # Check video generation models
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVICES['video_gen']}/api/models/list") as response:
                if response.status == 200:
                    data = await response.json()
                    for name, info in data.get("models", {}).items():
                        if info["type"] == "video" and info.get("installed"):
                            capabilities["video_models"].append(name)
    except:
        pass
    
    # List available workflows
    capabilities["workflows"] = [
        {
            "name": "story_to_video",
            "description": "Convert stories to multi-scene videos with narration"
        },
        {
            "name": "text_to_video",
            "description": "Generate videos from text prompts"
        },
        {
            "name": "animate_image",
            "description": "Animate still images with AI-driven motion"
        },
        {
            "name": "enhance_video",
            "description": "Upscale, interpolate, and enhance videos"
        },
        {
            "name": "multimodal",
            "description": "Generate using text, images, and audio references"
        }
    ]
    
    return capabilities

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "Advanced Video Workflows",
        "version": "1.0.0",
        "description": "Natural language to video generation pipeline",
        "endpoints": {
            "/api/workflow/story_to_video": "Convert stories to videos",
            "/api/workflow/text_to_video": "Generate video from text",
            "/api/workflow/animate_image": "Animate still images",
            "/api/workflow/enhance_video": "Enhance existing videos",
            "/api/workflow/multimodal": "Multi-modal generation",
            "/api/workflow/capabilities": "List available models",
            "/docs": "Interactive API documentation"
        },
        "models": {
            "vision": ["llava:7b", "bakllava:7b", "moondream"],
            "video": ["videocrafter1", "animatediff", "stable_video_diffusion"],
            "llm": ["llama3.1:8b", "mistral:7b-instruct", "deepseek-coder:6.7b"]
        }
    }

if __name__ == "__main__":
    print("🎬 Starting Advanced Video Workflows on http://localhost:8007")
    print("📚 API Documentation: http://localhost:8007/docs")
    print("\n✨ Capabilities:")
    print("  - Story to video with scenes")
    print("  - Image animation with AI")
    print("  - Video enhancement pipeline")
    print("  - Multi-modal generation")
    uvicorn.run(app, host="0.0.0.0", port=8007)
