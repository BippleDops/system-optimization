#!/usr/bin/env python3
"""
Test Video Generation Capabilities
Tests all video generation workflows with your installed models
"""

import asyncio
import aiohttp
import json
import os
from pathlib import Path

# Service endpoints
SERVICES = {
    "video_gen": "http://localhost:8006",
    "workflows": "http://localhost:8007",
    "ollama": "http://localhost:11434"
}

async def test_ollama_vision():
    """Test Ollama vision models"""
    print("\n🔍 Testing Ollama Vision Models...")
    
    models_to_test = ["llava:7b", "bakllava:7b", "moondream:latest"]
    
    for model in models_to_test:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVICES['ollama']}/api/generate",
                    json={
                        "model": model,
                        "prompt": "Describe a beautiful sunset over mountains",
                        "stream": False,
                        "options": {"num_predict": 50}
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ {model}: {result.get('response', '')[:100]}...")
                    else:
                        print(f"  ❌ {model}: Failed")
        except Exception as e:
            print(f"  ❌ {model}: {str(e)}")

async def test_text_to_video():
    """Test text to video generation"""
    print("\n🎬 Testing Text-to-Video Generation...")
    
    prompts = [
        {
            "prompt": "A serene lake with mountains reflected in the water, sunrise",
            "style": "cinematic"
        },
        {
            "prompt": "A robot dancing in a futuristic city",
            "style": "anime"
        },
        {
            "prompt": "Time-lapse of flowers blooming in a garden",
            "style": "realistic"
        }
    ]
    
    for test in prompts:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{SERVICES['workflows']}/api/workflow/text_to_video",
                    json={
                        "prompt": test["prompt"],
                        "style_preset": test["style"],
                        "duration": 4,
                        "fps": 8
                    }
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"  ✅ Generated: {test['prompt'][:50]}...")
                        print(f"     Model: {result.get('model_used')}")
                        print(f"     Path: {result.get('video_path')}")
                    else:
                        print(f"  ⚠️  Workflow server not running for: {test['prompt'][:50]}...")
        except:
            print(f"  ⚠️  Workflow server not available. Start with: python3 advanced_video_workflows.py")
            break

async def test_story_to_video():
    """Test story to video conversion"""
    print("\n📖 Testing Story-to-Video...")
    
    story = """
    Once upon a time, in a magical forest, a young deer discovered a glowing crystal.
    The crystal granted the deer the ability to fly. 
    Together, they soared above the clouds and saw the whole world.
    """
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{SERVICES['workflows']}/api/workflow/story_to_video",
                json={
                    "story": story,
                    "style": "fantasy",
                    "duration": 10,
                    "include_narration": True,
                    "include_music": True
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"  ✅ Story converted to video")
                    print(f"     Scenes: {result.get('scenes')}")
                    print(f"     Workflow ID: {result.get('workflow_id')}")
                else:
                    print("  ⚠️  Story workflow not available")
    except:
        print("  ⚠️  Workflow server not running")

async def test_model_availability():
    """Check which models are available"""
    print("\n📦 Checking Model Availability...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SERVICES['video_gen']}/api/models/list"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    models = data.get("models", {})
                    
                    print("\n  Video Models:")
                    for name, info in models.items():
                        if info["type"] == "video":
                            status = "✅" if info["installed"] else "❌"
                            print(f"    {status} {name}: {info['config']['description']}")
                    
                    print("\n  Image Models:")
                    for name, info in models.items():
                        if info["type"] == "image":
                            status = "✅" if info["installed"] else "❌"
                            print(f"    {status} {name}: {info['config']['description']}")
                    
                    print("\n  Recommendations:")
                    recs = data.get("recommendations", {})
                    for key, value in recs.items():
                        print(f"    {key}: {value}")
                else:
                    print("  ❌ Video generation server not running")
    except:
        print("  ❌ Video generation server not available")
        print("     Start with: python3 video_generation_server.py")

async def test_capabilities():
    """Test workflow capabilities"""
    print("\n🎯 Testing Workflow Capabilities...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{SERVICES['workflows']}/api/workflow/capabilities"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print("\n  Vision Models Available:")
                    for model in data.get("vision_models", []):
                        print(f"    ✅ {model['name']} ({model['size']})")
                    
                    print("\n  Video Models Ready:")
                    for model in data.get("video_models", []):
                        print(f"    ✅ {model}")
                    
                    print("\n  Workflows Available:")
                    for workflow in data.get("workflows", []):
                        print(f"    • {workflow['name']}: {workflow['description']}")
                else:
                    print("  ❌ Workflow server not responding")
    except:
        print("  ❌ Workflow server not available")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🎬 VIDEO GENERATION TEST SUITE")
    print("=" * 60)
    
    # Test Ollama vision models
    await test_ollama_vision()
    
    # Check model availability
    await test_model_availability()
    
    # Test workflows
    await test_capabilities()
    
    # Test video generation
    await test_text_to_video()
    
    # Test story conversion
    await test_story_to_video()
    
    print("\n" + "=" * 60)
    print("✅ Testing Complete!")
    print("\n📝 Quick Start Guide:")
    print("  1. Start video generation server:")
    print("     python3 video_generation_server.py")
    print("")
    print("  2. Start workflow server:")
    print("     python3 advanced_video_workflows.py")
    print("")
    print("  3. Generate a video:")
    print("     curl -X POST http://localhost:8007/api/workflow/text_to_video \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"prompt\": \"A beautiful sunset\", \"style_preset\": \"cinematic\"}'")
    print("")
    print("  4. Convert story to video:")
    print("     curl -X POST http://localhost:8007/api/workflow/story_to_video \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"story\": \"Your story here\", \"style\": \"fantasy\"}'")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
