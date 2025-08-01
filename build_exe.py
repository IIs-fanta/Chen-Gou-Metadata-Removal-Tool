#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
陈狗元数据去除工具 - 打包脚本
使用 PyInstaller 将应用程序打包为 exe 文件
"""

import os
import sys
import subprocess
import shutil

def check_pyinstaller():
    """检查是否安装了 PyInstaller"""
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
        return True
    except ImportError:
        print("✗ PyInstaller 未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller 安装成功")
            return True
        except subprocess.CalledProcessError:
            print("✗ PyInstaller 安装失败")
            return False

def check_requirements():
    """检查并安装依赖"""
    if os.path.exists("requirements.txt"):
        print("正在安装依赖包...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✓ 依赖包安装完成")
        except subprocess.CalledProcessError:
            print("✗ 依赖包安装失败")
            return False
    return True

def build_exe():
    """构建 exe 文件"""
    print("开始构建 exe 文件...")
    
    # 检查图标文件
    icon_file = "logo.ico"
    if not os.path.exists(icon_file):
        print(f"✗ 找不到图标文件: {icon_file}")
        return False
    
    # PyInstaller 命令参数
    cmd = [
        "pyinstaller",
        "--onefile",                    # 打包为单个文件
        "--windowed",                   # 不显示控制台窗口
        f"--icon={icon_file}",          # 设置图标
        "--name=陈狗元数据去除工具",      # 设置输出文件名
        "--add-data=logo.ico;.",        # 包含图标文件
        "--add-data=window.ico;.",      # 包含窗口图标文件
        "--hidden-import=PIL._tkinter_finder",  # 隐藏导入
        "--hidden-import=piexif",       # 隐藏导入
        "main.py"                       # 主程序文件
    ]
    
    try:
        print("执行打包命令...")
        print(" ".join(cmd))
        subprocess.check_call(cmd)
        print("✓ 打包完成！")
        
        # 检查输出文件
        exe_path = os.path.join("dist", "陈狗元数据去除工具.exe")
        if os.path.exists(exe_path):
            print(f"✓ 可执行文件已生成: {exe_path}")
            return True
        else:
            print("✗ 可执行文件生成失败")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ 打包失败: {e}")
        return False

def clean_build_files():
    """清理构建文件"""
    print("清理构建文件...")
    
    dirs_to_remove = ["build", "__pycache__"]
    files_to_remove = ["陈狗元数据去除工具.spec"]
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ 已删除目录: {dir_name}")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"✓ 已删除文件: {file_name}")

def main():
    """主函数"""
    print("=" * 50)
    print("陈狗元数据去除工具 - 打包脚本")
    print("=" * 50)
    
    # 检查虚拟环境
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ 检测到虚拟环境")
    else:
        print("⚠ 警告: 未检测到虚拟环境，建议在虚拟环境中运行")
    
    # 检查依赖
    if not check_pyinstaller():
        return
    
    if not check_requirements():
        return
    
    # 构建 exe
    if build_exe():
        print("\n" + "=" * 50)
        print("🎉 打包成功！")
        print("可执行文件位置: dist/陈狗元数据去除工具.exe")
        print("=" * 50)
        
        # 询问是否清理构建文件
        try:
            choice = input("\n是否清理构建文件？(y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                clean_build_files()
        except KeyboardInterrupt:
            print("\n用户取消操作")
    else:
        print("\n" + "=" * 50)
        print("❌ 打包失败！")
        print("=" * 50)

if __name__ == "__main__":
    main() 