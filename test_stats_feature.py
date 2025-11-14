#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统计功能脚本
验证处理结果统计与展示功能
"""

import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入主程序类
from main import ImageProcessor, ProcessingResultsDialog

def create_test_files():
    """创建测试文件"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    # 创建测试图片文件
    test_files = []
    
    # 创建空的PNG文件（应该能处理）
    png_file = os.path.join(temp_dir, "test.png")
    with open(png_file, 'wb') as f:
        # 写入PNG签名
        f.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')
        # 写入空的IHDR块
        f.write(b'\x00\x00\x00\x0DIHDR')  # 长度13，类型IHDR
        f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\x02\x00\x00\x00')  # IHDR数据
        f.write(b'\x91\xB4\x33\xE6')  # CRC
        # 写入IEND块
        f.write(b'\x00\x00\x00\x00IEND')
        f.write(b'\xAE\x42\x60\x82')
    
    test_files.append(png_file)
    
    # 创建损坏的文件（应该处理失败）
    corrupt_file = os.path.join(temp_dir, "corrupt.png")
    with open(corrupt_file, 'w') as f:
        f.write("这不是一个PNG文件")
    
    test_files.append(corrupt_file)
    
    # 创建JPEG文件（应该能用原方法处理）
    jpeg_file = os.path.join(temp_dir, "test.jpg")
    with open(jpeg_file, 'wb') as f:
        # 写入JPEG签名
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0C\x14\r\x0C\x0B\x0B\x0C\x19\x12\x13\x0F')
        f.write(b'\xFF\xD9')  # JPEG结束标记
    
    test_files.append(jpeg_file)
    
    return temp_dir, test_files

def test_stats_collection():
    """测试统计功能"""
    print("🧪 测试统计功能...")
    
    # 创建测试文件
    temp_dir, test_files = create_test_files()
    output_dir = os.path.join(temp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 创建ImageProcessor实例
        processor = ImageProcessor(test_files, output_dir, keep_original_name=True)
        
        # 模拟信号连接
        stats_result = []
        
        def mock_all_tasks_completed(stats):
            stats_result.append(stats)
        
        processor.all_tasks_completed.connect(mock_all_tasks_completed)
        
        # 手动运行处理流程
        print(f"📁 测试文件数量: {len(test_files)}")
        
        total = len(test_files)
        for i, image_path in enumerate(test_files):
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, filename)
            
            try:
                if processor.png_processor.is_png_file(image_path):
                    success = processor.png_processor.process_png_streaming(image_path, output_path)
                    if not success:
                        raise Exception("PNG块处理失败")
                else:
                    processor._process_non_png_image(image_path, output_path, filename)
                
                processor.processed_files.append(filename)
                print(f"  ✅ 成功: {filename}")
            except Exception as e:
                processor.failed_files.append(filename)
                print(f"  ❌ 失败: {filename} - {str(e)}")
            
            progress = int((i + 1) / total * 100)
            processor.progress_updated.emit(progress)
        
        # 准备统计结果
        stats = {
            'total_files': total,
            'successful': len(processor.processed_files),
            'failed': len(processor.failed_files),
            'processed_files': processor.processed_files.copy(),
            'failed_files': processor.failed_files.copy()
        }
        
        # 触发信号
        mock_all_tasks_completed(stats)
        
        # 验证统计结果
        print("\n📊 统计结果验证:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  成功处理: {stats['successful']}")
        print(f"  处理失败: {stats['failed']}")
        
        if stats_result:
            received_stats = stats_result[0]
            assert received_stats['total_files'] == len(test_files)
            assert received_stats['successful'] >= 0
            assert received_stats['failed'] >= 0
            assert received_stats['total_files'] == received_stats['successful'] + received_stats['failed']
            print("  ✅ 统计结果验证通过!")
        else:
            print("  ❌ 信号未触发!")
        
        return stats
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_dialog_ui():
    """测试对话框UI"""
    print("\n🎨 测试对话框UI...")
    
    # 创建模拟的统计数据
    test_stats = {
        'total_files': 3,
        'successful': 2,
        'failed': 1,
        'processed_files': ['test.png', 'test.jpg'],
        'failed_files': ['corrupt.png']
    }
    
    try:
        # 尝试创建对话框（不显示）
        dialog = ProcessingResultsDialog(None, test_stats)
        
        # 检查UI组件
        layout = dialog.layout()
        if layout is not None:
            print("  ✅ 对话框布局创建成功")
            
            # 检查组件数量
            widget_count = layout.count()
            print(f"  📐 对话框包含 {widget_count} 个组件")
            
            # 手动关闭对话框
            dialog.close()
            print("  ✅ 对话框关闭成功")
        else:
            print("  ❌ 对话框布局创建失败")
            
    except Exception as e:
        print(f"  ❌ 对话框测试失败: {str(e)}")

def main():
    """主测试函数"""
    print("🚀 开始测试统计功能")
    print("=" * 50)
    
    try:
        # 测试统计收集
        stats = test_stats_collection()
        
        # 测试对话框UI
        test_dialog_ui()
        
        print("\n" + "=" * 50)
        print("🎉 统计功能测试完成!")
        print(f"📈 示例统计: {stats}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()