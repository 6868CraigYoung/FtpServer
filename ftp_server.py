# 这是一个启动文件，整个 ftp_server 的入口

import sys
import os
from core import main   # 在环境变量中就可以找到 core 文件夹了

base_path = os.path.dirname(os.path.dirname(__file__))  # 获得本文件的上上级目录，也就是ftp_server目录
sys.path.append(base_path)  # 将 base_path 添加到临时的环境变量
print(base_path)

main.test().controllink()  # 用文件名加类名运行
