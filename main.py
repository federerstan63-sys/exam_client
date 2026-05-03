# -*- coding: utf-8 -*-
"""
main.py — 程序入口
初始化数据库、配置日志，然后启动主窗口。
"""

import logging  # logging 模块：Python 标准日志库，用于记录程序运行信息
import os
import sys

import config                          # 导入全局配置常量（路径、颜色、字体等）
from database.db_manager import DBManager  # 导入数据库管理器（负责建表和增删查改）


def setup_logging() -> None:
    """
    配置日志系统：同时将日志输出到文件和控制台。

    logging.basicConfig 是一次性全局配置，程序启动时调用一次即可。
    之后任何模块调用 logging.getLogger(__name__) 都会继承这里的配置。

    日志格式说明：
      %(asctime)s   — 时间戳，如 2024-01-01 12:00:00,123
      %(levelname)s — 日志级别，如 INFO / WARNING / ERROR
      %(name)s      — 记录器名称（通常是模块名 __name__）
      %(message)s   — 日志正文
    """
    logging.basicConfig(
        level=logging.INFO,   # 只记录 INFO 及以上级别（INFO/WARNING/ERROR/CRITICAL）
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            # FileHandler：将日志写入文件，encoding='utf-8' 防止中文乱码
            logging.FileHandler(config.LOG_PATH, encoding='utf-8'),
            # StreamHandler：将日志输出到控制台（sys.stdout = 标准输出）
            logging.StreamHandler(sys.stdout),
        ]
    )


def main() -> None:
    """
    程序主函数，按顺序完成三件事：
      1. 配置日志
      2. 初始化数据库（建表、写入默认设置）
      3. 启动 tkinter GUI 主循环
    """
    setup_logging()

    # logging.getLogger(__name__)：
    #   __name__ 在这里等于 '__main__'（直接运行时）
    #   获取一个以模块名命名的记录器，方便在日志中定位来源
    logger = logging.getLogger(__name__)
    logger.info('程序启动，版本 %s', config.APP_VERSION)
    # logger.info 的第二个参数是格式化占位符，%s 会被替换为 config.APP_VERSION
    # 这种写法比 f-string 更高效：只有真正需要输出时才格式化字符串

    # 初始化数据库（建表、插入默认设置）
    # DBManager.initialize 是类方法，只需调用一次，内部使用单例模式
    DBManager.initialize(config.DB_PATH)
    logger.info('数据库初始化完成：%s', config.DB_PATH)

    # 延迟导入 App，避免在数据库初始化前就触发 UI 相关代码
    from ui.app import App
    app = App()   # 创建主窗口实例（继承自 tk.Tk，是整个 GUI 的根窗口）
    app.mainloop()
    # mainloop()：启动 tkinter 事件循环
    #   程序会在这里"阻塞"，持续监听鼠标点击、键盘输入等事件
    #   直到用户关闭窗口，mainloop() 才会返回

    logger.info('程序正常退出')


if __name__ == '__main__':
    # 只有直接运行 main.py 时才执行 main()
    # 如果被其他模块 import，则不执行（防止意外启动程序）
    main()