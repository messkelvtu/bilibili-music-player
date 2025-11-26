#!/bin/bash

echo "==============================="
echo "    B站音乐播放器启动器"
echo "==============================="
echo

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到Python，请先安装Python 3.7+"
    echo "在Ubuntu/Debian上: sudo apt install python3 python3-pip"
    echo "在Mac上: brew install python"
    exit 1
fi

echo "✅ Python已安装"
echo

echo "正在安装依赖包..."
pip3 install -r requirements.txt

echo
echo "正在启动音乐播放器..."
python3 music_player.py
