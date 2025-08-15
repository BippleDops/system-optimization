#!/usr/bin/env python3
"""
Mac Automation Server - System management, file organization, and automation workflows
"""

import os
import json
import subprocess
import psutil
import shutil
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import plistlib
import hashlib

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Mac Automation Server", version="1.0.0")

class SystemInfoRequest(BaseModel):
    include_processes: bool = False
    include_network: bool = False
    include_disks: bool = True

class FileOrganizeRequest(BaseModel):
    source_directory: str
    rules: Dict[str, List[str]]  # extension -> folder mapping
    dry_run: bool = True

class AutomationRequest(BaseModel):
    action: str  # cleanup_downloads, organize_desktop, backup_configs, optimize_storage
    parameters: Optional[Dict[str, Any]] = {}

class AppManagementRequest(BaseModel):
    action: str  # list, launch, quit, update, uninstall
    app_name: Optional[str] = None

class ScheduleTaskRequest(BaseModel):
    name: str
    command: str
    schedule: str  # cron format or "daily", "weekly", "monthly"
    enabled: bool = True

class ClipboardRequest(BaseModel):
    action: str  # get, set, history, clear
    content: Optional[str] = None

@app.get("/api/system/info")
async def get_system_info(
    include_processes: bool = False,
    include_network: bool = False,
    include_disks: bool = True
):
    """Get comprehensive system information"""
    try:
        info = {
            "platform": "macOS",
            "hostname": os.uname().nodename,
            "cpu": {
                "count": psutil.cpu_count(),
                "percent": psutil.cpu_percent(interval=1),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent,
                "used": psutil.virtual_memory().used
            },
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        if include_disks:
            info["disks"] = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    info["disks"].append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent
                    })
                except:
                    continue
        
        if include_processes:
            info["top_processes"] = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 1:  # Only show significant processes
                        info["top_processes"].append(pinfo)
                except:
                    continue
            info["top_processes"].sort(key=lambda x: x['cpu_percent'], reverse=True)
            info["top_processes"] = info["top_processes"][:10]
        
        if include_network:
            info["network"] = []
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == 2:  # IPv4
                        info["network"].append({
                            "interface": interface,
                            "address": addr.address,
                            "netmask": addr.netmask
                        })
        
        return info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/files/organize")
async def organize_files(request: FileOrganizeRequest):
    """Organize files based on rules"""
    try:
        source = Path(request.source_directory).expanduser()
        if not source.exists():
            raise HTTPException(status_code=404, detail="Source directory not found")
        
        moves = []
        
        for file_path in source.iterdir():
            if file_path.is_file():
                extension = file_path.suffix.lower()
                
                # Find matching rule
                target_folder = None
                for folder, extensions in request.rules.items():
                    if extension in extensions or extension[1:] in extensions:
                        target_folder = folder
                        break
                
                if target_folder:
                    target_dir = source / target_folder
                    target_path = target_dir / file_path.name
                    
                    moves.append({
                        "source": str(file_path),
                        "destination": str(target_path),
                        "size": file_path.stat().st_size
                    })
                    
                    if not request.dry_run:
                        target_dir.mkdir(exist_ok=True)
                        shutil.move(str(file_path), str(target_path))
        
        return {
            "dry_run": request.dry_run,
            "total_files": len(moves),
            "moves": moves,
            "message": "Files organized" if not request.dry_run else "Dry run completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/automation/execute")
async def execute_automation(request: AutomationRequest):
    """Execute predefined automation workflows"""
    try:
        if request.action == "cleanup_downloads":
            # Clean up old downloads
            downloads = Path("~/Downloads").expanduser()
            days_old = request.parameters.get("days_old", 30)
            cutoff = datetime.now() - timedelta(days=days_old)
            
            cleaned = []
            total_size = 0
            
            for file in downloads.iterdir():
                if file.is_file():
                    mtime = datetime.fromtimestamp(file.stat().st_mtime)
                    if mtime < cutoff:
                        size = file.stat().st_size
                        cleaned.append({
                            "file": file.name,
                            "size": size,
                            "age_days": (datetime.now() - mtime).days
                        })
                        total_size += size
                        
                        if not request.parameters.get("dry_run", True):
                            file.unlink()
            
            return {
                "action": "cleanup_downloads",
                "files_removed": len(cleaned),
                "space_freed": total_size,
                "details": cleaned[:20]  # Show first 20
            }
        
        elif request.action == "organize_desktop":
            # Organize desktop files
            desktop = Path("~/Desktop").expanduser()
            
            rules = {
                "Documents": [".pdf", ".doc", ".docx", ".txt", ".md"],
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg"],
                "Videos": [".mp4", ".mov", ".avi", ".mkv"],
                "Archives": [".zip", ".tar", ".gz", ".dmg"],
                "Code": [".py", ".js", ".html", ".css", ".json"]
            }
            
            organize_request = FileOrganizeRequest(
                source_directory=str(desktop),
                rules=rules,
                dry_run=request.parameters.get("dry_run", True)
            )
            
            return await organize_files(organize_request)
        
        elif request.action == "backup_configs":
            # Backup important configuration files
            backup_dir = Path("~/Documents/MacConfigBackup").expanduser()
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_folder = backup_dir / timestamp
            backup_folder.mkdir()
            
            configs = [
                "~/.zshrc",
                "~/.bashrc",
                "~/.gitconfig",
                "~/.ssh/config",
                "~/Library/Preferences/com.apple.Terminal.plist"
            ]
            
            backed_up = []
            for config in configs:
                config_path = Path(config).expanduser()
                if config_path.exists():
                    dest = backup_folder / config_path.name
                    shutil.copy2(config_path, dest)
                    backed_up.append(str(config_path))
            
            return {
                "action": "backup_configs",
                "backup_location": str(backup_folder),
                "files_backed_up": backed_up
            }
        
        elif request.action == "optimize_storage":
            # Find and suggest removal of large duplicate files
            target_dir = Path(request.parameters.get("directory", "~")).expanduser()
            
            file_hashes = {}
            duplicates = []
            
            for file_path in target_dir.rglob("*"):
                if file_path.is_file() and file_path.stat().st_size > 1024 * 1024:  # > 1MB
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read(1024 * 1024)).hexdigest()  # First 1MB
                        
                        if file_hash in file_hashes:
                            duplicates.append({
                                "original": str(file_hashes[file_hash]),
                                "duplicate": str(file_path),
                                "size": file_path.stat().st_size
                            })
                        else:
                            file_hashes[file_hash] = file_path
                    except:
                        continue
            
            total_duplicate_size = sum(d["size"] for d in duplicates)
            
            return {
                "action": "optimize_storage",
                "duplicates_found": len(duplicates),
                "potential_savings": total_duplicate_size,
                "duplicates": duplicates[:50]  # Show first 50
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/apps/manage")
async def manage_applications(request: AppManagementRequest):
    """Manage macOS applications"""
    try:
        if request.action == "list":
            # List installed applications
            apps = []
            app_dirs = ["/Applications", "~/Applications"]
            
            for app_dir in app_dirs:
                app_path = Path(app_dir).expanduser()
                if app_path.exists():
                    for app in app_path.glob("*.app"):
                        try:
                            info_plist = app / "Contents/Info.plist"
                            if info_plist.exists():
                                with open(info_plist, 'rb') as f:
                                    plist = plistlib.load(f)
                                
                                apps.append({
                                    "name": app.name,
                                    "path": str(app),
                                    "bundle_id": plist.get("CFBundleIdentifier", ""),
                                    "version": plist.get("CFBundleShortVersionString", ""),
                                    "size": sum(f.stat().st_size for f in app.rglob("*") if f.is_file())
                                })
                        except:
                            apps.append({
                                "name": app.name,
                                "path": str(app),
                                "bundle_id": "",
                                "version": "",
                                "size": 0
                            })
            
            return {"apps": sorted(apps, key=lambda x: x["name"])}
        
        elif request.action == "launch":
            # Launch an application
            if not request.app_name:
                raise HTTPException(status_code=400, detail="App name required")
            
            result = subprocess.run(
                ["open", "-a", request.app_name],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise HTTPException(status_code=500, detail=f"Failed to launch: {result.stderr}")
            
            return {"message": f"Launched {request.app_name}"}
        
        elif request.action == "quit":
            # Quit an application
            if not request.app_name:
                raise HTTPException(status_code=400, detail="App name required")
            
            result = subprocess.run(
                ["osascript", "-e", f'quit app "{request.app_name}"'],
                capture_output=True,
                text=True
            )
            
            return {"message": f"Quit {request.app_name}"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule/task")
async def schedule_task(request: ScheduleTaskRequest):
    """Schedule recurring tasks using launchd"""
    try:
        # Create launchd plist
        plist_content = {
            "Label": f"com.user.{request.name}",
            "ProgramArguments": request.command.split(),
            "RunAtLoad": request.enabled,
        }
        
        # Parse schedule
        if request.schedule == "daily":
            plist_content["StartCalendarInterval"] = {"Hour": 9, "Minute": 0}
        elif request.schedule == "weekly":
            plist_content["StartCalendarInterval"] = {"Weekday": 1, "Hour": 9, "Minute": 0}
        elif request.schedule == "monthly":
            plist_content["StartCalendarInterval"] = {"Day": 1, "Hour": 9, "Minute": 0}
        else:
            # Assume cron format - simplified parsing
            raise HTTPException(status_code=400, detail="Complex cron not yet supported")
        
        # Save plist
        plist_path = Path(f"~/Library/LaunchAgents/com.user.{request.name}.plist").expanduser()
        
        with open(plist_path, 'wb') as f:
            plistlib.dump(plist_content, f)
        
        # Load into launchd
        if request.enabled:
            subprocess.run(["launchctl", "load", str(plist_path)])
        
        return {
            "task": request.name,
            "scheduled": True,
            "plist_path": str(plist_path),
            "enabled": request.enabled
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clipboard")
async def manage_clipboard(request: ClipboardRequest):
    """Manage system clipboard"""
    try:
        if request.action == "get":
            # Get current clipboard content
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                text=True
            )
            
            return {"content": result.stdout}
        
        elif request.action == "set":
            # Set clipboard content
            if not request.content:
                raise HTTPException(status_code=400, detail="Content required")
            
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=request.content)
            
            return {"message": "Clipboard updated"}
        
        elif request.action == "clear":
            # Clear clipboard
            process = subprocess.Popen(
                ["pbcopy"],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input="")
            
            return {"message": "Clipboard cleared"}
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/shortcuts")
async def list_shortcuts():
    """List available Shortcuts (formerly Automator workflows)"""
    try:
        # List shortcuts
        result = subprocess.run(
            ["shortcuts", "list"],
            capture_output=True,
            text=True
        )
        
        shortcuts = []
        for line in result.stdout.split('\n'):
            if line.strip():
                shortcuts.append(line.strip())
        
        return {"shortcuts": shortcuts}
        
    except Exception as e:
        # Shortcuts CLI might not be available
        return {"shortcuts": [], "note": "Shortcuts CLI not available"}

@app.post("/api/shortcuts/run/{name}")
async def run_shortcut(name: str):
    """Run a specific Shortcut"""
    try:
        result = subprocess.run(
            ["shortcuts", "run", name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Shortcut failed: {result.stderr}")
        
        return {"output": result.stdout}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "Mac Automation Server",
        "version": "1.0.0",
        "endpoints": {
            "/api/system/info": "Get system information",
            "/api/files/organize": "Organize files by rules",
            "/api/automation/execute": "Execute automation workflows",
            "/api/apps/manage": "Manage applications",
            "/api/schedule/task": "Schedule recurring tasks",
            "/api/clipboard": "Manage clipboard",
            "/api/shortcuts": "List Shortcuts",
            "/api/shortcuts/run/{name}": "Run a Shortcut",
            "/docs": "Interactive API documentation"
        },
        "automations": [
            "cleanup_downloads",
            "organize_desktop",
            "backup_configs",
            "optimize_storage"
        ]
    }

if __name__ == "__main__":
    print("🖥️ Starting Mac Automation Server on http://localhost:8003")
    print("📚 API Documentation: http://localhost:8003/docs")
    uvicorn.run(app, host="0.0.0.0", port=8003)
