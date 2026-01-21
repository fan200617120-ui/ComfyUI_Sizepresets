"""
分辨率预设与工具节点 - 专业版
包含所有尺寸处理功能的专业实现
"""
import torch
from typing import Dict, Any, Tuple
from .presets import get_size_from_preset, PRESETS, CROP_METHODS, RESIZE_ALGOS
from .utils import ImageUtils

class BaseResolutionNode:
    """基础分辨率节点 - 提供公共功能"""
    
    @classmethod
    def get_preset_inputs(cls) -> Dict[str, Any]:
        """获取预设输入选项"""
        return {
            k: (["关"] + [name for name, _ in v], {"default": "关"})
            for k, v in PRESETS.items()
        }
    
    @staticmethod
    def validate_resolution(width: int, height: int, min_size: int = 64, max_size: int = 8192) -> Tuple[int, int]:
        """验证分辨率是否在合理范围内"""
        width = max(min_size, min(width, max_size))
        height = max(min_size, min(height, max_size))
        return width, height

# ========== 专业分辨率处理节点 ==========

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
                "缩放长度": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 8192,
                    "step": 8
                }),
            },
            "optional": {
                "图像输入": ("IMAGE",),
                "遮罩输入": ("MASK",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "INT", "INT")
    RETURN_NAMES = ("图像输出", "遮罩输出", "宽度", "高度")
    FUNCTION = "process_image"
    CATEGORY = "ResolutionPresets"
    
    def process_image(self, 图像输入=None, 遮罩输入=None, **kwargs):
        use_edge = kwargs["启用边长缩放"]
        edge_mode = kwargs["缩放基准"]
        target_len = kwargs["缩放长度"]
        crop = kwargs["裁剪方式"]
        algo = kwargs["缩放算法"]
        
        # 边长缩放模式
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
        
        # 预设分辨率模式
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
        
        # 验证分辨率并创建潜在空间张量
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

# ========== 智能分辨率工具 ==========

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
                "目标长宽比": ([
                    "保持原比例", "1:1", "4:3", "3:2", "16:9", 
                    "3:4", "2:3", "9:16", "21:9"
                ], {"default": "保持原比例"}),
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
            # 解析长宽比
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
            # 按比例缩放
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # 应用最大边长限制
            if max(new_width, new_height) > max_side:
                scale_factor = max_side / max(new_width, new_height)
                new_width = int(new_width * scale_factor)
                new_height = int(new_height * scale_factor)
        
        # 确保是8的倍数
        if ensure_multiple:
            new_width = new_width - (new_width % 8)
            new_height = new_height - (new_height % 8)
        
        # 获取分辨率信息
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
                "详细模式": ("BOOLEAN", {"default": True}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("基本信息", "详细分析")
    FUNCTION = "analyze_resolution"
    CATEGORY = "ResolutionPresets"
    
    def analyze_resolution(self, 宽度, 高度, 详细模式):
        info = ImageUtils.get_resolution_info(宽度, 高度)
        
        # 基本信息
        basic_info = (
            f"分辨率: {info['width']}×{info['height']} "
            f"({info['aspect_name']})\n"
            f"像素: {info['megapixels']}MP • 等级: {info['resolution_level']}"
        )
        
        # 详细分析
        if 详细模式:
            detailed_info = self._generate_detailed_analysis(info)
        else:
            detailed_info = "详细分析已关闭"
        
        return (basic_info, detailed_info)
    
    def _generate_detailed_analysis(self, info: Dict[str, Any]) -> str:
        """生成详细的分辨率分析"""
        w, h = info['width'], info['height']
        mp = info['megapixels']
        aspect = info['aspect_ratio']
        
        analysis_lines = []
        analysis_lines.append("📊 详细分辨率分析")
        analysis_lines.append("══════════════════")
        
        # 基础信息
        analysis_lines.append(f"• 宽度: {w:,} 像素")
        analysis_lines.append(f"• 高度: {h:,} 像素")
        analysis_lines.append(f"• 总像素: {info['total_pixels']:,}")
        analysis_lines.append(f"• 百万像素: {mp:.2f} MP")
        analysis_lines.append(f"• 长宽比: {info['aspect_name']} ({aspect:.3f})")
        
        # 建议用途
        analysis_lines.append("\n💡 建议用途:")
        if mp < 0.5:
            analysis_lines.append("  ✓ 图标、小尺寸图片")
            analysis_lines.append("  ✓ 低分辨率预览图")
        elif mp < 2.0:
            analysis_lines.append("  ✓ 社交媒体分享")
            analysis_lines.append("  ✓ 网页图片展示")
            analysis_lines.append("  ✓ 手机壁纸")
        elif mp < 5.0:
            analysis_lines.append("  ✓ 高清壁纸")
            analysis_lines.append("  ✓ 印刷品（小尺寸）")
            analysis_lines.append("  ✓ 专业摄影展示")
        elif mp < 10.0:
            analysis_lines.append("  ✓ 4K显示器壁纸")
            analysis_lines.append("  ✓ 中等尺寸印刷")
            analysis_lines.append("  ✓ 高质量数字内容")
        else:
            analysis_lines.append("  ✓ 大幅面印刷品")
            analysis_lines.append("  ✓ 超高精度需求")
            analysis_lines.append("  ✓ 专业摄影后期")
        
        # 技术建议
        analysis_lines.append("\n🔧 技术建议:")
        if info['is_landscape']:
            analysis_lines.append("  • 适合横版内容展示")
        elif info['is_portrait']:
            analysis_lines.append("  • 适合竖版移动端内容")
        else:
            analysis_lines.append("  • 适合社交媒体头像、图标")
        
        # 模型匹配建议
        analysis_lines.append("\n🤖 AI模型匹配:")
        if w == h:
            analysis_lines.append("  • 适合所有模型的1:1生成")
        elif abs(aspect - 1.777) < 0.1:  # 接近16:9
            analysis_lines.append("  • 适合FLUX、SDXL的视频比例")
        elif abs(aspect - 0.667) < 0.1:  # 接近2:3
            analysis_lines.append("  • 适合SDXL、QWEN的竖版比例")
        
        analysis_lines.append("══════════════════")
        analysis_lines.append(f"生成时间建议: {self._get_render_time_estimate(mp)}")
        
        return "\n".join(analysis_lines)
    
    def _get_render_time_estimate(self, megapixels: float) -> str:
        """根据像素数估算渲染时间"""
        if megapixels < 1.0:
            return "快速（数秒）"
        elif megapixels < 4.0:
            return "中等（10-30秒）"
        elif megapixels < 10.0:
            return "较慢（30-60秒）"
        else:
            return "较慢（可能需要1分钟以上）"

# ========== 实用工具节点 ==========

class AspectRatioCalculator(BaseResolutionNode):
    """长宽比计算器"""
    
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        return {
            "required": {
                "宽度": ("INT", {"default": 1920, "min": 64, "max": 8192, "step": 8}),
                "高度": ("INT", {"default": 1080, "min": 64, "max": 8192, "step": 8}),
            }
        }
    
    RETURN_TYPES = ("FLOAT", "STRING")
    RETURN_NAMES = ("长宽比值", "长宽比描述")
    FUNCTION = "calculate_aspect"
    CATEGORY = "ResolutionPresets"
    
    def calculate_aspect(self, 宽度, 高度):
        # 计算最大公约数
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        
        w, h = 宽度, 高度
        divisor = gcd(w, h)
        ratio_w = w // divisor
        ratio_h = h // divisor
        aspect_ratio = w / h
        
        # 常见长宽比识别
        common_ratios = {
            1.0: "1:1 (正方形)",
            1.3333: "4:3 (传统电视)",
            1.5: "3:2 (传统胶片)",
            1.7778: "16:9 (高清视频)",
            1.6: "16:10 (显示器)",
            0.6667: "2:3 (竖版照片)",
            0.75: "3:4 (竖版照片)",
            0.5625: "9:16 (手机竖屏)",
            2.3333: "21:9 (电影超宽屏)",
        }
        
        # 找到最接近的常见长宽比
        closest_ratio = min(common_ratios.keys(), key=lambda x: abs(x - aspect_ratio))
        if abs(closest_ratio - aspect_ratio) < 0.01:
            description = common_ratios[closest_ratio]
        else:
            description = f"{ratio_w}:{ratio_h} (自定义比例)"
        
        return (float(aspect_ratio), description)

# ========== 节点注册 ==========

NODE_CLASS_MAPPINGS = {
    # 主功能节点
    "ResolutionPresetImage": ResolutionPresetImage,
    "ResolutionPresetLatent": ResolutionPresetLatent,
    "ResolutionPresetSetter": ResolutionPresetSetter,
    
    # 工具节点
    "ResolutionCalculator": ResolutionCalculator,
    "ResolutionAnalyzer": ResolutionAnalyzer,
    "AspectRatioCalculator": AspectRatioCalculator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    # 主功能节点
    "ResolutionPresetImage": "分辨率预设 - 图像",
    "ResolutionPresetLatent": "分辨率预设 - 潜在空间",
    "ResolutionPresetSetter": "分辨率预设器",
    
    # 工具节点
    "ResolutionCalculator": "分辨率计算器",
    "ResolutionAnalyzer": "分辨率分析器",
    "AspectRatioCalculator": "长宽比计算器",
}