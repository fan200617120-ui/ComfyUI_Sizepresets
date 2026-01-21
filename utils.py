"""
图像处理工具模块
"""
import torch
import numpy as np
from PIL import Image, ImageOps
from typing import Tuple, Optional, Dict, Any

class ImageUtils:
    """图像处理工具类"""
    
    @staticmethod
    def tensor_to_pil(tensor: torch.Tensor, is_mask: bool = False) -> Image.Image:
        """Tensor转PIL图像"""
        if tensor.dim() == 4:
            tensor = tensor.squeeze(0)
        elif tensor.dim() == 2:
            tensor = tensor.unsqueeze(0)
        
        if tensor.max() <= 1.0:
            tensor = tensor * 255
        
        arr = tensor.cpu().numpy().astype(np.uint8)
        
        if is_mask:
            return Image.fromarray(arr.squeeze(), mode='L')
        else:
            if arr.shape[0] == 3:
                arr = arr.transpose(1, 2, 0)
            elif arr.shape[0] == 1:
                arr = np.stack([arr.squeeze()] * 3, axis=-1)
            return Image.fromarray(arr)
    
    @staticmethod
    def pil_to_tensor(pil_img: Image.Image, is_mask: bool = False) -> torch.Tensor:
        """PIL图像转Tensor"""
        arr = np.array(pil_img).astype(np.float32) / 255.0
        
        if is_mask:
            if len(arr.shape) == 3:
                arr = arr.mean(axis=-1) if arr.shape[-1] > 1 else arr[..., 0]
            tensor = torch.from_numpy(arr).unsqueeze(0).unsqueeze(0)
        else:
            if len(arr.shape) == 2:
                arr = np.stack([arr] * 3, axis=-1)
            elif arr.shape[2] == 4:
                arr = arr[..., :3]
            
            arr = arr.transpose(2, 0, 1)
            tensor = torch.from_numpy(arr).unsqueeze(0)
        
        return tensor
    
    @staticmethod
    def resize_with_crop(
        image: Image.Image,
        width: int,
        height: int,
        crop_method: str,
        algo: str
    ) -> Image.Image:
        """带裁剪的缩放"""
        try:
            resample_method = getattr(Image.Resampling, algo.upper())
        except AttributeError:
            resample_method = Image.Resampling.LANCZOS
        
        if crop_method == "中心裁剪":
            return ImageOps.fit(image, (width, height), method=resample_method)
        else:
            return image.resize((width, height), resample=resample_method)
    
    @staticmethod
    def resize_by_edge(
        pil_img: Image.Image,
        edge_mode: str,
        target_length: int
    ) -> Image.Image:
        """按边长缩放"""
        width, height = pil_img.size
        
        if edge_mode == "最长边":
            if width >= height:
                new_width = target_length
                new_height = int(height * target_length / width)
            else:
                new_width = int(width * target_length / height)
                new_height = target_length
        else:  # 最短边
            if width <= height:
                new_width = target_length
                new_height = int(height * target_length / width)
            else:
                new_width = int(width * target_length / height)
                new_height = target_length
        
        return pil_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    @staticmethod
    def calculate_optimal_size(
        original_width: int,
        original_height: int,
        target_scale: float = 1.0,
        target_aspect_ratio: Optional[Tuple[int, int]] = None,
        max_side: int = 4096,
        multiple_of: int = 8
    ) -> Tuple[int, int]:
        """计算最优尺寸"""
        if target_aspect_ratio:
            target_w_ratio, target_h_ratio = target_aspect_ratio
            
            current_aspect = original_width / original_height
            target_aspect = target_w_ratio / target_h_ratio
            
            if current_aspect > target_aspect:
                new_width = int(original_height * target_aspect)
                new_height = original_height
            else:
                new_width = original_width
                new_height = int(original_width / target_aspect)
        else:
            new_width = int(original_width * target_scale)
            new_height = int(original_height * target_scale)
        
        max_current_side = max(new_width, new_height)
        if max_current_side > max_side:
            scale = max_side / max_current_side
            new_width = int(new_width * scale)
            new_height = int(new_height * scale)
        
        new_width = max(512, new_width)
        new_height = max(512, new_height)
        
        new_width = new_width - (new_width % multiple_of)
        new_height = new_height - (new_height % multiple_of)
        
        return new_width, new_height
    
    @staticmethod
    def get_resolution_info(width: int, height: int) -> Dict[str, Any]:
        """获取分辨率信息"""
        aspect_ratio = width / height
        
        total_pixels = width * height
        megapixels = total_pixels / 1000000
        
        if megapixels < 0.3:
            level = "极低"
        elif megapixels < 0.9:
            level = "低"
        elif megapixels < 2.0:
            level = "标清"
        elif megapixels < 3.7:
            level = "高清"
        elif megapixels < 8.3:
            level = "2K/2.5K"
        elif megapixels < 14.7:
            level = "4K"
        else:
            level = "超高"
        
        common_ratios = {
            (1, 1): "1:1 (正方形)",
            (4, 3): "4:3",
            (3, 2): "3:2",
            (16, 9): "16:9",
            (2, 3): "2:3",
            (3, 4): "3:4",
            (9, 16): "9:16",
            (21, 9): "21:9 (超宽屏)",
        }
        
        def ratio_to_float(r):
            return r[0] / r[1]
        
        closest_ratio = min(
            common_ratios.keys(),
            key=lambda r: abs(ratio_to_float(r) - aspect_ratio)
        )
        ratio_name = common_ratios.get(closest_ratio, f"{width}:{height}")
        
        return {
            "width": width,
            "height": height,
            "total_pixels": total_pixels,
            "megapixels": round(megapixels, 2),
            "aspect_ratio": round(aspect_ratio, 3),
            "aspect_name": ratio_name,
            "resolution_level": level,
            "is_landscape": width > height,
            "is_portrait": height > width,
            "is_square": width == height,
        }
