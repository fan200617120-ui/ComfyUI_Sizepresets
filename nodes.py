"""
ComfyUI Resolution Presets 节点定义
文件夹名：ComfyUI_Sizepresets
节点显示名：专业分辨率节点
"""

import torch
import numpy as np
from PIL import Image, ImageOps
from typing import Dict, Any, Tuple

# 导入预设
from .presets import PRESETS, CROP_METHODS, RESIZE_ALGOS, get_size_from_preset

class ResolutionPresetImage:
    """分辨率预设 - 图像处理"""
    
    @classmethod
    def INPUT_TYPES(cls):
        preset_dict = {k: ["关"] + [t[0] for t in PRESETS[k]] for k in PRESETS}
        return {
            "required": {
                **{k: (v, {"default": "关"}) for k, v in preset_dict.items()},
                "裁剪方式": (CROP_METHODS, {"default": "中心裁剪"}),
                "缩放算法": (RESIZE_ALGOS, {"default": "lanczos"}),
                "启用边长缩放": ("BOOLEAN", {"default": False}),
                "缩放至边": (["最长边", "最短边"], {"default": "最长边"}),
                "缩放长度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            },
            "optional": {
                "图像": ("IMAGE",),
                "遮罩": ("MASK",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("图像", "遮罩", "宽度", "高度")
    FUNCTION = "run"
    CATEGORY = "ResolutionPresets"  # 关键：专业分类名
    
    def run(self, 图像=None, 遮罩=None, **kwargs):
        use_edge = kwargs["启用边长缩放"]
        edge_mode = kwargs["缩放至边"]
        target_len = kwargs["缩放长度"]
        crop = kwargs["裁剪方式"]
        algo = kwargs["缩放算法"]
        
        # 边长缩放模式
        if use_edge:
            if 图像 is not None:
                b, h0, w0, c = 图像.shape
                arr = (图像.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
                pil_img = Image.fromarray(arr)
                pil_img = self._resize_by_edge(pil_img, edge_mode, target_len)
                arr = np.array(pil_img).astype(np.float32) / 255.0
                图像 = torch.from_numpy(arr).unsqueeze(0)
                out_w, out_h = pil_img.size
            else:
                图像 = torch.zeros((1, 512, 512, 3), dtype=torch.float32)
                out_w, out_h = 512, 512
            
            if 遮罩 is not None:
                b, h0, w0 = 遮罩.shape
                arr = (遮罩.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
                pil_msk = Image.fromarray(arr, mode="L")
                pil_msk = self._resize_by_edge(pil_msk, edge_mode, target_len)
                arr = np.array(pil_msk).astype(np.float32) / 255.0
                遮罩 = torch.from_numpy(arr).unsqueeze(0)
            else:
                遮罩 = torch.zeros((1, out_h, out_w), dtype=torch.float32)
            
            return (图像, 遮罩, out_w, out_h)
        
        # 预设尺寸模式
        choices = {k: kwargs[k] for k in PRESETS}
        w, h = get_size_from_preset(choices)
        
        if 图像 is not None:
            b, h0, w0, c = 图像.shape
            arr = (图像.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
            pil_img = Image.fromarray(arr)
            pil_img = self._resize_crop(pil_img, w, h, crop, algo)
            arr = np.array(pil_img).astype(np.float32) / 255.0
            图像 = torch.from_numpy(arr).unsqueeze(0)
        else:
            图像 = torch.zeros((1, h, w, 3), dtype=torch.float32)
        
        if 遮罩 is not None:
            b, h0, w0 = 遮罩.shape
            arr = (遮罩.squeeze(0).cpu().numpy() * 255).astype(np.uint8)
            pil_msk = Image.fromarray(arr, mode="L")
            pil_msk = self._resize_crop(pil_msk, w, h, crop, algo)
            arr = np.array(pil_msk).astype(np.float32) / 255.0
            遮罩 = torch.from_numpy(arr).unsqueeze(0)
        else:
            遮罩 = torch.zeros((1, h, w), dtype=torch.float32)
        
        return (图像, 遮罩, w, h)
    
    def _resize_crop(self, image: Image.Image, tgt_w, tgt_h, crop_method, algo) -> Image.Image:
        if crop_method == "中心裁剪":
            image = ImageOps.fit(image, (tgt_w, tgt_h), method=Image.Resampling[algo.upper()])
        else:
            image = image.resize((tgt_w, tgt_h), resample=Image.Resampling[algo.upper()])
        return image
    
    def _resize_by_edge(self, pil_img: Image.Image, edge_mode: str, target_len: int) -> Image.Image:
        w, h = pil_img.size
        if edge_mode == "最长边":
            if w >= h:
                new_w, new_h = target_len, int(h * target_len / w)
            else:
                new_w, new_h = int(w * target_len / h), target_len
        else:  # 最短边
            if w <= h:
                new_w, new_h = target_len, int(h * target_len / w)
            else:
                new_w, new_h = int(w * target_len / h), target_len
        return pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

class ResolutionPresetLatent:
    """分辨率预设 - 潜在空间"""
    
    @classmethod
    def INPUT_TYPES(cls):
        preset_dict = {k: ["关"] + [t[0] for t in PRESETS[k]] for k in PRESETS}
        return {
            "required": {
                **{k: (v, {"default": "关"}) for k, v in preset_dict.items()},
                "启用自定义尺寸": ("BOOLEAN", {"default": False}),
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    FUNCTION = "run"
    CATEGORY = "ResolutionPresets"  # 关键：专业分类名
    
    def run(self, **kwargs):
        use_custom = kwargs["启用自定义尺寸"]
        if use_custom:
            w, h = kwargs["宽度"], kwargs["高度"]
        else:
            choices = {k: kwargs[k] for k in PRESETS}
            w, h = get_size_from_preset(choices)
        latent = torch.zeros([1, 4, h // 8, w // 8])
        return ({"samples": latent},)

class ResolutionPresetSetter:
    """分辨率预设器"""
    
    @classmethod
    def INPUT_TYPES(cls):
        preset_dict = {k: ["关"] + [t[0] for t in PRESETS[k]] for k in PRESETS}
        return {
            "required": {
                **{k: (v, {"default": "关"}) for k, v in preset_dict.items()},
                "启用自定义尺寸": ("BOOLEAN", {"default": False}),
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }
    
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("宽度", "高度")
    FUNCTION = "run"
    CATEGORY = "ResolutionPresets"  # 关键：专业分类名
    
    def run(self, **kwargs):
        use_custom = kwargs["启用自定义尺寸"]
        if use_custom:
            return (kwargs["宽度"], kwargs["高度"])
        choices = {k: kwargs[k] for k in PRESETS}
        w, h = get_size_from_preset(choices)
        return (w, h)

# 节点注册 - 使用专业显示名
NODE_CLASS_MAPPINGS = {
    "ResolutionPresetImage": ResolutionPresetImage,
    "ResolutionPresetLatent": ResolutionPresetLatent,
    "ResolutionPresetSetter": ResolutionPresetSetter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ResolutionPresetImage": "分辨率预设 - 图像",
    "ResolutionPresetLatent": "分辨率预设 - 潜在空间",
    "ResolutionPresetSetter": "分辨率预设器",
}
