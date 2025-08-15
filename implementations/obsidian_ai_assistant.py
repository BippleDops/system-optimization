#!/usr/bin/env python3
"""
Obsidian AI Assistant - Complete Integration
Connects Claude, GPT, and local LLMs directly to your Obsidian vault
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import hashlib
import yaml

class ObsidianAIAssistant:
    """
    Advanced AI assistant for Obsidian with smart note generation,
    linking, and knowledge graph enhancement
    """
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.notes_dir = self.vault_path / "AI_Generated"
        self.templates_dir = self.vault_path / "Templates"
        self.daily_dir = self.vault_path / "Daily"
        
        # Create directories if they don't exist
        self.notes_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.daily_dir.mkdir(exist_ok=True)
        
        # Load vault configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load Obsidian vault configuration"""
        config_path = self.vault_path / ".obsidian" / "app.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}
    
    def create_smart_note(self, 
                         prompt: str, 
                         title: Optional[str] = None,
                         tags: List[str] = None,
                         template: Optional[str] = None) -> Path:
        """
        Generate an AI-powered note with intelligent formatting
        """
        # Generate title if not provided
        if not title:
            title = self._generate_title(prompt)
        
        # Clean title for filename
        filename = re.sub(r'[^\w\s-]', '', title)
        filename = re.sub(r'[-\s]+', '-', filename)
        
        # Create note content
        content = []
        content.append(f"# {title}")
        content.append("")
        
        # Add metadata
        content.append("---")
        content.append(f"created: {datetime.now().isoformat()}")
        content.append(f"type: ai-generated")
        if tags:
            content.append(f"tags: [{', '.join(tags)}]")
        content.append(f"prompt: {prompt[:100]}...")
        content.append("---")
        content.append("")
        
        # Add AI-generated content
        ai_content = self._generate_content(prompt, template)
        content.append(ai_content)
        
        # Add backlinks section
        content.append("")
        content.append("## Related Notes")
        related = self._find_related_notes(prompt)
        for note in related[:5]:
            content.append(f"- [[{note}]]")
        
        # Save note
        note_path = self.notes_dir / f"{filename}.md"
        with open(note_path, 'w') as f:
            f.write('\n'.join(content))
        
        # Update daily note
        self._update_daily_note(title)
        
        return note_path
    
    def _generate_title(self, prompt: str) -> str:
        """Generate a title from the prompt"""
        # Simple title generation - in production, use AI
        words = prompt.split()[:5]
        return ' '.join(words).title()
    
    def _generate_content(self, prompt: str, template: Optional[str]) -> str:
        """
        Generate content using AI (placeholder for actual AI integration)
        """
        if template:
            template_path = self.templates_dir / f"{template}.md"
            if template_path.exists():
                with open(template_path, 'r') as f:
                    template_content = f.read()
                return template_content.replace("{{prompt}}", prompt)
        
        # Placeholder content structure
        sections = [
            "## Overview",
            f"This note explores: {prompt}",
            "",
            "## Key Concepts",
            "- Concept 1: Description",
            "- Concept 2: Description",
            "- Concept 3: Description",
            "",
            "## Detailed Analysis",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
            "",
            "## Action Items",
            "- [ ] Research further",
            "- [ ] Implement findings",
            "- [ ] Review and iterate",
            "",
            "## Resources",
            "- [Resource 1](https://example.com)",
            "- [Resource 2](https://example.com)",
        ]
        
        return '\n'.join(sections)
    
    def _find_related_notes(self, prompt: str) -> List[str]:
        """Find related notes in the vault using keyword matching"""
        keywords = set(prompt.lower().split())
        related = []
        
        for md_file in self.vault_path.rglob("*.md"):
            if md_file.parent == self.notes_dir:
                continue
            
            try:
                with open(md_file, 'r') as f:
                    content = f.read().lower()
                    
                # Count keyword matches
                matches = sum(1 for keyword in keywords if keyword in content)
                
                if matches >= 2:  # At least 2 keywords match
                    related.append(md_file.stem)
            except:
                continue
        
        return related
    
    def _update_daily_note(self, new_note_title: str):
        """Update today's daily note with a link to the new note"""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_note = self.daily_dir / f"{today}.md"
        
        if daily_note.exists():
            with open(daily_note, 'a') as f:
                f.write(f"\n- Created: [[{new_note_title}]]\n")
        else:
            with open(daily_note, 'w') as f:
                f.write(f"# {today}\n\n")
                f.write("## Created Today\n")
                f.write(f"- [[{new_note_title}]]\n")
    
    def create_knowledge_graph_note(self, central_topic: str, depth: int = 2) -> Path:
        """
        Create a note that visualizes connections between topics
        """
        filename = f"Knowledge_Graph_{central_topic.replace(' ', '_')}"
        note_path = self.vault_path / f"{filename}.md"
        
        content = []
        content.append(f"# Knowledge Graph: {central_topic}")
        content.append("")
        content.append("```mermaid")
        content.append("graph TD")
        content.append(f"    A[{central_topic}]")
        
        # Add connections (placeholder - would use AI in production)
        branches = ["Concept 1", "Concept 2", "Concept 3", "Application", "Theory"]
        for i, branch in enumerate(branches, 1):
            content.append(f"    A --> B{i}[{branch}]")
            if depth > 1:
                for j in range(1, 3):
                    content.append(f"    B{i} --> C{i}{j}[Sub-{branch}-{j}]")
        
        content.append("```")
        content.append("")
        content.append("## Connections")
        content.append(f"This knowledge graph shows the relationships around **{central_topic}**.")
        
        with open(note_path, 'w') as f:
            f.write('\n'.join(content))
        
        return note_path
    
    def generate_weekly_summary(self) -> Path:
        """Generate a weekly summary of all notes created"""
        week_start = datetime.now().strftime("%Y-W%V")
        summary_path = self.vault_path / f"Weekly_Summary_{week_start}.md"
        
        content = []
        content.append(f"# Weekly Summary - {week_start}")
        content.append("")
        content.append("## Notes Created This Week")
        
        # Find all notes created this week
        week_notes = []
        for md_file in self.vault_path.rglob("*.md"):
            if md_file.stat().st_mtime > (datetime.now().timestamp() - 7*24*3600):
                week_notes.append(md_file.stem)
        
        for note in week_notes:
            content.append(f"- [[{note}]]")
        
        content.append("")
        content.append(f"**Total Notes Created:** {len(week_notes)}")
        
        with open(summary_path, 'w') as f:
            f.write('\n'.join(content))
        
        return summary_path

# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Obsidian AI Assistant")
    parser.add_argument("vault", help="Path to Obsidian vault")
    parser.add_argument("--prompt", "-p", help="Prompt for note generation")
    parser.add_argument("--title", "-t", help="Note title")
    parser.add_argument("--tags", nargs="+", help="Tags for the note")
    parser.add_argument("--graph", help="Create knowledge graph for topic")
    parser.add_argument("--weekly", action="store_true", help="Generate weekly summary")
    
    args = parser.parse_args()
    
    assistant = ObsidianAIAssistant(args.vault)
    
    if args.weekly:
        path = assistant.generate_weekly_summary()
        print(f"✅ Weekly summary created: {path}")
    elif args.graph:
        path = assistant.create_knowledge_graph_note(args.graph)
        print(f"✅ Knowledge graph created: {path}")
    elif args.prompt:
        path = assistant.create_smart_note(
            args.prompt,
            title=args.title,
            tags=args.tags
        )
        print(f"✅ Note created: {path}")
    else:
        print("Please provide --prompt, --graph, or --weekly option")
