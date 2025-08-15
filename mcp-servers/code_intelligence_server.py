#!/usr/bin/env python3
"""
Code Intelligence MCP Server
Provides code analysis, generation, and project management capabilities
"""

from mcp.server import Server, logger
from mcp.server.models import ServerInfo
from mcp.types import ServerCapabilities, Tool, TextContent
from typing import List, Dict, Any, Optional
import os
import json
import ast
import subprocess
from pathlib import Path
import re
from datetime import datetime
import hashlib


app = Server("code-intelligence-server")


class CodeAnalyzer:
    """Analyze Python code for patterns, issues, and metrics"""
    
    @staticmethod
    def analyze_file(file_path: str) -> Dict[str, Any]:
        """Analyze a Python file"""
        try:
            path = Path(file_path).expanduser()
            if not path.exists() or not path.suffix == '.py':
                return {"error": "Not a valid Python file"}
            
            with open(path, 'r') as f:
                source = f.read()
            
            tree = ast.parse(source)
            
            analysis = {
                "file": str(path),
                "lines": len(source.splitlines()),
                "classes": [],
                "functions": [],
                "imports": [],
                "complexity": 0,
                "docstring_coverage": 0,
                "type_hints": False
            }
            
            # Walk the AST
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    analysis["classes"].append({
                        "name": node.name,
                        "methods": [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                        "docstring": ast.get_docstring(node) is not None
                    })
                
                elif isinstance(node, ast.FunctionDef):
                    # Check for type hints
                    has_type_hints = bool(node.returns or 
                                         any(arg.annotation for arg in node.args.args))
                    
                    analysis["functions"].append({
                        "name": node.name,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node) is not None,
                        "type_hints": has_type_hints
                    })
                    
                    if has_type_hints:
                        analysis["type_hints"] = True
                
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            analysis["imports"].append(alias.name)
                    else:
                        analysis["imports"].append(node.module or "")
            
            # Calculate metrics
            total_items = len(analysis["functions"]) + sum(len(c["methods"]) for c in analysis["classes"])
            if total_items > 0:
                with_docs = sum(1 for f in analysis["functions"] if f["docstring"])
                with_docs += sum(1 for c in analysis["classes"] for m in c["methods"] if c["docstring"])
                analysis["docstring_coverage"] = round((with_docs / total_items) * 100, 1)
            
            # Estimate complexity (simplified)
            analysis["complexity"] = len(analysis["functions"]) + len(analysis["classes"]) * 2
            
            return analysis
            
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def find_todos(directory: str) -> List[Dict[str, Any]]:
        """Find TODO/FIXME comments in code"""
        todos = []
        path = Path(directory).expanduser()
        
        patterns = [
            r'#\s*(TODO|FIXME|HACK|XXX|NOTE|OPTIMIZE|BUG):?\s*(.*)',
            r'//\s*(TODO|FIXME|HACK|XXX|NOTE|OPTIMIZE|BUG):?\s*(.*)',
        ]
        
        for file_path in path.rglob('*.py'):
            try:
                with open(file_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern in patterns:
                            if match := re.search(pattern, line, re.IGNORECASE):
                                todos.append({
                                    "file": str(file_path.relative_to(path)),
                                    "line": line_num,
                                    "type": match.group(1).upper(),
                                    "message": match.group(2).strip(),
                                    "context": line.strip()
                                })
            except:
                continue
        
        return todos


class ProjectManager:
    """Manage project structure and configuration"""
    
    @staticmethod
    def analyze_project(project_path: str) -> Dict[str, Any]:
        """Analyze project structure and configuration"""
        path = Path(project_path).expanduser()
        if not path.is_dir():
            return {"error": "Not a valid directory"}
        
        analysis = {
            "path": str(path),
            "name": path.name,
            "type": "unknown",
            "size": 0,
            "files": {"py": 0, "js": 0, "ts": 0, "md": 0, "json": 0, "yaml": 0},
            "structure": {},
            "dependencies": [],
            "tests": False,
            "documentation": False,
            "version_control": False
        }
        
        # Detect project type
        if (path / "package.json").exists():
            analysis["type"] = "node"
            with open(path / "package.json") as f:
                pkg = json.load(f)
                analysis["dependencies"] = list(pkg.get("dependencies", {}).keys())
        
        elif (path / "requirements.txt").exists():
            analysis["type"] = "python"
            with open(path / "requirements.txt") as f:
                analysis["dependencies"] = [
                    line.split("==")[0].strip() 
                    for line in f if line.strip() and not line.startswith("#")
                ]
        
        elif (path / "Cargo.toml").exists():
            analysis["type"] = "rust"
        
        elif (path / "go.mod").exists():
            analysis["type"] = "go"
        
        # Count files
        for file_path in path.rglob('*'):
            if file_path.is_file():
                analysis["size"] += file_path.stat().st_size
                ext = file_path.suffix[1:] if file_path.suffix else "none"
                if ext in analysis["files"]:
                    analysis["files"][ext] += 1
        
        # Check for common directories
        analysis["tests"] = (path / "tests").exists() or (path / "test").exists()
        analysis["documentation"] = (path / "docs").exists() or (path / "README.md").exists()
        analysis["version_control"] = (path / ".git").exists()
        
        # Build structure tree (simplified)
        def build_tree(p: Path, max_depth: int = 2, current_depth: int = 0):
            if current_depth >= max_depth:
                return "..."
            
            tree = {}
            try:
                for item in sorted(p.iterdir()):
                    if item.name.startswith('.'):
                        continue
                    if item.is_dir():
                        tree[item.name + "/"] = build_tree(item, max_depth, current_depth + 1)
                    else:
                        tree[item.name] = "file"
            except:
                pass
            return tree
        
        analysis["structure"] = build_tree(path)
        
        # Format size
        size_mb = analysis["size"] / (1024 * 1024)
        analysis["size_formatted"] = f"{size_mb:.2f} MB"
        
        return analysis


class CodeGenerator:
    """Generate code snippets and boilerplate"""
    
    @staticmethod
    def generate_pydantic_model(name: str, fields: List[Dict[str, str]]) -> str:
        """Generate a Pydantic model"""
        code = f"""from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class {name}(BaseModel):
    \"\"\"Generated {name} model\"\"\"
"""
        
        for field in fields:
            field_name = field.get("name", "field")
            field_type = field.get("type", "str")
            required = field.get("required", True)
            description = field.get("description", "")
            
            if not required:
                field_type = f"Optional[{field_type}]"
                default = " = None"
            else:
                default = ""
            
            if description:
                code += f"    {field_name}: {field_type} = Field(...{', ' if description else ''} description=\"{description}\")\n"
            else:
                code += f"    {field_name}: {field_type}{default}\n"
        
        code += """
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
"""
        return code
    
    @staticmethod
    def generate_fastapi_endpoint(method: str, path: str, name: str) -> str:
        """Generate FastAPI endpoint"""
        method_lower = method.lower()
        code = f"""from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()


@router.{method_lower}("{path}")
async def {name}("""
        
        if method_lower in ["post", "put", "patch"]:
            code += "data: BaseModel, "
        
        if "{" in path:
            # Extract path parameters
            params = re.findall(r'\{(\w+)\}', path)
            for param in params:
                code += f"{param}: str, "
        
        code = code.rstrip(", ")
        code += """):
    \"\"\"
    {method} {path}
    
    TODO: Add description
    \"\"\"
    try:
        # TODO: Implement logic
        result = {"message": "Success"}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""
        return code
    
    @staticmethod
    def generate_test(function_name: str, test_cases: List[Dict[str, Any]] = None) -> str:
        """Generate pytest test"""
        code = f"""import pytest
from unittest.mock import Mock, patch


def test_{function_name}_basic():
    \"\"\"Test basic functionality of {function_name}\"\"\"
    # Arrange
    # TODO: Set up test data
    
    # Act
    # TODO: Call function
    
    # Assert
    # TODO: Verify results
    assert True  # Replace with actual assertion


def test_{function_name}_edge_cases():
    \"\"\"Test edge cases for {function_name}\"\"\"
    # TODO: Test with None values
    # TODO: Test with empty inputs
    # TODO: Test with invalid inputs
    pass


def test_{function_name}_error_handling():
    \"\"\"Test error handling in {function_name}\"\"\"
    with pytest.raises(Exception):
        # TODO: Test error conditions
        pass
"""
        
        if test_cases:
            code += f"""

@pytest.mark.parametrize("input_val,expected", ["""
            for tc in test_cases:
                code += f"\n    ({tc.get('input')}, {tc.get('expected')}),"
            code += f"""
])
def test_{function_name}_parametrized(input_val, expected):
    \"\"\"Parametrized tests for {function_name}\"\"\"
    # result = {function_name}(input_val)
    # assert result == expected
    pass
"""
        
        return code


class DependencyManager:
    """Manage project dependencies"""
    
    @staticmethod
    def check_updates(project_path: str) -> Dict[str, Any]:
        """Check for dependency updates"""
        path = Path(project_path).expanduser()
        
        if (path / "requirements.txt").exists():
            try:
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json"],
                    capture_output=True,
                    text=True,
                    cwd=str(path)
                )
                
                if result.returncode == 0:
                    outdated = json.loads(result.stdout)
                    return {
                        "type": "python",
                        "outdated": outdated,
                        "count": len(outdated)
                    }
            except:
                pass
        
        return {"message": "No dependency file found or unable to check"}


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available code intelligence tools"""
    return [
        Tool(
            name="analyze_code",
            description="Analyze Python code for structure, metrics, and quality",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to Python file to analyze"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="analyze_project",
            description="Analyze project structure and configuration",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to project directory"
                    }
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="find_todos",
            description="Find TODO/FIXME comments in code",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in"
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="generate_pydantic_model",
            description="Generate a Pydantic model class",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Model class name"
                    },
                    "fields": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "required": {"type": "boolean"},
                                "description": {"type": "string"}
                            }
                        },
                        "description": "List of field definitions"
                    }
                },
                "required": ["name", "fields"]
            }
        ),
        Tool(
            name="generate_fastapi_endpoint",
            description="Generate FastAPI endpoint boilerplate",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                        "description": "HTTP method"
                    },
                    "path": {
                        "type": "string",
                        "description": "Endpoint path (e.g., /users/{id})"
                    },
                    "name": {
                        "type": "string",
                        "description": "Function name"
                    }
                },
                "required": ["method", "path", "name"]
            }
        ),
        Tool(
            name="generate_test",
            description="Generate pytest test boilerplate",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "Name of function to test"
                    },
                    "test_cases": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "input": {"type": "string"},
                                "expected": {"type": "string"}
                            }
                        },
                        "description": "Optional test cases"
                    }
                },
                "required": ["function_name"]
            }
        ),
        Tool(
            name="check_dependency_updates",
            description="Check for outdated dependencies",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to project directory"
                    }
                },
                "required": ["project_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name}")
    
    try:
        if name == "analyze_code":
            result = CodeAnalyzer.analyze_file(arguments["file_path"])
        
        elif name == "analyze_project":
            result = ProjectManager.analyze_project(arguments["project_path"])
        
        elif name == "find_todos":
            result = CodeAnalyzer.find_todos(arguments["directory"])
        
        elif name == "generate_pydantic_model":
            code = CodeGenerator.generate_pydantic_model(
                arguments["name"],
                arguments["fields"]
            )
            result = {"code": code, "language": "python"}
        
        elif name == "generate_fastapi_endpoint":
            code = CodeGenerator.generate_fastapi_endpoint(
                arguments["method"],
                arguments["path"],
                arguments["name"]
            )
            result = {"code": code, "language": "python"}
        
        elif name == "generate_test":
            code = CodeGenerator.generate_test(
                arguments["function_name"],
                arguments.get("test_cases")
            )
            result = {"code": code, "language": "python"}
        
        elif name == "check_dependency_updates":
            result = DependencyManager.check_updates(arguments["project_path"])
        
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Format code results specially
        if isinstance(result, dict) and "code" in result:
            return [TextContent(
                type="text",
                text=f"```{result.get('language', 'python')}\n{result['code']}\n```"
            )]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


@app.get_server_info()
async def get_server_info() -> ServerInfo:
    """Get server information"""
    return ServerInfo(
        name="Code Intelligence MCP Server",
        version="1.0.0",
        protocolVersion="1.0",
        capabilities=ServerCapabilities(tools=True)
    )


async def main():
    """Main entry point"""
    logger.info("Starting Code Intelligence MCP Server")
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.get_server_info(),
            raise_exceptions=True
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())