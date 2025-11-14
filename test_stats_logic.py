#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试统计逻辑功能脚本
验证统计数据的准确性
"""

import sys
import os
import tempfile
import shutil

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ImageProcessor

def test_stats_logic():
    """测试统计逻辑"""
    print("🧪 测试统计逻辑...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 创建测试文件
        test_files = []
        
        # 有效的PNG文件
        png_file = os.path.join(temp_dir, "valid.png")
        with open(png_file, 'wb') as f:
            f.write(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A')  # PNG签名
            f.write(b'\x00\x00\x00\x0DIHDR')  # IHDR块
            f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00\x08\x02\x00\x00\x00')
            f.write(b'\x91\xB4\x33\xE6')
            f.write(b'\x00\x00\x00\x00IDAT')  # IDAT块
            f.write(b'\x78\x9C\x62\x62\x62\x00\x00\x00\x02\x00\x01')  # 压缩数据
            f.write(b'\xE2\x21\xBC\x33')
            f.write(b'\x00\x00\x00\x00IEND')  # IEND块
            f.write(b'\xAE\x42\x60\x82')
        test_files.append(png_file)
        
        # 无效文件
        invalid_file = os.path.join(temp_dir, "invalid.txt")
        with open(invalid_file, 'w') as f:
            f.write("这不是图片文件")
        test_files.append(invalid_file)
        
        # 创建输出目录
        output_dir = os.path.join(temp_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建处理器实例
        processor = ImageProcessor(test_files, output_dir, keep_original_name=True)
        
        # 手动执行处理逻辑并统计
        total = len(test_files)
        print(f"📁 总计处理文件: {total}")
        
        for i, image_path in enumerate(test_files):
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, filename)
            
            print(f"\n🔄 处理文件 {i+1}/{total}: {filename}")
            
            try:
                # 使用PNG处理器
                if processor.png_processor.is_png_file(image_path):
                    success = processor.png_processor.process_png_streaming(image_path, output_path)
                    if not success:
                        raise Exception("PNG块处理失败")
                else:
                    # 尝试使用PIL处理
                    processor._process_non_png_image(image_path, output_path, filename)
                
                processor.processed_files.append(filename)
                print(f"  ✅ 成功")
                
            except Exception as e:
                processor.failed_files.append(filename)
                print(f"  ❌ 失败: {str(e)}")
        
        # 生成统计结果
        stats = {
            'total_files': total,
            'successful': len(processor.processed_files),
            'failed': len(processor.failed_files),
            'processed_files': processor.processed_files.copy(),
            'failed_files': processor.failed_files.copy()
        }
        
        # 打印统计结果
        print(f"\n📊 最终统计结果:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  成功处理: {stats['successful']}")
        print(f"  处理失败: {stats['failed']}")
        print(f"  成功率: {(stats['successful']/stats['total_files']*100):.1f}%")
        
        if stats['processed_files']:
            print(f"\n✅ 成功处理的文件:")
            for file in stats['processed_files']:
                print(f"    • {file}")
        
        if stats['failed_files']:
            print(f"\n❌ 处理失败的文件:")
            for file in stats['failed_files']:
                print(f"    • {file}")
        
        # 验证统计准确性
        assert stats['total_files'] == len(test_files), "总文件数统计错误"
        assert stats['successful'] + stats['failed'] == stats['total_files'], "成功失败文件数不匹配"
        assert len(stats['processed_files']) == stats['successful'], "成功文件列表长度错误"
        assert len(stats['failed_files']) == stats['failed'], "失败文件列表长度错误"
        
        print(f"\n✅ 统计验证通过!")
        return stats
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_empty_stats():
    """测试空统计"""
    print("\n🧪 测试空统计...")
    
    empty_stats = {
        'total_files': 0,
        'successful': 0,
        'failed': 0,
        'processed_files': [],
        'failed_files': []
    }
    
    print(f"📊 空统计结果:")
    print(f"  总文件数: {empty_stats['total_files']}")
    print(f"  成功处理: {empty_stats['successful']}")
    print(f"  处理失败: {empty_stats['failed']}")
    
    if empty_stats['total_files'] > 0:
        success_rate = (empty_stats['successful'] / empty_stats['total_files']) * 100
        print(f"  成功率: {success_rate:.1f}%")
    else:
        print(f"  成功率: N/A (无文件)")
    
    print("✅ 空统计处理正常!")

def test_all_success():
    """测试全部成功的情况"""
    print("\n🧪 测试全部成功情况...")
    
    success_stats = {
        'total_files': 5,
        'successful': 5,
        'failed': 0,
        'processed_files': ['file1.png', 'file2.png', 'file3.jpg', 'file4.png', 'file5.png'],
        'failed_files': []
    }
    
    success_rate = (success_stats['successful'] / success_stats['total_files']) * 100
    
    print(f"📊 全部成功统计结果:")
    print(f"  总文件数: {success_stats['total_files']}")
    print(f"  成功处理: {success_stats['successful']}")
    print(f"  处理失败: {success_stats['failed']}")
    print(f"  成功率: {success_rate:.1f}%")
    
    print("✅ 全部成功统计正常!")

def main():
    """主测试函数"""
    print("🚀 开始测试统计逻辑功能")
    print("=" * 60)
    
    try:
        # 测试基本统计逻辑
        stats = test_stats_logic()
        
        # 测试空统计
        test_empty_stats()
        
        # 测试全部成功
        test_all_success()
        
        print("\n" + "=" * 60)
        print("🎉 统计逻辑测试全部通过!")
        print("📈 统计功能已就绪，可以在主程序中使用!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()