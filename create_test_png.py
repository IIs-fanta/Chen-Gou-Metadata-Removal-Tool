#!/usr/bin/env python3
"""
创建测试PNG文件，包含元数据
"""

from PIL import Image, PngImagePlugin
import json

def create_test_png_with_metadata():
    """创建一个包含ComfyUI工作流元数据的测试PNG文件"""
    
    # 创建一个简单的图像
    img = Image.new('RGB', (200, 200), color='blue')
    
    # 创建元数据
    metadata = PngImagePlugin.PngInfo()
    
    # 添加一些ComfyUI风格的元数据
    workflow_data = {
        "last_node_id": 15,
        "last_link_id": 20,
        "nodes": [
            {"id": 1, "type": "CheckpointLoaderSimple", "pos": [100, 200], "size": {"0": 315, "1": 98}},
            {"id": 2, "type": "CLIPTextEncode", "pos": [400, 200], "size": {"0": 300, "1": 200}},
            {"id": 3, "type": "VAEDecode", "pos": [800, 200], "size": {"0": 210, "1": 46}},
        ],
        "links": [
            [1, 0, 2, 0, " Conditioning"],
            [2, 0, 3, 0, "LATENT"]
        ]
    }
    
    # 添加各种类型的文本块（这些将被新算法丢弃）
    metadata.add_text("workflow", json.dumps(workflow_data, indent=2))
    metadata.add_text("prompt", '{"positive": "beautiful landscape", "negative": "blurry"}')
    metadata.add_text("ComfyUI", '{"version": "0.4.2"}')
    metadata.add_text("parameters", '{"width": 512, "height": 512, "steps": 20}')
    
    # 添加一些安全块（这些应该被保留）
    # 注意：PIL会自动添加一些辅助块，我们可以通过后续处理验证
    
    # 保存文件
    output_path = "test_input.png"
    img.save(output_path, "PNG", pnginfo=metadata)
    
    # 获取文件大小
    import os
    file_size = os.path.getsize(output_path)
    
    print(f"已创建测试PNG文件: {output_path}")
    print(f"文件大小: {file_size} 字节")
    print("包含的元数据类型:")
    print("- workflow (ComfyUI工作流)")
    print("- prompt (提示词)")
    print("- ComfyUI (版本信息)")
    print("- parameters (生成参数)")
    print("\n这些元数据将被新的块处理算法丢弃，但图像数据(IDAT)将完全保留。")
    
    return output_path

if __name__ == "__main__":
    create_test_png_with_metadata()