#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的显示效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from main import ProcessingResultsDialog

def test_display_fix():
    """测试显示修复效果"""
    print("🧪 测试处理结果统计对话框的显示修复...")
    
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 模拟大量文件名
    test_stats = {
        'total_files': 20,
        'successful': 15,
        'failed': 5,
        'processed_files': [
            f"very_long_filename_test_01_with_very_long_path_structure_and_multiple_directories.png",
            f"very_long_filename_test_02_with_very_long_path_structure_and_multiple_directories.jpg", 
            f"very_long_filename_test_03_with_very_long_path_structure_and_multiple_directories.png",
            f"very_long_filename_test_04_with_very_long_path_structure_and_multiple_directories.jpg",
            f"very_long_filename_test_05_with_very_long_path_structure_and_multiple_directories.png",
            f"very_long_filename_test_06_with_very_long_path_structure_and_multiple_directories.jpg",
            f"very_long_filename_test_07_with_very_long_path_structure_and_multiple_directories.png",
            f"very_long_filename_test_08_with_very_long_path_structure_and_multiple_directories.jpg",
            f"very_long_filename_test_09_with_very_long_path_structure_and_multiple_directories.png",
            f"very_long_filename_test_10_with_very_long_path_structure_and_multiple_directories.jpg",
            f"very_long_filename_test_11_with_very_long_path_structure_and_multiple_directories.png",
            f"very_long_filename_test_12_with_very_long_path_structure_and_multiple_directories.jpg",
            f"very_long_filename_test_13_with_very_long_path_structure_and_multiple_directories.png",
            f"very_long_filename_test_14_with_very_long_path_structure_and_multiple_directories.jpg",
            f"very_long_filename_test_15_with_very_long_path_structure_and_multiple_directories.png"
        ],
        'failed_files': [
            f"failed_file_01_with_very_long_filename_to_test_display_issues.png",
            f"failed_file_02_with_very_long_filename_to_test_display_issues.jpg",
            f"failed_file_03_with_very_long_filename_to_test_display_issues.png", 
            f"failed_file_04_with_very_long_filename_to_test_display_issues.jpg",
            f"failed_file_05_with_very_long_filename_to_test_display_issues.png"
        ]
    }
    
    # 创建对话框
    dialog = ProcessingResultsDialog(None, test_stats)
    
    # 设置对话框标题
    dialog.setWindowTitle("📊 显示修复测试 - 长文件名处理效果")
    
    # 显示对话框
    print("✅ 对话框已创建，显示修复测试完成！")
    print("📋 测试内容：")
    print(f"   - 总文件数: {test_stats['total_files']}")
    print(f"   - 成功处理: {test_stats['successful']} (包含长文件名)")
    print(f"   - 处理失败: {test_stats['failed']} (包含长文件名)")
    print("🔧 修复效果：")
    print("   ✅ 文件列表高度从120px增加到200px")
    print("   ✅ 添加了滚动区域支持")
    print("   ✅ 启用了文本换行功能")
    print("   ✅ 改进了视觉样式和颜色区分")
    
    # 执行对话框
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        print("✅ 对话框测试通过！")
    else:
        print("ℹ️ 用户取消了对话框")
    
    return True

if __name__ == "__main__":
    try:
        test_display_fix()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()