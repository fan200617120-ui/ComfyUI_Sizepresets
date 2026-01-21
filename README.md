# ComfyUI Resolution Presets 🎯

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Plugin-blue)](https://github.com/comfyanonymous/ComfyUI)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)

一个专业的ComfyUI分辨率预设与工具插件，支持多种AI模型的标准分辨率预设，提供智能尺寸计算和分辨率分析功能。

## ✨ 特性亮点

### 🎯 **核心功能**
- **多模型预设**：SD1.5、SDXL、FLUX、WAN、QWEN等完整预设
- **智能尺寸计算**：自动计算最优分辨率，支持多种长宽比
- **分辨率分析**：详细的技术参数分析和使用建议
- **专业工具**：长宽比计算器、批量处理等实用工具
###📐 **节点列表**
 节点	         功能	    说明
**分辨率预设** - 图像	处理图像和遮罩	支持多种裁剪和缩放算法
**分辨率预设** - 潜在空间	生成潜在空间	用于AI图像生成
**分辨率预设器**	获取分辨率值	控制其他节点尺寸
**分辨率计算器**	智能计算尺寸	支持多种缩放模式
**分辨率分析器**	分析分辨率信息	提供使用建议
**长宽比计算器**	计算长宽比	识别常见比例

### 📊 **支持的模型预设**
| 模型 | 预设数量 | 特点 |
|------|----------|------|
| **SD1.5** | 5个 | 经典512×512基础预设 |
| **SDXL** | 13个 | 1024×1024及多种长宽比 |
| **FLUX** | 27个 | 完整2K/3K/4K/5K/6K大尺寸 |
| **WAN** | 14个 | 手机端和网页端优化 |
| **QWEN** | 7个 | 通义千问专用分辨率 |
| **自定义** | 6个 | 常用自定义尺寸 |
### 🛠 **技术特性**
- 🚀 **高性能处理**：优化的Tensor/PIL转换，内存效率高
- 🎨 **专业命名**：统一的中文专业术语，易于理解
- 🔧 **模块化设计**：清晰的代码结构，易于维护扩展
- ✅ **完全兼容**：兼容所有ComfyUI工作流
  
## 📦 安装方法

### 方法一：通过ComfyUI Manager安装（推荐）
1. 打开ComfyUI，确保已安装ComfyUI-Manager
2. 点击"Manager" → "Install Custom Nodes"
3. 搜索"ComfyUI_Sizepresets"
4. 点击安装，重启ComfyUI

### 方法二：手动安装

cd ComfyUI/custom_nodes
git clone https://github.com/fan200617120-ui/ComfyUI_Sizepresets.git

### 基础使用
1. 在节点菜单中找到 ResolutionPresets 分类
2. 添加 分辨率预设器 节点
3. 选择模型和预设尺寸
4. 连接输出到你的工作流
📐 节点详解
1. 分辨率预设 - 图像处理图像和遮罩的分辨率调整，支持多种缩放算法和裁剪方式。
2. 分辨率预设 - 潜在空间生成指定分辨率的潜在空间张量，专为AI图像生成设计。
3. 分辨率预设器获取分辨率值，用于控制其他节点的尺寸参数。
🎨 FLUX 大尺寸预设示例：
• 1920×1080 (16:9) 2K
• 2560×1440 (16:9) 2.5K
• 3840×2160 (16:9) 4K UHD
• 4096×2160 (17:9) 4K DCI
• 5120×2880 (16:9) 5K
• 6144×3456 (16:9) 6K

![ComfyUI工作流示例](https://github.com/fan200617120-ui/ComfyUI_Sizepresets/blob/main/2026-01-22_010856.png?raw=true)

### 目录结构
ComfyUI-ResolutionPresets/
├── __init__.py
├── nodes.py
├── presets.py
├── utils.py
├── README.md
├── LICENSE
├── requirements.txt
├── workflow_examples/
│   ├── basic_workflow.json
│   └── advanced_workflow.json
└── web/
    └── resolution_presets.js

### 基础工作流 
{
  "nodes": [
    {
      "type": "ResolutionPresetSetter",
      "inputs": {
        "FLUX": "1920×1080 (16:9) 2K"
      }
    }
  ]
}

🤝 贡献指南欢迎提交Issue和PR！
📄 许可证MIT License￼如果这个插件对你有帮助，请给个⭐ Star！















