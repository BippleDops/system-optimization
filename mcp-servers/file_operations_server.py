#!/usr/bin/env python3
"""
MCP File Operations Server
Provides file manipulation, search, and processing capabilities
"""

from mcp.server import Server, logger
from mcp.server.models import ServerInfo
from mcp.types import ServerCapabilities, Tool, TextContent
from typing import List, Dict, Any, Optional
import os
import json
import shutil
import hashlib
import mimetypes
from pathlib import Path
import zipfile
import tarfile
import csv


app = Server("file-operations-server")


def get_file_info(path: str) -> Dict[str, Any]:
    """Get detailed information about a file or directory"""
    try:
        path_obj = Path(path).expanduser()
        if not path_obj.exists():
            return {"error": f"Path does not exist: {path}"}
        
        stat = path_obj.stat()
        info = {
            "path": str(path_obj.absolute()),
            "name": path_obj.name,
            "exists": True,
            "is_file": path_obj.is_file(),
            "is_directory": path_obj.is_dir(),
            "size_bytes": stat.st_size,
            "size_human": format_bytes(stat.st_size),
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "permissions": oct(stat.st_mode)[-3:]
        }
        
        if path_obj.is_file():
            info["extension"] = path_obj.suffix
            info["mime_type"] = mimetypes.guess_type(str(path_obj))[0]
            
            # Calculate hash for small files
            if stat.st_size < 100 * 1024 * 1024:  # Less than 100MB
                with open(path_obj, 'rb') as f:
                    info["md5"] = hashlib.md5(f.read()).hexdigest()
        
        elif path_obj.is_dir():
            contents = list(path_obj.iterdir())
            info["item_count"] = len(contents)
            info["subdirectories"] = len([p for p in contents if p.is_dir()])
            info["files"] = len([p for p in contents if p.is_file()])
        
        return info
    
    except Exception as e:
        return {"error": str(e)}


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.2f} PB"


def search_files(directory: str, pattern: str, recursive: bool = True) -> List[str]:
    """Search for files matching a pattern"""
    try:
        path_obj = Path(directory).expanduser()
        if not path_obj.is_dir():
            return []
        
        if recursive:
            matches = list(path_obj.rglob(pattern))
        else:
            matches = list(path_obj.glob(pattern))
        
        return [str(m.absolute()) for m in matches]
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return []


def organize_files(directory: str, by: str = "extension") -> Dict[str, Any]:
    """Organize files in a directory by extension, date, or size"""
    try:
        path_obj = Path(directory).expanduser()
        if not path_obj.is_dir():
            return {"error": "Not a directory"}
        
        organized = {}
        
        for file_path in path_obj.iterdir():
            if file_path.is_file():
                if by == "extension":
                    ext = file_path.suffix or "no_extension"
                    target_dir = path_obj / ext[1:] if ext.startswith('.') else path_obj / ext
                elif by == "date":
                    from datetime import datetime
                    date = datetime.fromtimestamp(file_path.stat().st_mtime)
                    target_dir = path_obj / date.strftime("%Y-%m")
                elif by == "size":
                    size = file_path.stat().st_size
                    if size < 1024 * 1024:
                        target_dir = path_obj / "small"
                    elif size < 10 * 1024 * 1024:
                        target_dir = path_obj / "medium"
                    else:
                        target_dir = path_obj / "large"
                else:
                    continue
                
                target_dir.mkdir(exist_ok=True)
                new_path = target_dir / file_path.name
                
                if not new_path.exists():
                    shutil.move(str(file_path), str(new_path))
                    
                    category = str(target_dir.name)
                    if category not in organized:
                        organized[category] = []
                    organized[category].append(file_path.name)
        
        return {"organized": organized, "categories": len(organized)}
    
    except Exception as e:
        return {"error": str(e)}


def create_archive(source: str, output: str, format: str = "zip") -> Dict[str, Any]:
    """Create an archive from a file or directory"""
    try:
        source_path = Path(source).expanduser()
        output_path = Path(output).expanduser()
        
        if not source_path.exists():
            return {"error": f"Source does not exist: {source}"}
        
        if format == "zip":
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                if source_path.is_file():
                    zf.write(source_path, source_path.name)
                else:
                    for file_path in source_path.rglob('*'):
                        if file_path.is_file():
                            arc_name = file_path.relative_to(source_path.parent)
                            zf.write(file_path, arc_name)
        
        elif format in ["tar", "tar.gz", "tgz"]:
            mode = 'w:gz' if format in ["tar.gz", "tgz"] else 'w'
            with tarfile.open(output_path, mode) as tf:
                tf.add(source_path, arcname=source_path.name)
        
        else:
            return {"error": f"Unsupported format: {format}"}
        
        return {
            "archive": str(output_path.absolute()),
            "size": output_path.stat().st_size,
            "format": format
        }
    
    except Exception as e:
        return {"error": str(e)}


def process_csv(file_path: str, operation: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Process CSV files with various operations"""
    try:
        path_obj = Path(file_path).expanduser()
        if not path_obj.exists() or not path_obj.is_file():
            return {"error": "File not found"}
        
        params = params or {}
        
        if operation == "read":
            with open(path_obj, 'r') as f:
                reader = csv.DictReader(f)
                data = list(reader)
                return {
                    "rows": len(data),
                    "columns": list(data[0].keys()) if data else [],
                    "sample": data[:5] if len(data) > 5 else data
                }
        
        elif operation == "filter":
            column = params.get("column")
            value = params.get("value")
            output = params.get("output", str(path_obj.parent / f"{path_obj.stem}_filtered.csv"))
            
            with open(path_obj, 'r') as f_in:
                reader = csv.DictReader(f_in)
                rows = [row for row in reader if row.get(column) == value]
            
            if rows:
                with open(output, 'w', newline='') as f_out:
                    writer = csv.DictWriter(f_out, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
            
            return {"filtered_rows": len(rows), "output_file": output}
        
        elif operation == "merge":
            other_file = params.get("other_file")
            output = params.get("output", str(path_obj.parent / "merged.csv"))
            
            if not other_file:
                return {"error": "other_file parameter required"}
            
            other_path = Path(other_file).expanduser()
            
            with open(path_obj, 'r') as f1:
                data1 = list(csv.DictReader(f1))
            
            with open(other_path, 'r') as f2:
                data2 = list(csv.DictReader(f2))
            
            merged = data1 + data2
            
            if merged:
                all_keys = set()
                for row in merged:
                    all_keys.update(row.keys())
                
                with open(output, 'w', newline='') as f_out:
                    writer = csv.DictWriter(f_out, fieldnames=sorted(all_keys))
                    writer.writeheader()
                    writer.writerows(merged)
            
            return {"total_rows": len(merged), "output_file": output}
        
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    except Exception as e:
        return {"error": str(e)}


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available file operation tools"""
    return [
        Tool(
            name="get_file_info",
            description="Get detailed information about a file or directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the file or directory"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="search_files",
            description="Search for files matching a pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to search in"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Search pattern (e.g., '*.txt', 'test_*')"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Search recursively in subdirectories",
                        "default": True
                    }
                },
                "required": ["directory", "pattern"]
            }
        ),
        Tool(
            name="organize_files",
            description="Organize files in a directory by extension, date, or size",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to organize"
                    },
                    "by": {
                        "type": "string",
                        "enum": ["extension", "date", "size"],
                        "description": "Organization criteria",
                        "default": "extension"
                    }
                },
                "required": ["directory"]
            }
        ),
        Tool(
            name="create_archive",
            description="Create an archive from files or directories",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "description": "Source file or directory to archive"
                    },
                    "output": {
                        "type": "string",
                        "description": "Output archive path"
                    },
                    "format": {
                        "type": "string",
                        "enum": ["zip", "tar", "tar.gz", "tgz"],
                        "description": "Archive format",
                        "default": "zip"
                    }
                },
                "required": ["source", "output"]
            }
        ),
        Tool(
            name="process_csv",
            description="Process CSV files (read, filter, merge)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the CSV file"
                    },
                    "operation": {
                        "type": "string",
                        "enum": ["read", "filter", "merge"],
                        "description": "Operation to perform"
                    },
                    "params": {
                        "type": "object",
                        "description": "Additional parameters for the operation"
                    }
                },
                "required": ["file_path", "operation"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    logger.info(f"Tool called: {name}")
    
    try:
        if name == "get_file_info":
            result = get_file_info(arguments["path"])
        elif name == "search_files":
            result = search_files(
                arguments["directory"],
                arguments["pattern"],
                arguments.get("recursive", True)
            )
        elif name == "organize_files":
            result = organize_files(
                arguments["directory"],
                arguments.get("by", "extension")
            )
        elif name == "create_archive":
            result = create_archive(
                arguments["source"],
                arguments["output"],
                arguments.get("format", "zip")
            )
        elif name == "process_csv":
            result = process_csv(
                arguments["file_path"],
                arguments["operation"],
                arguments.get("params")
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        logger.error(f"Error in tool {name}: {str(e)}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


@app.get_server_info()
async def get_server_info() -> ServerInfo:
    """Get server information"""
    return ServerInfo(
        name="File Operations MCP Server",
        version="1.0.0",
        protocolVersion="1.0",
        capabilities=ServerCapabilities(tools=True)
    )


async def main():
    """Main entry point"""
    logger.info("Starting File Operations MCP Server")
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