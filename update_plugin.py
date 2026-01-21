#!/usr/bin/env python3
"""
ComfyUI Resolution Presets 插件更新脚本
自动安装/更新到最新版本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def get_plugin_path():
    """获取插件安装路径"""
    # 尝试从环境变量获取ComfyUI路径
    comfyui_path = os.environ.get('COMFYUI_PATH')
    if comfyui_path:
        custom_nodes_path = Path(comfyui_path) / 'custom_nodes'
    else:
        # 尝试常见路径
        possible_paths = [
            Path.cwd() / 'custom_nodes',
            Path.home() / 'ComfyUI' / 'custom_nodes',
            Path('/opt/ComfyUI/custom_nodes'),
        ]
        
        for path in possible_paths:
            if path.exists():
                custom_nodes_path = path
                break
        else:
            custom_nodes_path = Path.cwd() / 'custom_nodes'
            custom_nodes_path.mkdir(exist_ok=True)
    
    plugin_path = custom_nodes_path / 'ComfyUI_Sizepresets'
    return plugin_path

def install_plugin():
    """安装插件"""
    plugin_path = get_plugin_path()
    
    print(f"📦 安装插件到: {plugin_path}")
    
    # 如果已存在，备份旧版本
    if plugin_path.exists():
        backup_path = plugin_path.with_suffix('.backup')
        if backup_path.exists():
            shutil.rmtree(backup_path)
        shutil.move(plugin_path, backup_path)
        print(f"📋 已备份旧版本到: {backup_path}")
    
    # 创建插件目录
    plugin_path.mkdir(exist_ok=True)
    
    # 获取当前脚本所在目录的文件
    current_dir = Path(__file__).parent
    plugin_files = ['__init__.py', 'nodes.py', 'presets.py', 'utils.py', 'README.md', 'LICENSE']
    
    # 复制文件
    for file in plugin_files:
        src = current_dir / file
        dst = plugin_path / file
        if src.exists():
            shutil.copy2(src, dst)
            print(f"✅ 复制: {file}")
    
    print("\n✨ 安装完成！")
    print("重启ComfyUI后，在节点菜单中找到 'ResolutionPresets' 分类。")
    
    return plugin_path

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    
    dependencies = ['PIL', 'numpy', 'torch']
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep.lower() if dep == 'PIL' else dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"⚠️  缺少依赖: {', '.join(missing)}")
        print("建议手动安装: pip install pillow numpy torch")
    else:
        print("✅ 所有依赖已安装")

def main():
    """主函数"""
    print("=" * 50)
    print("ComfyUI Resolution Presets 插件安装器")
    print("=" * 50)
    
    try:
        plugin_path = install_plugin()
        check_dependencies()
        
        print("\n📚 插件信息:")
        print(f"   名称: Resolution Presets")
        print(f"   版本: 1.0.0")
        print(f"   作者: fan200617120-ui")
        print(f"   路径: {plugin_path}")
        print("\n🎉 安装成功！请重启ComfyUI。")
        
    except Exception as e:
        print(f"❌ 安装失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()