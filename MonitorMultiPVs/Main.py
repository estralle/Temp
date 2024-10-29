# -*- coding: utf-8 -*-
from DataCollector import DataCollector 
from ModelEvaluator import ModelEvaluator
from Monitor import Monitor
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import time
import queue
from threading import Thread
import json 
import os
from time import sleep
from epics import ca
import threading


# 设置环境变量
os.environ["EPICS_CA_ADDR_LIST"] = "10.1.236.84 10.1.44.223 "
os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"  # 如果需要，也可以设置其他相关的环境变量
#os.environ["EPICS_CA_SERVER_PORT"] = "5066"

def main():
    
    config_path = '/home/pengna/Workspace/General_info/scripts/Temp/MonitorMultiPVs/T_config.json'
    # 初始化 EPICS 上下文
    ca.initialize_libca()
    context = ca.current_context()
    
    # 创建全局打印锁
    print_lock = threading.Lock()
    
    # 创建 Monitor 实例
    monitor_manager = Monitor(config_path, print_lock, context)
    # 创建线程池
    executor = ThreadPoolExecutor(max_workers=300)
    
    #启动初始配置中的所有监控
    initial_variables = monitor_manager.config.get('variables_to_monitor', [])
    futures = {}
    for variable in initial_variables:
       futures[variable] = executor.submit(
           monitor_manager.variable_monitoring_routine, variable, data_vector_length=360)
    
    #等待所有任务完成
    for future in futures.values():
       future.result()
       
    ca.finalize_libca()
    
if __name__ == "__main__":
    main()