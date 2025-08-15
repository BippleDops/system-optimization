#!/usr/bin/env python3
"""
Audio Generation Server - Text to Speech, Music Generation, and Audio Processing
"""

import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import tempfile
import wave
import struct
import math

from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Audio Generation Server", version="1.0.0")

class TextToSpeechRequest(BaseModel):
    text: str
    voice: str = "default"
    language: str = "en"
    speed: float = 1.0
    pitch: float = 1.0
    emotion: Optional[str] = None

class MusicGenerationRequest(BaseModel):
    prompt: str
    duration: int = 30  # seconds
    style: str = "ambient"
    bpm: Optional[int] = None
    key: Optional[str] = None
    instruments: Optional[List[str]] = None

class AudioProcessingRequest(BaseModel):
    effect: str  # reverb, echo, pitch_shift, time_stretch, noise_reduction
    parameters: Dict[str, Any]

class AudioMixRequest(BaseModel):
    tracks: List[str]  # file paths
    volumes: Optional[List[float]] = None
    output_format: str = "mp3"

# Audio utilities
def generate_sine_wave(frequency: float, duration: float, sample_rate: int = 44100) -> bytes:
    """Generate a simple sine wave for testing"""
    samples = []
    for i in range(int(sample_rate * duration)):
        sample = 32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate)
        samples.append(struct.pack('<h', int(sample)))
    return b''.join(samples)

def create_wav_file(audio_data: bytes, sample_rate: int = 44100) -> str:
    """Create a WAV file from raw audio data"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    with wave.open(temp_file.name, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data)
    return temp_file.name

@app.post("/api/tts")
async def text_to_speech(request: TextToSpeechRequest):
    """Generate speech from text using system TTS or external models"""
    try:
        # For macOS, use the built-in 'say' command
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.aiff').name
        
        # Build the say command
        cmd = ['say']
        
        # Add voice if specified
        if request.voice != "default":
            cmd.extend(['-v', request.voice])
        
        # Add rate (words per minute, default is ~200)
        rate = int(200 * request.speed)
        cmd.extend(['-r', str(rate)])
        
        # Add output file
        cmd.extend(['-o', output_file])
        
        # Add the text
        cmd.append(request.text)
        
        # Execute the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"TTS failed: {result.stderr}")
        
        # Convert to MP3 for smaller file size
        mp3_file = output_file.replace('.aiff', '.mp3')
        subprocess.run(['ffmpeg', '-i', output_file, '-acodec', 'mp3', mp3_file, '-y'], 
                      capture_output=True)
        
        # Clean up AIFF file
        os.unlink(output_file)
        
        return FileResponse(
            mp3_file,
            media_type="audio/mpeg",
            filename=f"speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/voices")
async def list_voices():
    """List available TTS voices"""
    try:
        # Get macOS voices
        result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
        voices = []
        
        for line in result.stdout.split('\n'):
            if line.strip():
                parts = line.split()
                if len(parts) >= 2:
                    voice_name = parts[0]
                    language = parts[1] if len(parts) > 1 else "unknown"
                    voices.append({
                        "name": voice_name,
                        "language": language,
                        "description": ' '.join(parts[2:]) if len(parts) > 2 else ""
                    })
        
        return {"voices": voices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_music")
async def generate_music(request: MusicGenerationRequest):
    """Generate music based on text prompt"""
    try:
        # For now, generate a simple procedural melody
        # In production, integrate with models like MusicGen, AudioCraft, etc.
        
        duration = request.duration
        bpm = request.bpm or 120
        
        # Generate a simple melody pattern
        notes = [440, 494, 523, 587, 659, 698, 784]  # A major scale
        beat_duration = 60.0 / bpm
        
        audio_data = b''
        current_time = 0
        
        while current_time < duration:
            # Pick a random note from the scale
            import random
            note = random.choice(notes)
            
            # Generate note
            note_audio = generate_sine_wave(note, beat_duration * 0.8)
            
            # Add silence between notes
            silence = b'\x00\x00' * int(44100 * beat_duration * 0.2)
            
            audio_data += note_audio + silence
            current_time += beat_duration
        
        # Create WAV file
        wav_file = create_wav_file(audio_data)
        
        # Convert to MP3
        mp3_file = wav_file.replace('.wav', '.mp3')
        subprocess.run(['ffmpeg', '-i', wav_file, '-acodec', 'mp3', mp3_file, '-y'],
                      capture_output=True)
        
        os.unlink(wav_file)
        
        return FileResponse(
            mp3_file,
            media_type="audio/mpeg",
            filename=f"music_{request.style}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/process_audio")
async def process_audio(
    file: UploadFile = File(...),
    effect: str = "reverb",
    parameters: str = "{}"
):
    """Apply audio effects to uploaded file"""
    try:
        # Save uploaded file
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
        content = await file.read()
        temp_input.write(content)
        temp_input.close()
        
        # Parse parameters
        params = json.loads(parameters)
        
        # Output file
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
        
        # Build ffmpeg command based on effect
        cmd = ['ffmpeg', '-i', temp_input.name]
        
        if effect == "reverb":
            reverb_amount = params.get('amount', 0.5)
            cmd.extend(['-af', f'aecho=0.8:0.9:{reverb_amount*1000}:0.3'])
        
        elif effect == "echo":
            delay = params.get('delay', 0.5)
            decay = params.get('decay', 0.5)
            cmd.extend(['-af', f'aecho=1.0:1.0:{delay*1000}:{decay}'])
        
        elif effect == "pitch_shift":
            semitones = params.get('semitones', 0)
            pitch_factor = 2 ** (semitones / 12)
            cmd.extend(['-af', f'asetrate=44100*{pitch_factor},aresample=44100'])
        
        elif effect == "time_stretch":
            speed = params.get('speed', 1.0)
            cmd.extend(['-filter:a', f'atempo={speed}'])
        
        elif effect == "noise_reduction":
            cmd.extend(['-af', 'afftdn=nf=-20:nr=10'])
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown effect: {effect}")
        
        cmd.extend([output_file, '-y'])
        
        # Execute ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Processing failed: {result.stderr}")
        
        # Clean up input
        os.unlink(temp_input.name)
        
        return FileResponse(
            output_file,
            media_type="audio/mpeg",
            filename=f"processed_{effect}_{Path(file.filename).stem}.mp3"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mix_audio")
async def mix_audio(request: AudioMixRequest):
    """Mix multiple audio tracks together"""
    try:
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{request.output_format}').name
        
        # Build ffmpeg command for mixing
        cmd = ['ffmpeg']
        
        # Add input files
        for track in request.tracks:
            cmd.extend(['-i', track])
        
        # Build filter complex for mixing
        filter_parts = []
        for i, track in enumerate(request.tracks):
            volume = request.volumes[i] if request.volumes and i < len(request.volumes) else 1.0
            filter_parts.append(f'[{i}:a]volume={volume}[a{i}]')
        
        # Mix all tracks
        mix_inputs = ''.join([f'[a{i}]' for i in range(len(request.tracks))])
        filter_parts.append(f'{mix_inputs}amix=inputs={len(request.tracks)}[out]')
        
        cmd.extend(['-filter_complex', ';'.join(filter_parts)])
        cmd.extend(['-map', '[out]', output_file, '-y'])
        
        # Execute
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Mixing failed: {result.stderr}")
        
        return FileResponse(
            output_file,
            media_type=f"audio/{request.output_format}",
            filename=f"mixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.output_format}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """API documentation"""
    return {
        "service": "Audio Generation Server",
        "version": "1.0.0",
        "endpoints": {
            "/api/tts": "Text to speech generation",
            "/api/voices": "List available TTS voices",
            "/api/generate_music": "Generate music from text prompt",
            "/api/process_audio": "Apply effects to audio files",
            "/api/mix_audio": "Mix multiple audio tracks",
            "/docs": "Interactive API documentation"
        },
        "supported_effects": [
            "reverb", "echo", "pitch_shift", "time_stretch", "noise_reduction"
        ],
        "note": "Requires ffmpeg installed on system"
    }

if __name__ == "__main__":
    print("🎵 Starting Audio Generation Server on http://localhost:8001")
    print("📚 API Documentation: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001)
