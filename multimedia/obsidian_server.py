#!/usr/bin/env python3
"""
Obsidian Management Server - Advanced vault management, AI-powered note generation, and workflow automation
"""

import os
import json
import re
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import frontmatter
import yaml
from collections import defaultdict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Obsidian Management Server", version="2.0.0")

# Configuration
OBSIDIAN_VAULT_PATH = os.path.expanduser("~/Documents/ObsidianVault")
EXCLUDED_VAULT = "/Users/jongosussmango/Library/Mobile Documents/iCloud~md~obsidian/Documents/ObsidianTTRPGVault Experimental"

class NoteRequest(BaseModel):
    title: str
    content: str
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    template: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    query: str
    folder: Optional[str] = None
    tags: Optional[List[str]] = None
    limit: int = 50
    search_type: str = "content"  # content, title, tags, backlinks

class GraphRequest(BaseModel):
    depth: int = 2
    node: Optional[str] = None
    include_tags: bool = True
    include_attachments: bool = False

class TemplateRequest(BaseModel):
    name: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class WorkflowRequest(BaseModel):
    workflow_type: str  # daily_note, weekly_review, project_setup, research_compilation
    parameters: Dict[str, Any]

class AIAssistRequest(BaseModel):
    action: str  # summarize, expand, connect, generate_questions, create_outline
    note_path: Optional[str] = None
    content: Optional[str] = None
    context: Optional[List[str]] = None

def ensure_vault_exists():
    """Ensure the Obsidian vault directory exists"""
    if not os.path.exists(OBSIDIAN_VAULT_PATH):
        os.makedirs(OBSIDIAN_VAULT_PATH)
        os.makedirs(f"{OBSIDIAN_VAULT_PATH}/Templates")
        os.makedirs(f"{OBSIDIAN_VAULT_PATH}/Daily Notes")
        os.makedirs(f"{OBSIDIAN_VAULT_PATH}/Projects")
        os.makedirs(f"{OBSIDIAN_VAULT_PATH}/Archive")

def is_excluded_path(path: str) -> bool:
    """Check if path is in excluded vault"""
    return EXCLUDED_VAULT in str(path)

@app.post("/api/notes/create")
async def create_note(request: NoteRequest):
    """Create a new note in the vault"""
    try:
        ensure_vault_exists()
        
        # Determine folder path
        if request.folder:
            folder_path = Path(OBSIDIAN_VAULT_PATH) / request.folder
        else:
            folder_path = Path(OBSIDIAN_VAULT_PATH)
        
        if is_excluded_path(str(folder_path)):
            raise HTTPException(status_code=403, detail="Cannot modify excluded vault")
        
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # Create note with frontmatter
        note_data = {
            'title': request.title,
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat(),
            'tags': request.tags or [],
        }
        
        if request.metadata:
            note_data.update(request.metadata)
        
        # Apply template if specified
        content = request.content
        if request.template:
            template_path = Path(OBSIDIAN_VAULT_PATH) / "Templates" / f"{request.template}.md"
            if template_path.exists():
                with open(template_path, 'r') as f:
                    template_content = f.read()
                content = template_content.replace('{{content}}', content)
                content = content.replace('{{date}}', datetime.now().strftime('%Y-%m-%d'))
                content = content.replace('{{time}}', datetime.now().strftime('%H:%M'))
        
        # Create the note file
        note_path = folder_path / f"{request.title}.md"
        post = frontmatter.Post(content, **note_data)
        
        with open(note_path, 'w') as f:
            f.write(frontmatter.dumps(post))
        
        return {
            "success": True,
            "path": str(note_path),
            "message": f"Note created: {request.title}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/notes/search")
async def search_notes(request: SearchRequest):
    """Search notes in the vault"""
    try:
        ensure_vault_exists()
        results = []
        
        for root, dirs, files in os.walk(OBSIDIAN_VAULT_PATH):
            if is_excluded_path(root):
                continue
                
            # Filter by folder if specified
            if request.folder and request.folder not in root:
                continue
            
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        post = frontmatter.loads(content)
                        
                        # Search based on type
                        match = False
                        
                        if request.search_type == "content":
                            if request.query.lower() in content.lower():
                                match = True
                        
                        elif request.search_type == "title":
                            if request.query.lower() in file.lower():
                                match = True
                        
                        elif request.search_type == "tags":
                            note_tags = post.metadata.get('tags', [])
                            if any(tag in note_tags for tag in request.tags or [request.query]):
                                match = True
                        
                        elif request.search_type == "backlinks":
                            # Search for notes that link to this one
                            link_pattern = rf'\[\[{request.query}.*?\]\]'
                            if re.search(link_pattern, content):
                                match = True
                        
                        if match:
                            results.append({
                                'path': str(file_path),
                                'title': file_path.stem,
                                'preview': content[:200] + '...' if len(content) > 200 else content,
                                'tags': post.metadata.get('tags', []),
                                'modified': post.metadata.get('modified', ''),
                                'matches': len(re.findall(request.query, content, re.IGNORECASE))
                            })
                    
                    except Exception as e:
                        continue
        
        # Sort by relevance (number of matches)
        results.sort(key=lambda x: x['matches'], reverse=True)
        
        return {
            "query": request.query,
            "count": len(results),
            "results": results[:request.limit]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/graph/generate")
async def generate_graph(request: GraphRequest):
    """Generate a knowledge graph of notes and connections"""
    try:
        ensure_vault_exists()
        
        nodes = {}
        edges = []
        
        # Build the graph
        for root, dirs, files in os.walk(OBSIDIAN_VAULT_PATH):
            if is_excluded_path(root):
                continue
                
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    note_name = file_path.stem
                    
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        post = frontmatter.loads(content)
                        
                        # Add node
                        nodes[note_name] = {
                            'id': note_name,
                            'label': note_name,
                            'path': str(file_path),
                            'tags': post.metadata.get('tags', []),
                            'size': len(content),
                            'type': 'note'
                        }
                        
                        # Find links
                        link_pattern = r'\[\[(.*?)\]\]'
                        links = re.findall(link_pattern, content)
                        
                        for link in links:
                            # Clean link (remove aliases)
                            clean_link = link.split('|')[0].strip()
                            edges.append({
                                'source': note_name,
                                'target': clean_link,
                                'type': 'link'
                            })
                        
                        # Add tag nodes if requested
                        if request.include_tags:
                            for tag in post.metadata.get('tags', []):
                                if tag not in nodes:
                                    nodes[tag] = {
                                        'id': tag,
                                        'label': f"#{tag}",
                                        'type': 'tag',
                                        'size': 1
                                    }
                                edges.append({
                                    'source': note_name,
                                    'target': tag,
                                    'type': 'tag'
                                })
                    
                    except Exception as e:
                        continue
        
        # Filter by depth if a specific node is requested
        if request.node and request.node in nodes:
            filtered_nodes = {}
            filtered_edges = []
            
            def traverse(node, depth):
                if depth <= 0 or node not in nodes:
                    return
                
                filtered_nodes[node] = nodes[node]
                
                for edge in edges:
                    if edge['source'] == node and edge['target'] not in filtered_nodes:
                        filtered_edges.append(edge)
                        traverse(edge['target'], depth - 1)
                    elif edge['target'] == node and edge['source'] not in filtered_nodes:
                        filtered_edges.append(edge)
                        traverse(edge['source'], depth - 1)
            
            traverse(request.node, request.depth)
            nodes = filtered_nodes
            edges = filtered_edges
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "stats": {
                "total_notes": sum(1 for n in nodes.values() if n['type'] == 'note'),
                "total_tags": sum(1 for n in nodes.values() if n['type'] == 'tag'),
                "total_links": len(edges)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workflow/execute")
async def execute_workflow(request: WorkflowRequest):
    """Execute predefined workflows"""
    try:
        ensure_vault_exists()
        
        if request.workflow_type == "daily_note":
            # Create daily note
            date = datetime.now().strftime('%Y-%m-%d')
            
            content = f"""# Daily Note - {date}

## 📅 Schedule
- [ ] Morning routine
- [ ] Check emails
- [ ] Review tasks

## 🎯 Top 3 Priorities
1. 
2. 
3. 

## 📝 Notes


## 💭 Reflections


## 🔗 Related Notes
- [[{(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}|Yesterday]]
- [[Weekly Review]]
"""
            
            note_request = NoteRequest(
                title=date,
                content=content,
                folder="Daily Notes",
                tags=["daily", "journal"],
                metadata={"type": "daily_note"}
            )
            
            result = await create_note(note_request)
            return {"success": True, "message": f"Daily note created for {date}", "path": result['path']}
        
        elif request.workflow_type == "weekly_review":
            # Create weekly review
            week_num = datetime.now().isocalendar()[1]
            year = datetime.now().year
            
            content = f"""# Weekly Review - Week {week_num}, {year}

## 📊 Week Overview
### Accomplishments
- 

### Challenges
- 

### Learnings
- 

## 📈 Progress on Goals
### Personal
- 

### Professional
- 

## 🎯 Next Week's Focus
1. 
2. 
3. 

## 📝 Notes to Self


## 🔗 Daily Notes This Week
"""
            # Add links to daily notes
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                content += f"- [[{date}]]\n"
            
            note_request = NoteRequest(
                title=f"Week {week_num} - {year}",
                content=content,
                folder="Weekly Reviews",
                tags=["weekly", "review"],
                metadata={"type": "weekly_review", "week": week_num, "year": year}
            )
            
            result = await create_note(note_request)
            return {"success": True, "message": f"Weekly review created", "path": result['path']}
        
        elif request.workflow_type == "project_setup":
            # Create project structure
            project_name = request.parameters.get('name', 'New Project')
            
            # Create project folder
            project_folder = Path(OBSIDIAN_VAULT_PATH) / "Projects" / project_name
            project_folder.mkdir(parents=True, exist_ok=True)
            
            # Create project overview
            overview_content = f"""# {project_name}

## 📋 Project Overview
**Start Date:** {datetime.now().strftime('%Y-%m-%d')}
**Status:** 🟡 In Progress
**Priority:** High

## 🎯 Objectives
- 

## 🗓️ Timeline
- **Phase 1:** 
- **Phase 2:** 
- **Phase 3:** 

## 👥 Stakeholders
- 

## 📝 Notes
- [[{project_name} - Research]]
- [[{project_name} - Tasks]]
- [[{project_name} - Meetings]]

## 📊 Progress Log
"""
            
            # Create main project note
            with open(project_folder / f"{project_name}.md", 'w') as f:
                f.write(overview_content)
            
            # Create supporting notes
            for suffix in ["Research", "Tasks", "Meetings"]:
                with open(project_folder / f"{project_name} - {suffix}.md", 'w') as f:
                    f.write(f"# {project_name} - {suffix}\n\n")
            
            return {
                "success": True,
                "message": f"Project '{project_name}' created",
                "path": str(project_folder)
            }
        
        elif request.workflow_type == "research_compilation":
            # Compile research from multiple notes
            topic = request.parameters.get('topic', 'Research')
            sources = request.parameters.get('sources', [])
            
            compiled_content = f"""# {topic} - Research Compilation
**Compiled:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📚 Sources
"""
            
            for source in sources:
                compiled_content += f"- [[{source}]]\n"
            
            compiled_content += "\n## 📝 Compiled Notes\n\n"
            
            # Read and compile content from sources
            for source in sources:
                source_path = Path(OBSIDIAN_VAULT_PATH) / f"{source}.md"
                if source_path.exists():
                    with open(source_path, 'r') as f:
                        content = f.read()
                    
                    # Extract main content (skip frontmatter)
                    post = frontmatter.loads(content)
                    compiled_content += f"### From: {source}\n{post.content}\n\n---\n\n"
            
            compiled_content += "## 🎯 Key Takeaways\n- \n\n## 🔮 Next Steps\n- "
            
            note_request = NoteRequest(
                title=f"{topic} - Compilation",
                content=compiled_content,
                folder="Research",
                tags=["research", "compilation"],
                metadata={"type": "research_compilation", "sources": sources}
            )
            
            result = await create_note(note_request)
            return {"success": True, "message": f"Research compilation created", "path": result['path']}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown workflow: {request.workflow_type}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/assist")
async def ai_assist(request: AIAssistRequest):
    """AI-powered note assistance"""
    try:
        # This would integrate with your AI models
        # For now, providing template responses
        
        if request.action == "summarize":
            # Would use AI to summarize
            return {
                "action": "summarize",
                "result": "This feature would use AI to create a concise summary of the content."
            }
        
        elif request.action == "expand":
            # Would use AI to expand on ideas
            return {
                "action": "expand",
                "result": "This feature would use AI to elaborate on the key points and add relevant details."
            }
        
        elif request.action == "connect":
            # Find related notes
            return {
                "action": "connect",
                "result": "This feature would analyze content and suggest related notes to link."
            }
        
        elif request.action == "generate_questions":
            # Generate questions for deeper thinking
            return {
                "action": "generate_questions",
                "questions": [
                    "What are the key assumptions here?",
                    "How does this relate to existing knowledge?",
                    "What are the potential implications?",
                    "What evidence supports this?",
                    "What alternative perspectives exist?"
                ]
            }
        
        elif request.action == "create_outline":
            # Create structured outline
            return {
                "action": "create_outline",
                "outline": """## Main Topic
### Key Point 1
- Supporting detail
- Evidence

### Key Point 2
- Supporting detail
- Evidence

### Conclusion
- Summary
- Next steps"""
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_vault_stats():
    """Get statistics about the vault"""
    try:
        ensure_vault_exists()
        
        stats = {
            "total_notes": 0,
            "total_words": 0,
            "total_links": 0,
            "total_tags": set(),
            "folders": defaultdict(int),
            "recent_notes": [],
            "orphan_notes": []
        }
        
        all_notes = set()
        linked_notes = set()
        
        for root, dirs, files in os.walk(OBSIDIAN_VAULT_PATH):
            if is_excluded_path(root):
                continue
                
            folder_name = Path(root).relative_to(OBSIDIAN_VAULT_PATH).as_posix()
            
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    all_notes.add(file_path.stem)
                    
                    stats['total_notes'] += 1
                    stats['folders'][folder_name] += 1
                    
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Count words
                        stats['total_words'] += len(content.split())
                        
                        # Count links
                        links = re.findall(r'\[\[(.*?)\]\]', content)
                        stats['total_links'] += len(links)
                        for link in links:
                            linked_notes.add(link.split('|')[0].strip())
                        
                        # Extract tags
                        post = frontmatter.loads(content)
                        for tag in post.metadata.get('tags', []):
                            stats['total_tags'].add(tag)
                        
                        # Track recent notes
                        mtime = os.path.getmtime(file_path)
                        stats['recent_notes'].append({
                            'title': file_path.stem,
                            'path': str(file_path),
                            'modified': datetime.fromtimestamp(mtime).isoformat()
                        })
                    
                    except Exception as e:
                        continue
        
        # Find orphan notes (no incoming or outgoing links)
        stats['orphan_notes'] = list(all_notes - linked_notes)
        
        # Sort recent notes
        stats['recent_notes'].sort(key=lambda x: x['modified'], reverse=True)
        stats['recent_notes'] = stats['recent_notes'][:10]
        
        # Convert set to list for JSON
        stats['total_tags'] = list(stats['total_tags'])
        stats['folders'] = dict(stats['folders'])
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "Obsidian Management Server",
        "version": "2.0.0",
        "vault_path": OBSIDIAN_VAULT_PATH,
        "endpoints": {
            "/api/notes/create": "Create new notes with templates",
            "/api/notes/search": "Search notes by content, title, tags, or backlinks",
            "/api/graph/generate": "Generate knowledge graph",
            "/api/workflow/execute": "Execute predefined workflows",
            "/api/ai/assist": "AI-powered note assistance",
            "/api/stats": "Get vault statistics",
            "/docs": "Interactive API documentation"
        },
        "workflows": [
            "daily_note", "weekly_review", "project_setup", "research_compilation"
        ],
        "ai_actions": [
            "summarize", "expand", "connect", "generate_questions", "create_outline"
        ],
        "note": f"Excluding vault: {EXCLUDED_VAULT}"
    }

if __name__ == "__main__":
    print("📝 Starting Obsidian Management Server on http://localhost:8002")
    print(f"📁 Managing vault at: {OBSIDIAN_VAULT_PATH}")
    print(f"🚫 Excluding: {EXCLUDED_VAULT}")
    print("📚 API Documentation: http://localhost:8002/docs")
    uvicorn.run(app, host="0.0.0.0", port=8002)
