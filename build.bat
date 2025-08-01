@echo off
chcp 65001 >nul
echo ================================================
echo 陈狗元数据去除工具 - 自动打包脚本
echo ================================================
echo.

REM 检查是否在虚拟环境中
python -c "import sys; print('虚拟环境检测:', hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))"

echo.
echo 开始打包...
echo.

REM 运行打包脚本
python build_exe.py

echo.
echo 按任意键退出...
pause >nul 