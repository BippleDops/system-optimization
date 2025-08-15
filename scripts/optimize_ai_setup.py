#!/usr/bin/env python3
"""
AI Setup Optimizer - Configures and optimizes ComfyUI and Stable Diffusion WebUI
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Any

class AIOptimizer:
    def __init__(self):
        self.home = Path.home()
        self.comfyui_path = self.home / "ComfyUI"
        self.sd_webui_path = self.home / "stable-diffusion-webui"
        self.stats = {
            "models_found": 0,
            "duplicates_removed": 0,
            "space_saved_mb": 0,
            "optimizations": []
        }
    
    def optimize_comfyui(self):
        """Optimize ComfyUI settings"""
        settings_path = self.comfyui_path / "user" / "default" / "comfyui.settings.json"
        
        optimal_settings = {
            "Comfy.DevMode": False,
            "Comfy.PreviewFormat": "webp",
            "Comfy.DisableSliders": False,
            "Comfy.DisableFloatRounding": False,
            "Comfy.FloatRoundingPrecision": 3,
            "Comfy.SnapToGrid": True,
            "Comfy.SnapToGridSize": 10,
            "Comfy.Workflow.ShowMinimap": True,
            "Comfy.Workflow.MinimapSize": 150,
            "Comfy.NodeAutoComplete.Enabled": True,
            "Comfy.NodeSearchBoxImpl": "default",
            "Comfy.LinkRenderMode": "spline",
            "Comfy.UseNewMenu": "Floating",
            "Comfy.Workflow.ZoomSpeed": 1.1,
            "Comfy.Graph.CanvasInfo": True,
            "Comfy.Graph.CanvasInfoPosition": "top-right",
            "Comfy.NodeBadge.NodeIdBadgeMode": "None",
            "Comfy.NodeBadge.NodeSourceBadgeMode": "None",
            "Comfy.NodeBadge.NodeLifeCycleBadgeMode": "None",
            "Comfy.Keybinding.UseKeybindingForCtrlUpDown": False,
            "Comfy.TextareaWidget.FontSize": 12,
            "Comfy.ConfirmClear": True,
            "Comfy.PromptFilename": True,
            "Comfy.Queue.BatchCount": 1,
            "Comfy.ModelManager.ModelPathsFile": "extra_model_paths.yaml",
            "Comfy.Workflow.WorkflowTabsPosition": "Tabs",
            "Comfy.TreeExplorer.ItemHeight": 24,
            "Comfy.Sidebar.Location": "left",
            "Comfy.Sidebar.Size": 300,
            "Comfy.InvertMenuScrolling": False,
            "Comfy.MiddleClickAction": "Pan",
            "Comfy.NodeDefaults.SavedImagePrefix": "ComfyUI",
            "Comfy.NodeDefaults.CheckpointLoader.ckpt_name": "",
            "AGL.DevMode": False,
            "AGL.UseNewMenu": "Floating"
        }
        
        # Ensure directory exists
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write optimized settings
        with open(settings_path, 'w') as f:
            json.dump(optimal_settings, f, indent=2)
        
        self.stats["optimizations"].append("ComfyUI settings optimized")
        print("✅ ComfyUI settings optimized")
    
    def optimize_sd_webui(self):
        """Optimize Stable Diffusion WebUI settings"""
        config_path = self.sd_webui_path / "config.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Optimal settings for performance
        optimizations = {
            "samples_save": True,
            "samples_format": "png",
            "grid_save": True,
            "return_grid": True,
            "do_not_show_images": False,
            "add_model_hash_to_info": True,
            "add_model_name_to_info": True,
            "disable_weights_auto_swap": False,
            "inpainting_mask_weight": 1.0,
            "initial_noise_multiplier": 1.0,
            "CLIP_stop_at_last_layers": 1,
            "upcast_attn": False,
            "auto_launch_browser": "Local",
            "show_progress_in_title": True,
            "quicksettings_list": [
                "sd_model_checkpoint",
                "sd_vae",
                "CLIP_stop_at_last_layers"
            ],
            "ui_tab_order": [],
            "hidden_tabs": [],
            "show_progressbar": True,
            "live_previews_enable": True,
            "live_preview_content": "Prompt",
            "live_preview_refresh_period": 1000,
            "save_images_before_face_restoration": False,
            "save_images_before_highres_fix": False,
            "save_images_before_color_correction": False,
            "save_mask": False,
            "save_mask_composite": False,
            "jpeg_quality": 95,
            "webp_lossless": False,
            "img_max_size_mp": 200,
            "use_original_name_batch": True,
            "use_upscaler_name_as_suffix": False,
            "save_selected_only": True,
            "save_init_img": False,
            "temp_dir": "",
            "clean_temp_dir_at_start": True,
            "save_incomplete_images": False,
            "notification_audio": False,
            "notification_volume": 100,
            "outdir_samples": "",
            "outdir_txt2img_samples": "outputs/txt2img-images",
            "outdir_img2img_samples": "outputs/img2img-images",
            "outdir_extras_samples": "outputs/extras-images",
            "outdir_grids": "",
            "outdir_txt2img_grids": "outputs/txt2img-grids",
            "outdir_img2img_grids": "outputs/img2img-grids",
            "outdir_save": "log/images",
            "outdir_init_images": "outputs/init-images",
            "gradio_theme": "Default",
            "gradio_themes_cache": True,
            "gallery_height": "",
            "sd_checkpoint_cache": 1,
            "sd_vae_checkpoint_cache": 0,
            "sd_vae_overrides_per_model_preferences": True,
            "auto_vae_precision_bfloat16": False,
            "auto_vae_precision": True,
            "sd_vae_encode_method": "Full",
            "sd_vae_decode_method": "Full",
            "sd_vae_sliced_encode": False,
            "sd_vae_sliced_decode": False,
            "rollback_vae": False,
            "sd_lora": "None",
            "lora_preferred_name": "Alias from file",
            "lora_add_hashes_to_infotext": True,
            "lora_show_all": False,
            "lora_hide_unknown_for_versions": [],
            "lora_in_memory_limit": 0,
            "lora_not_found_warning_console": False,
            "lora_not_found_gradio_warning": False,
            "cross_attention_optimization": "Automatic",
            "cross_attention_options": [],
            "s_min_uncond": 0.0,
            "token_merging_ratio": 0.0,
            "token_merging_ratio_img2img": 0.0,
            "token_merging_ratio_hr": 0.0,
            "pad_cond_uncond": False,
            "pad_cond_uncond_v0": False,
            "persistent_cond_cache": True,
            "batch_cond_uncond": True,
            "fp8_storage": "Disable",
            "cache_fp16_weight": False,
            "hide_ldm_prints": True,
            "disable_mmap_load_safetensors": False,
            "use_old_emphasis_implementation": False,
            "use_old_karras_scheduler_sigmas": False,
            "no_dpmpp_sde_batch_determinism": False,
            "use_old_hires_fix_width_height": False,
            "dont_fix_second_order_samplers_schedule": False,
            "hires_fix_use_firstpass_conds": False,
            "use_old_scheduling": False,
            "use_downcasted_alpha_bar": False,
            "interrogate_keep_models_in_memory": False,
            "interrogate_return_ranks": False,
            "interrogate_clip_num_beams": 1,
            "interrogate_clip_min_length": 24,
            "interrogate_clip_max_length": 48,
            "interrogate_clip_dict_limit": 1500,
            "interrogate_clip_skip_categories": [],
            "interrogate_deepbooru_score_threshold": 0.5,
            "deepbooru_sort_alpha": True,
            "deepbooru_use_spaces": True,
            "deepbooru_escape": True,
            "deepbooru_filter_tags": "",
            "training_enable_tensorboard": False,
            "training_tensorboard_save_images": False,
            "training_tensorboard_flush_every": 120
        }
        
        config.update(optimizations)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.stats["optimizations"].append("SD-WebUI config optimized")
        print("✅ Stable Diffusion WebUI config optimized")
    
    def find_duplicate_models(self):
        """Find and remove duplicate model files"""
        model_dirs = [
            self.comfyui_path / "models",
            self.sd_webui_path / "models"
        ]
        
        model_hashes = {}
        duplicates = []
        
        for model_dir in model_dirs:
            if not model_dir.exists():
                continue
            
            for model_file in model_dir.rglob("*.safetensors"):
                # Get file size as simple duplicate check
                size = model_file.stat().st_size
                key = (model_file.name, size)
                
                if key in model_hashes:
                    duplicates.append((model_hashes[key], model_file))
                else:
                    model_hashes[key] = model_file
                
                self.stats["models_found"] += 1
        
        # Report duplicates (don't auto-delete for safety)
        if duplicates:
            print(f"\n⚠️  Found {len(duplicates)} potential duplicate models:")
            for original, duplicate in duplicates[:5]:  # Show first 5
                size_mb = duplicate.stat().st_size / (1024 * 1024)
                print(f"  - {duplicate.name} ({size_mb:.1f} MB)")
                self.stats["space_saved_mb"] += size_mb
        
        self.stats["duplicates_removed"] = len(duplicates)
    
    def create_model_symlinks(self):
        """Create symlinks to share models between ComfyUI and SD-WebUI"""
        # Map SD-WebUI directories to ComfyUI directories
        symlink_map = {
            "models/Stable-diffusion": "models/checkpoints",
            "models/VAE": "models/vae",
            "models/Lora": "models/loras",
            "models/ESRGAN": "models/upscale_models",
            "embeddings": "models/embeddings",
            "models/ControlNet": "models/controlnet"
        }
        
        for sd_dir, comfy_dir in symlink_map.items():
            sd_path = self.sd_webui_path / sd_dir
            comfy_path = self.comfyui_path / comfy_dir
            
            if sd_path.exists() and not comfy_path.exists():
                comfy_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    comfy_path.symlink_to(sd_path)
                    print(f"✅ Created symlink: {comfy_dir} -> {sd_dir}")
                    self.stats["optimizations"].append(f"Symlinked {comfy_dir}")
                except:
                    pass
    
    def cleanup_cache(self):
        """Clean up unnecessary cache files"""
        cache_dirs = [
            self.comfyui_path / "__pycache__",
            self.sd_webui_path / "__pycache__",
            self.home / ".cache" / "torch",
            self.home / ".cache" / "huggingface"
        ]
        
        for cache_dir in cache_dirs:
            if cache_dir.exists():
                try:
                    size_before = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
                    shutil.rmtree(cache_dir, ignore_errors=True)
                    self.stats["space_saved_mb"] += size_before / (1024 * 1024)
                    print(f"✅ Cleaned cache: {cache_dir.name}")
                except:
                    pass
    
    def print_report(self):
        """Print optimization report"""
        print("\n" + "="*60)
        print("🚀 AI SETUP OPTIMIZATION REPORT")
        print("="*60)
        print(f"📊 Models found: {self.stats['models_found']}")
        print(f"🔄 Duplicate models: {self.stats['duplicates_removed']}")
        print(f"💾 Potential space savings: {self.stats['space_saved_mb']:.1f} MB")
        print(f"✨ Optimizations applied: {len(self.stats['optimizations'])}")
        
        if self.stats['optimizations']:
            print("\n📋 Completed optimizations:")
            for opt in self.stats['optimizations']:
                print(f"  • {opt}")
        
        print("\n💡 Recommendations:")
        print("  1. Restart ComfyUI and SD-WebUI to apply settings")
        print("  2. Review duplicate models and remove manually if confirmed")
        print("  3. Consider using model symlinks to save space")
        print("  4. Enable xFormers for better performance if available")
        print("  5. Use --medvram or --lowvram flags if experiencing OOM errors")
        print("="*60)

def main():
    optimizer = AIOptimizer()
    
    print("🔧 Starting AI setup optimization...")
    
    # Run optimizations
    optimizer.optimize_comfyui()
    optimizer.optimize_sd_webui()
    optimizer.find_duplicate_models()
    optimizer.create_model_symlinks()
    optimizer.cleanup_cache()
    
    # Print report
    optimizer.print_report()

if __name__ == "__main__":
    main()
