#!/usr/bin/env python3
"""
Test script to verify LLM integration with your local Ollama installation
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Your available models
AVAILABLE_MODELS = [
    "mistral:7b-instruct",
    "llama3.1:8b",
    "qwen2:7b-instruct",
    "deepseek-coder:6.7b-instruct",
    "llama3.2:3b",
    "phi3:mini",
    "gpt-oss:20b"
]

async def test_ollama_direct():
    """Test direct Ollama API connection"""
    print("🔍 Testing Direct Ollama Connection...")
    
    async with aiohttp.ClientSession() as session:
        # Test if Ollama is running
        try:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Ollama is running!")
                    print(f"   Found {len(data.get('models', []))} models")
                    for model in data.get('models', [])[:5]:
                        print(f"   - {model['name']}: {model['size'] / 1e9:.1f}GB")
                else:
                    print("❌ Ollama API not responding")
                    return False
        except Exception as e:
            print(f"❌ Could not connect to Ollama: {e}")
            return False
    
    return True

async def test_model_generation(model: str = "llama3.2:3b"):
    """Test text generation with a specific model"""
    print(f"\n📝 Testing Text Generation with {model}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            prompt = "Write a haiku about artificial intelligence"
            
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 100
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Generation successful!")
                    print(f"\nPrompt: {prompt}")
                    print(f"Response: {data.get('response', 'No response')}")
                    return True
                else:
                    print(f"❌ Generation failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error during generation: {e}")
            return False

async def test_chat_completion(model: str = "mistral:7b-instruct"):
    """Test chat completion"""
    print(f"\n💬 Testing Chat with {model}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            messages = [
                {"role": "system", "content": "You are a helpful coding assistant."},
                {"role": "user", "content": "What's the best way to handle errors in Python?"}
            ]
            
            async with session.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Chat successful!")
                    print(f"Response: {data.get('message', {}).get('content', 'No response')[:200]}...")
                    return True
                else:
                    print(f"❌ Chat failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error during chat: {e}")
            return False

async def test_code_generation(model: str = "deepseek-coder:6.7b-instruct"):
    """Test code generation with DeepSeek Coder"""
    print(f"\n🖥️ Testing Code Generation with {model}...")
    
    async with aiohttp.ClientSession() as session:
        try:
            prompt = """Write a Python function that:
1. Takes a list of numbers
2. Returns the mean, median, and mode
3. Handles edge cases

Include docstring and type hints."""
            
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 500
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Code generation successful!")
                    print(f"\nGenerated code:\n{data.get('response', 'No response')[:500]}")
                    return True
                else:
                    print(f"❌ Code generation failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ Error during code generation: {e}")
            return False

async def test_local_llm_server():
    """Test the local LLM server we created"""
    print("\n🤖 Testing Local LLM Server Integration...")
    
    server_running = False
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:8005") as response:
                if response.status == 200:
                    server_running = True
                    print("✅ Local LLM Server is running!")
        except:
            print("⚠️  Local LLM Server not running (start with: python multimedia/local_llm_server.py)")
    
    if server_running:
        # Test chat endpoint
        try:
            async with session.post(
                "http://localhost:8005/api/chat",
                json={
                    "model": "llama3.1:8b",
                    "messages": [
                        {"role": "user", "content": "Hello, can you help me?"}
                    ]
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Server chat endpoint working!")
                    print(f"   Response: {data.get('response', '')[:100]}...")
        except Exception as e:
            print(f"❌ Server chat test failed: {e}")

async def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 OLLAMA INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Test Ollama connection
    ollama_ok = await test_ollama_direct()
    
    if ollama_ok:
        # Test different models for different tasks
        await test_model_generation("llama3.2:3b")  # Small, fast model
        await test_chat_completion("mistral:7b-instruct")  # Good for chat
        await test_code_generation("deepseek-coder:6.7b-instruct")  # Specialized for code
        
        # Test local server if running
        await test_local_llm_server()
    
    print("\n" + "=" * 60)
    print("✅ Testing complete!")
    print("\n📚 Your available models for different tasks:")
    print("  - General purpose: llama3.1:8b, mistral:7b-instruct")
    print("  - Code generation: deepseek-coder:6.7b-instruct")
    print("  - Fast responses: llama3.2:3b, phi3:mini")
    print("  - Advanced tasks: gpt-oss:20b")
    print("\n🚀 Start the LLM server with:")
    print("  cd multimedia && python local_llm_server.py")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
