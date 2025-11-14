#!/usr/bin/env python3
"""
PNG块处理器测试脚本
测试新的基于块的流式处理算法
"""

import os
import sys
from main import PNGBlockProcessor

def test_png_processor():
    """测试PNG块处理器功能"""
    processor = PNGBlockProcessor()
    
    print("=" * 50)
    print("PNG块处理器测试")
    print("=" * 50)
    
    # 测试1: 检查是否是非PNG文件
    print("\n测试1: 文件类型检测")
    test_files = ["main.py", "README.md", "requirements.txt"]
    for file_path in test_files:
        if os.path.exists(file_path):
            is_png = processor.is_png_file(file_path)
            print(f"  {file_path}: {'是PNG文件' if is_png else '不是PNG文件'}")
    
    # 测试2: 创建测试PNG文件（包含元数据）
    print("\n测试2: 创建测试PNG文件")
    
    # 创建一个简单的测试PNG文件（包含一些文本块）
    test_png_path = "test_input.png"
    test_output_path = "test_output.png"
    
    # 模拟PNG文件的创建（这里我们只创建一个简单的文件用于测试）
    # 实际使用时应该有真实的PNG文件
    if not os.path.exists(test_png_path):
        print(f"  注意: 找不到测试PNG文件 {test_png_path}")
        print("  请手动准备一个包含ComfyUI工作流的PNG文件进行测试")
    
    # 测试3: 显示处理器的配置信息
    print("\n测试3: 处理器配置信息")
    print(f"  关键块 (必须保留): {sorted(processor.CRITICAL_CHUNKS)}")
    print(f"  安全辅助块 (可保留): {sorted(processor.SAFE_ANCILLARY_CHUNKS)}")
    print(f"  元数据块 (将被丢弃): {sorted(processor.METADATA_CHUNKS)}")
    
    # 测试4: 文件信息获取
    if os.path.exists(test_png_path):
        print(f"\n测试4: 获取PNG文件信息")
        info = processor.get_file_info(test_png_path)
        if info:
            print(f"  文件信息: {info}")
        else:
            print(f"  无法获取文件信息")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("\n使用方法:")
    print("1. 准备一个包含ComfyUI工作流的PNG文件")
    print("2. 运行主程序，导入该文件")
    print("3. 观察处理结果，验证元数据是否被正确移除")
    print("4. 比较处理前后的文件大小和处理速度")
    print("=" * 50)

def create_test_png():
    """创建一个简单的测试PNG文件（带元数据）"""
    try:
        from PIL import Image, PngImagePlugin
        import io
        
        # 创建一个简单的图像
        img = Image.new('RGB', (100, 100), color='red')
        
        # 添加一些元数据（模拟ComfyUI工作流）
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("workflow", '{"nodes": [{"id": 1, "type": "Node1"}]}')
        metadata.add_text("prompt", '{"workflow": "test"}')
        metadata.add_text("parameters", '{"steps": 20}')
        
        # 保存图像
        img.save("test_input.png", "PNG", pnginfo=metadata)
        print("已创建测试PNG文件: test_input.png")
        
    except ImportError:
        print("无法创建测试PNG文件: PIL库不可用")
    except Exception as e:
        print(f"创建测试PNG文件失败: {str(e)}")

if __name__ == "__main__":
    # 如果命令行有参数，创建测试PNG文件
    if len(sys.argv) > 1 and sys.argv[1] == "create_test":
        create_test_png()
    else:
        test_png_processor()