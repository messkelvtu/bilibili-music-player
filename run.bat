
### 6. `run.bat`（Windows启动脚本）
```batch
@echo off
chcp 65001 >nul
title B站音乐播放器

echo ===============================
echo      B站音乐播放器启动器
echo ===============================
echo.

echo 正在检查Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Python，请先安装Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python已安装
echo.

echo 正在安装依赖包...
pip install -r requirements.txt

echo.
echo 正在启动音乐播放器...
python music_player.py

pause
