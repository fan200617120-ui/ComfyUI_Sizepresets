"""
分辨率预设与工具节点 - 专业版
文件夹名：ComfyUI_ResolutionPresets
节点显示名：专业分辨率节点
"""
import torch
import math
from typing import Dict, Any, Tuple
from .presets import get_size_from_preset, PRESETS, CROP_METHODS, RESIZE_ALGOS
from .utils import ImageUtils

class BaseResolutionNode:
    """基础分辨率节点"""
    
    @classmethod
    def get_preset_inputs(cls) -> Dict[str, Any]:
        return {
            k: (["关"] + [name for name, _ in v], {"default": "关"})
            for k, v in PRESETS.items()
        }
    
    @staticmethod
    def validate_resolution(width: int, height: int, min_size: int = 64, max_size: int = 8192) -> Tuple[int, int]:
        width = max(min_size, min(width, max_size))
        height = max(min_size, min(height, max_size))
        return width, height

# ========== 核心节点：保持专业显示名 ==========

class ResolutionPresetImage(BaseResolutionNode):
    """分辨率预设 - 图像处理"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                **cls.get_preset_inputs(),
                "裁剪方式": (CROP_METHODS, {"default": "中心裁剪"}),
                "缩放算法": (RESIZE_ALGOS, {"default": "lanczos"}),
                "启用边长缩放": ("BOOLEAN", {"default": False}),
                "缩放基准": (["最长边", "最短边"], {"default": "最长边"}),
                "缩放长度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            },
            "optional": {
                "图像输入": ("IMAGE",),
                "遮罩输入": ("MASK",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("图像输出", "遮罩输出", "宽度", "高度")
    FUNCTION = "process_image"
    CATEGORY = "ResolutionPresets"  # 专业分类名
    
    def process_image(self, 图像输入=None, 遮罩输入=None, **kwargs):
        use_edge = kwargs["启用边长缩放"]
        edge_mode = kwargs["缩放基准"]
        target_len = kwargs["缩放长度"]
        crop = kwargs["裁剪方式"]
        algo = kwargs["缩放算法"]
        
        if use_edge:
            if 图像输入 is not None:
                pil_img = ImageUtils.tensor_to_pil(图像输入)
                pil_img = ImageUtils.resize_by_edge(pil_img, edge_mode, target_len)
                图像输出 = ImageUtils.pil_to_tensor(pil_img)
                out_w, out_h = pil_img.size
            else:
                图像输出 = torch.zeros((1, 3, 512, 512), dtype=torch.float32)
                out_w, out_h = 512, 512
            
            if 遮罩输入 is not None:
                pil_msk = ImageUtils.tensor_to_pil(遮罩输入, is_mask=True)
                pil_msk = ImageUtils.resize_by_edge(pil_msk, edge_mode, target_len)
                遮罩输出 = ImageUtils.pil_to_tensor(pil_msk, is_mask=True)
            else:
                遮罩输出 = torch.zeros((1, 1, out_h, out_w), dtype=torch.float32)
            
            return (图像输出, 遮罩输出, out_w, out_h)
        
        choices = {k: kwargs[k] for k in PRESETS}
        w, h = get_size_from_preset(choices)
        
        if 图像输入 is not None:
            pil_img = ImageUtils.tensor_to_pil(图像输入)
            pil_img = ImageUtils.resize_with_crop(pil_img, w, h, crop, algo)
            图像输出 = ImageUtils.pil_to_tensor(pil_img)
        else:
            图像输出 = torch.zeros((1, 3, h, w), dtype=torch.float32)
        
        if 遮罩输入 is not None:
            pil_msk = ImageUtils.tensor_to_pil(遮罩输入, is_mask=True)
            pil_msk = ImageUtils.resize_with_crop(pil_msk, w, h, crop, algo)
            遮罩输出 = ImageUtils.pil_to_tensor(pil_msk, is_mask=True)
        else:
            遮罩输出 = torch.zeros((1, 1, h, w), dtype=torch.float32)
        
        return (图像输出, 遮罩输出, w, h)

class ResolutionPresetLatent(BaseResolutionNode):
    """分辨率预设 - 潜在空间"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                **cls.get_preset_inputs(),
                "启用自定义分辨率": ("BOOLEAN", {"default": False}),
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }
    
    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("潜在空间",)
    FUNCTION = "create_latent"
    CATEGORY = "ResolutionPresets"
    
    def create_latent(self, **kwargs):
        use_custom = kwargs["启用自定义分辨率"]
        
        if use_custom:
            w, h = kwargs["宽度"], kwargs["高度"]
        else:
            choices = {k: kwargs[k] for k in PRESETS}
            w, h = get_size_from_preset(choices)
        
        w, h = self.validate_resolution(w, h)
        latent = torch.zeros([1, 4, h // 8, w // 8])
        return ({"samples": latent},)

class ResolutionPresetSetter(BaseResolutionNode):
    """分辨率预设器"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                **cls.get_preset_inputs(),
                "启用自定义分辨率": ("BOOLEAN", {"default": False}),
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }
    
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("宽度", "高度")
    FUNCTION = "get_resolution"
    CATEGORY = "ResolutionPresets"
    
    def get_resolution(self, **kwargs):
        use_custom = kwargs["启用自定义分辨率"]
        
        if use_custom:
            w, h = kwargs["宽度"], kwargs["高度"]
        else:
            choices = {k: kwargs[k] for k in PRESETS}
            w, h = get_size_from_preset(choices)
        
        return self.validate_resolution(w, h)

# ========== 新增：极简比例计算器 ==========

class AspectRatioLock(BaseResolutionNode):
    """极简比例计算器 - 输入宽或高，另一个自动计算"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "锁定比例": ([
                    "1:1 (正方形)",
                    "4:3 (传统电视)",
                    "3:2 (经典照片)", 
                    "16:9 (宽屏)",
                    "2:3 (竖版照片)",
                    "3:4 (竖版传统)",
                    "9:16 (竖屏视频)",
                    "21:9 (超宽影院)",
                    "自定义比例"
                ], {"default": "16:9 (宽屏)"}),
                "自定义宽比": ("INT", {"default": 16, "min": 1, "max": 100, "step": 1}),
                "自定义高比": ("INT", {"default": 9, "min": 1, "max": 100, "step": 1}),
                "输入类型": (["输入宽度", "输入高度"], {"default": "输入宽度"}),
                "输入值": ("INT", {"default": 1920, "min": 64, "max": 8192, "step": 8}),
                "确保8的倍数": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("宽度", "高度", "比例信息")
    FUNCTION = "calculate_by_aspect"
    CATEGORY = "ResolutionPresets"
    
    def calculate_by_aspect(self, **kwargs):
        lock_ratio = kwargs["锁定比例"]
        custom_w = kwargs["自定义宽比"]
        custom_h = kwargs["自定义高比"]
        input_type = kwargs["输入类型"]
        input_value = kwargs["输入值"]
        ensure_multiple = kwargs["确保8的倍数"]
        
        # 1. 获取比例值
        if lock_ratio == "自定义比例":
            aspect_w = custom_w
            aspect_h = custom_h
        else:
            # 从字符串中提取比例，如"16:9 (宽屏)" -> 16:9
            ratio_part = lock_ratio.split(" ")[0]  # 获取"16:9"部分
            if ":" in ratio_part:
                aspect_w, aspect_h = map(int, ratio_part.split(":"))
            else:
                aspect_w, aspect_h = 16, 9  # 默认
        
        # 2. 根据输入类型计算
        if input_type == "输入宽度":
            # 已知宽度，计算高度
            width = input_value
            height = int(width * aspect_h / aspect_w)
        else:
            # 已知高度，计算宽度
            height = input_value
            width = int(height * aspect_w / aspect_h)
        
        # 3. 确保8的倍数
        if ensure_multiple:
            width = width - (width % 8)
            height = height - (height % 8)
        
        # 4. 确保最小尺寸
        width = max(64, width)
        height = max(64, height)
        
        # 5. 生成信息
        ratio_name = lock_ratio
        if lock_ratio == "自定义比例":
            ratio_name = f"{aspect_w}:{aspect_h} (自定义)"
        
        actual_ratio = width / height
        info_str = (
            f"🔒 锁定比例: {ratio_name}\n"
            f"📐 输出尺寸: {width} × {height}\n"
            f"📊 实际比例: {width}:{height} ≈ {actual_ratio:.3f}:1\n"
            f"📱 方向: {'横版 🌄' if width > height else '竖版 📱' if height > width else '正方形 ⬜'}"
        )
        
        return (width, height, info_str)

# ========== 新增：智能比例缩放器（原版，保留） ==========

class SmartAspectScaler(BaseResolutionNode):
    """智能比例缩放器 - 修改宽或高，自动按比例调整另一维度"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "目标比例": ([
                    "保持当前比例",
                    "1:1 (正方形)",
                    "4:3 (传统电视)",
                    "3:2 (经典照片)",
                    "16:9 (宽屏)",
                    "2:3 (竖版照片)",
                    "3:4 (竖版传统)",
                    "9:16 (竖屏视频)",
                    "21:9 (超宽影院)",
                    "自定义比例"
                ], {"default": "保持当前比例"}),
                "自定义比例_宽": ("INT", {"default": 16, "min": 1, "max": 100, "step": 1}),
                "自定义比例_高": ("INT", {"default": 9, "min": 1, "max": 100, "step": 1}),
                "当前宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "当前高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "调整维度": (["宽度", "高度"], {"default": "宽度"}),
                "目标值": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "确保8的倍数": ("BOOLEAN", {"default": True}),
                "限制最大边长": ("BOOLEAN", {"default": True}),
                "最大边长": ("INT", {"default": 4096, "min": 512, "max": 8192, "step": 8}),
            }
        }
    
    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("新宽度", "新高度", "比例信息")
    FUNCTION = "calculate_by_aspect"
    CATEGORY = "ResolutionPresets"
    
    def calculate_by_aspect(self, **kwargs):
        target_aspect = kwargs["目标比例"]
        custom_w = kwargs["自定义比例_宽"]
        custom_h = kwargs["自定义比例_高"]
        current_w = kwargs["当前宽度"]
        current_h = kwargs["当前高度"]
        adjust_dim = kwargs["调整维度"]
        target_value = kwargs["目标值"]
        ensure_multiple = kwargs["确保8的倍数"]
        limit_max = kwargs["限制最大边长"]
        max_side = kwargs["最大边长"]
        
        # 1. 计算目标比例
        aspect_ratio = None
        
        if target_aspect == "保持当前比例":
            # 使用当前宽高比
            aspect_ratio = current_w / current_h
        elif target_aspect == "自定义比例":
            aspect_ratio = custom_w / custom_h
        else:
            # 解析预设比例
            ratio_str = target_aspect.split(" ")[0]  # 获取"16:9"部分
            if ":" in ratio_str:
                w, h = map(int, ratio_str.split(":"))
                aspect_ratio = w / h
        
        if aspect_ratio is None:
            aspect_ratio = 1.0  # 默认1:1
        
        # 2. 根据调整维度计算新尺寸
        if adjust_dim == "宽度":
            # 固定宽度，计算高度
            new_width = target_value
            new_height = int(target_value / aspect_ratio)
        else:
            # 固定高度，计算宽度
            new_height = target_value
            new_width = int(target_value * aspect_ratio)
        
        # 3. 限制最大边长
        if limit_max:
            if new_width > max_side:
                scale = max_side / new_width
                new_width = max_side
                new_height = int(new_height * scale)
            elif new_height > max_side:
                scale = max_side / new_height
                new_height = max_side
                new_width = int(new_width * scale)
        
        # 4. 确保最小尺寸
        new_width = max(64, new_width)
        new_height = max(64, new_height)
        
        # 5. 确保8的倍数
        if ensure_multiple:
            new_width = new_width - (new_width % 8)
            new_height = new_height - (new_height % 8)
        
        # 6. 生成比例信息
        actual_ratio = new_width / new_height
        ratio_str = f"{new_width}:{new_height} ≈ {actual_ratio:.3f}:1"
        
        if abs(actual_ratio - 1.0) < 0.01:
            ratio_name = "1:1 (正方形)"
        elif abs(actual_ratio - 4/3) < 0.02:
            ratio_name = "4:3 (传统电视)"
        elif abs(actual_ratio - 3/2) < 0.02:
            ratio_name = "3:2 (经典照片)"
        elif abs(actual_ratio - 16/9) < 0.02:
            ratio_name = "16:9 (宽屏)"
        elif abs(actual_ratio - 2/3) < 0.02:
            ratio_name = "2:3 (竖版照片)"
        elif abs(actual_ratio - 3/4) < 0.02:
            ratio_name = "3:4 (竖版传统)"
        elif abs(actual_ratio - 9/16) < 0.02:
            ratio_name = "9:16 (竖屏视频)"
        elif abs(actual_ratio - 21/9) < 0.02:
            ratio_name = "21:9 (超宽影院)"
        else:
            # 简化比例
            gcd_val = math.gcd(new_width, new_height)
            simple_w = new_width // gcd_val
            simple_h = new_height // gcd_val
            ratio_name = f"{simple_w}:{simple_h} (自定义)"
        
        info_str = (
            f"📐 新尺寸: {new_width} × {new_height}\n"
            f"🔳 比例: {ratio_name}\n"
            f"📊 像素: {(new_width * new_height) / 1000000:.2f} MP\n"
            f"📱 方向: {'横版 🌄' if new_width > new_height else '竖版 📱' if new_height > new_width else '正方形 ⬜'}\n"
            f"🔗 原始比例: {current_w}:{current_h}"
        )
        
        return (new_width, new_height, info_str)

# ========== 工具节点 ==========

class ResolutionCalculator(BaseResolutionNode):
    """分辨率计算器"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "原始宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "原始高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "缩放模式": (["按比例", "按长宽比", "固定分辨率"], {"default": "按比例"}),
                "缩放比例": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 4.0, "step": 0.1}),
                "目标长宽比": (["保持原比例", "1:1", "4:3", "3:2", "16:9", "3:4", "2:3", "9:16", "21:9"], {"default": "保持原比例"}),
                "最大边长限制": ("INT", {"default": 4096, "min": 512, "max": 8192, "step": 8}),
                "确保8的倍数": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("INT", "INT", "STRING")
    RETURN_NAMES = ("宽度", "高度", "分辨率信息")
    FUNCTION = "calculate_resolution"
    CATEGORY = "ResolutionPresets"
    
    def calculate_resolution(self, **kwargs):
        width = kwargs["原始宽度"]
        height = kwargs["原始高度"]
        mode = kwargs["缩放模式"]
        scale = kwargs["缩放比例"]
        aspect = kwargs["目标长宽比"]
        max_side = kwargs["最大边长限制"]
        ensure_multiple = kwargs["确保8的倍数"]
        
        if mode == "固定分辨率":
            new_width, new_height = width, height
        elif mode == "按长宽比" and aspect != "保持原比例":
            if ":" in aspect:
                w_ratio, h_ratio = map(int, aspect.split(":"))
                new_width, new_height = ImageUtils.calculate_optimal_size(
                    width, height,
                    target_aspect_ratio=(w_ratio, h_ratio),
                    max_side=max_side,
                    multiple_of=8 if ensure_multiple else 1
                )
            else:
                new_width, new_height = width, height
        else:
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            if max(new_width, new_height) > max_side:
                scale_factor = max_side / max(new_width, new_height)
                new_width = int(new_width * scale_factor)
                new_height = int(new_height * scale_factor)
        
        if ensure_multiple:
            new_width = new_width - (new_width % 8)
            new_height = new_height - (new_height % 8)
        
        info = ImageUtils.get_resolution_info(new_width, new_height)
        info_str = (
            f"📐 分辨率: {new_width} × {new_height}\n"
            f"🔳 长宽比: {info['aspect_name']}\n"
            f"📊 像素: {info['megapixels']} MP ({info['resolution_level']})\n"
            f"📱 方向: {'横版 🌄' if info['is_landscape'] else '竖版 📱' if info['is_portrait'] else '正方形 ⬜'}"
        )
        
        return (new_width, new_height, info_str)

class ResolutionAnalyzer(BaseResolutionNode):
    """分辨率分析器"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("分辨率信息",)
    FUNCTION = "analyze_resolution"
    CATEGORY = "ResolutionPresets"
    
    def analyze_resolution(self, 宽度, 高度):
        info = ImageUtils.get_resolution_info(宽度, 高度)
        
        info_str = (
            f"分辨率: {info['width']}×{info['height']} ({info['aspect_name']})\n"
            f"像素: {info['megapixels']}MP • 等级: {info['resolution_level']}\n"
            f"方向: {'横版 🌄' if info['is_landscape'] else '竖版 📱' if info['is_portrait'] else '正方形 ⬜'}"
        )
        
        return (info_str,)

# ========== 节点注册 ==========

NODE_CLASS_MAPPINGS = {
    "ResolutionPresetImage": ResolutionPresetImage,
    "ResolutionPresetLatent": ResolutionPresetLatent,
    "ResolutionPresetSetter": ResolutionPresetSetter,
    "ResolutionCalculator": ResolutionCalculator,
    "ResolutionAnalyzer": ResolutionAnalyzer,
    "SmartAspectScaler": SmartAspectScaler,
    "AspectRatioLock": AspectRatioLock,  # 新增极简节点
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ResolutionPresetImage": "分辨率预设 - 图像",
    "ResolutionPresetLatent": "分辨率预设 - 潜在空间",
    "ResolutionPresetSetter": "分辨率预设器",
    "ResolutionCalculator": "分辨率计算器",
    "ResolutionAnalyzer": "分辨率分析器",
    "SmartAspectScaler": "智能比例缩放器",
    "AspectRatioLock": "极简比例计算器",  # 新增显示名
}

