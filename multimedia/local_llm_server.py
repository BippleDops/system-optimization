#!/usr/bin/env python3
"""
Local LLM Server - Integration with Ollama, LM Studio, and local language models
"""

import os
import json
import asyncio
import aiohttp
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Local LLM Server", version="1.0.0")

# LLM Service Endpoints
LLM_SERVICES = {
    "ollama": "http://localhost:11434",
    "lm_studio": "http://localhost:1234",
    "text_generation_webui": "http://localhost:5000",
    "llamacpp": "http://localhost:8080"
}

class ChatRequest(BaseModel):
    model: str = "llama3.1:8b"  # Updated to your actual model
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    system_prompt: Optional[str] = None

class CompletionRequest(BaseModel):
    model: str = "llama3.1:8b"  # Updated to your actual model
    prompt: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    stream: bool = False

class EmbeddingRequest(BaseModel):
    model: str = "llama3.1:8b"  # Updated to your actual model
    input: str

class ModelManagementRequest(BaseModel):
    action: str  # pull, delete, list
    model_name: Optional[str] = None

class RAGRequest(BaseModel):
    query: str
    context: List[str]
    model: str = "llama3.1:8b"  # Updated to your actual model
    max_tokens: int = 500

class FunctionCallRequest(BaseModel):
    model: str = "mistral:7b-instruct"  # Using Mistral for function calling
    prompt: str
    functions: List[Dict[str, Any]]
    temperature: float = 0.7

@app.post("/api/chat")
async def chat_completion(request: ChatRequest):
    """Chat with local LLM"""
    try:
        # Try Ollama first
        async with aiohttp.ClientSession() as session:
            ollama_request = {
                "model": request.model,
                "messages": request.messages,
                "stream": request.stream,
                "options": {
                    "temperature": request.temperature
                }
            }
            
            if request.max_tokens:
                ollama_request["options"]["num_predict"] = request.max_tokens
            
            if request.system_prompt:
                # Add system message at the beginning
                ollama_request["messages"].insert(0, {
                    "role": "system",
                    "content": request.system_prompt
                })
            
            async with session.post(
                f"{LLM_SERVICES['ollama']}/api/chat",
                json=ollama_request
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "model": request.model,
                        "response": result.get("message", {}).get("content", ""),
                        "usage": {
                            "prompt_tokens": result.get("prompt_eval_count", 0),
                            "completion_tokens": result.get("eval_count", 0),
                            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0)
                        }
                    }
                else:
                    # Fallback to LM Studio
                    async with session.post(
                        f"{LLM_SERVICES['lm_studio']}/v1/chat/completions",
                        json={
                            "model": request.model,
                            "messages": request.messages,
                            "temperature": request.temperature,
                            "max_tokens": request.max_tokens
                        }
                    ) as lm_response:
                        if lm_response.status == 200:
                            result = await lm_response.json()
                            return result
    
    except Exception as e:
        # If no LLM service is available, return a helpful message
        return {
            "model": request.model,
            "response": f"No local LLM service available. Please start Ollama (ollama serve) or LM Studio.",
            "error": str(e)
        }

@app.post("/api/completion")
async def text_completion(request: CompletionRequest):
    """Generate text completion"""
    try:
        async with aiohttp.ClientSession() as session:
            # Try Ollama generate endpoint
            async with session.post(
                f"{LLM_SERVICES['ollama']}/api/generate",
                json={
                    "model": request.model,
                    "prompt": request.prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "top_p": request.top_p,
                        "num_predict": request.max_tokens
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "model": request.model,
                        "text": result.get("response", ""),
                        "done": result.get("done", True),
                        "context": result.get("context", [])
                    }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/embeddings")
async def generate_embeddings(request: EmbeddingRequest):
    """Generate embeddings for text"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LLM_SERVICES['ollama']}/api/embeddings",
                json={
                    "model": request.model,
                    "prompt": request.input
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "model": request.model,
                        "embedding": result.get("embedding", []),
                        "dimensions": len(result.get("embedding", []))
                    }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/models/manage")
async def manage_models(request: ModelManagementRequest):
    """Manage local LLM models"""
    try:
        if request.action == "list":
            # List available models
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{LLM_SERVICES['ollama']}/api/tags") as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "models": result.get("models", []),
                            "count": len(result.get("models", []))
                        }
        
        elif request.action == "pull":
            # Pull a new model
            if not request.model_name:
                raise HTTPException(status_code=400, detail="Model name required")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{LLM_SERVICES['ollama']}/api/pull",
                    json={"name": request.model_name}
                ) as response:
                    if response.status == 200:
                        return {"message": f"Pulling model {request.model_name}"}
        
        elif request.action == "delete":
            # Delete a model
            if not request.model_name:
                raise HTTPException(status_code=400, detail="Model name required")
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{LLM_SERVICES['ollama']}/api/delete",
                    json={"name": request.model_name}
                ) as response:
                    if response.status == 200:
                        return {"message": f"Deleted model {request.model_name}"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag")
async def rag_query(request: RAGRequest):
    """Retrieval-Augmented Generation query"""
    try:
        # Combine context into prompt
        context_text = "\n\n".join(request.context)
        
        augmented_prompt = f"""Based on the following context, please answer the question.

Context:
{context_text}

Question: {request.query}

Answer:"""
        
        # Use chat completion with context
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LLM_SERVICES['ollama']}/api/generate",
                json={
                    "model": request.model,
                    "prompt": augmented_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for factual responses
                        "num_predict": request.max_tokens
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "query": request.query,
                        "answer": result.get("response", ""),
                        "context_used": len(request.context),
                        "model": request.model
                    }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/function_call")
async def function_calling(request: FunctionCallRequest):
    """Simulate function calling with local LLM"""
    try:
        # Create a prompt that instructs the model to use functions
        functions_desc = json.dumps(request.functions, indent=2)
        
        function_prompt = f"""You are a helpful assistant with access to the following functions:

{functions_desc}

To use a function, respond with:
FUNCTION_CALL: function_name
PARAMETERS: {{
  "param1": "value1",
  "param2": "value2"
}}

User request: {request.prompt}

Response:"""
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{LLM_SERVICES['ollama']}/api/generate",
                json={
                    "model": request.model,
                    "prompt": function_prompt,
                    "stream": False,
                    "options": {
                        "temperature": request.temperature,
                        "num_predict": 500
                    }
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_text = result.get("response", "")
                    
                    # Parse function call from response
                    if "FUNCTION_CALL:" in response_text:
                        lines = response_text.split('\n')
                        function_name = None
                        parameters = {}
                        
                        for i, line in enumerate(lines):
                            if "FUNCTION_CALL:" in line:
                                function_name = line.split("FUNCTION_CALL:")[1].strip()
                            elif "PARAMETERS:" in line:
                                # Extract JSON parameters
                                param_start = i + 1
                                param_lines = []
                                for j in range(param_start, len(lines)):
                                    param_lines.append(lines[j])
                                    if lines[j].strip() == "}":
                                        break
                                
                                try:
                                    parameters = json.loads('\n'.join(param_lines))
                                except:
                                    parameters = {}
                        
                        return {
                            "function_call": {
                                "name": function_name,
                                "parameters": parameters
                            },
                            "raw_response": response_text
                        }
                    
                    else:
                        return {
                            "response": response_text,
                            "function_call": None
                        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for streaming chat"""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            model = data.get("model", "llama2")
            message = data.get("message", "")
            
            # Stream response from LLM
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{LLM_SERVICES['ollama']}/api/generate",
                    json={
                        "model": model,
                        "prompt": message,
                        "stream": True
                    }
                ) as response:
                    async for line in response.content:
                        if line:
                            try:
                                chunk = json.loads(line)
                                if not chunk.get("done", False):
                                    await websocket.send_json({
                                        "type": "token",
                                        "content": chunk.get("response", "")
                                    })
                                else:
                                    await websocket.send_json({
                                        "type": "done",
                                        "stats": {
                                            "total_duration": chunk.get("total_duration"),
                                            "eval_count": chunk.get("eval_count")
                                        }
                                    })
                            except:
                                continue
    
    except Exception as e:
        await websocket.close()

@app.get("/api/services/status")
async def check_llm_services():
    """Check status of all LLM services"""
    status = {}
    
    for service_name, url in LLM_SERVICES.items():
        try:
            async with aiohttp.ClientSession() as session:
                # Different endpoints for different services
                check_url = url
                if service_name == "ollama":
                    check_url = f"{url}/api/tags"
                elif service_name == "lm_studio":
                    check_url = f"{url}/v1/models"
                
                async with session.get(check_url, timeout=2) as response:
                    status[service_name] = {
                        "url": url,
                        "status": "online" if response.status in [200, 404] else "error",
                        "code": response.status
                    }
        except:
            status[service_name] = {
                "url": url,
                "status": "offline",
                "code": None
            }
    
    return status

@app.get("/api/prompts/templates")
async def get_prompt_templates():
    """Get useful prompt templates"""
    return {
        "templates": {
            "code_review": """Review the following code and provide feedback on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance improvements
4. Security concerns

Code:
{code}""",
            
            "explain_concept": """Explain {concept} in simple terms. Include:
1. A basic definition
2. Why it's important
3. A real-world example
4. Common misconceptions""",
            
            "creative_writing": """Write a {genre} story about {topic}. 
Requirements:
- Length: {word_count} words
- Tone: {tone}
- Include: {elements}""",
            
            "data_analysis": """Analyze the following data and provide:
1. Key insights
2. Patterns or trends
3. Anomalies
4. Recommendations

Data:
{data}""",
            
            "task_breakdown": """Break down the following task into actionable steps:
Task: {task}

Provide:
1. Step-by-step instructions
2. Time estimates
3. Required resources
4. Potential challenges"""
        }
    }

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "Local LLM Server",
        "version": "1.0.0",
        "endpoints": {
            "/api/chat": "Chat with local LLM",
            "/api/completion": "Text completion",
            "/api/embeddings": "Generate embeddings",
            "/api/models/manage": "Manage models (list, pull, delete)",
            "/api/rag": "RAG queries with context",
            "/api/function_call": "Function calling simulation",
            "/ws/chat": "WebSocket streaming chat",
            "/api/services/status": "Check LLM service status",
            "/api/prompts/templates": "Get prompt templates",
            "/docs": "Interactive API documentation"
        },
        "supported_services": list(LLM_SERVICES.keys()),
        "setup_instructions": {
            "ollama": "brew install ollama && ollama serve",
            "lm_studio": "Download from lmstudio.ai",
            "text_generation_webui": "github.com/oobabooga/text-generation-webui",
            "llamacpp": "github.com/ggerganov/llama.cpp"
        },
        "note": "At least one LLM service must be running"
    }

if __name__ == "__main__":
    print("🤖 Starting Local LLM Server on http://localhost:8005")
    print("📚 API Documentation: http://localhost:8005/docs")
    print("\n⚠️  Make sure at least one LLM service is running:")
    print("  - Ollama: ollama serve")
    print("  - LM Studio: Launch the application")
    print("  - Text Generation WebUI: python server.py")
    uvicorn.run(app, host="0.0.0.0", port=8005)
