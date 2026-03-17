"""
Test script to check current directory and file paths
"""
import os

print("当前工作目录:", os.getcwd())
print("脚本所在目录:", os.path.dirname(os.path.abspath(__file__)))
print("路书脚本路径:", os.path.abspath(".roadbook\jimeng-ai-video-crawl\scripts\script.py"))
print("路书脚本是否存在:", os.path.exists(".roadbook\jimeng-ai-video-crawl\scripts\script.py"))
