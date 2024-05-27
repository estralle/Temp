from DataCollector import DataCollector 
from ModelEvaluator import ModelEvaluator
from Monitor import Monitor
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import queue
from threading import Thread
import threading 
import json 
import os
from time import sleep


# 设置环境变量
os.environ["EPICS_CA_ADDR_LIST"] = "10.1.236.84 10.1.44.232 "
os.environ["EPICS_CA_AUTO_ADDR_LIST"] = "NO"  # 如果需要，也可以设置其他相关的环境变量


def main():
    config_path = '/home/pengna/Workspace/General_info/scripts/Temp/MonitorMultiPVs/PS_config.json'
    #lock=threading.Lock()  
    monitor_manager = Monitor(config_path)
    executor = ThreadPoolExecutor(max_workers=300)

    # 启动初始配置中的所有监控
    initial_variables = monitor_manager.config.get('variables_to_monitor', [])
    futures = {}
    for variable in initial_variables:
        print(f"Submitting monitoring task for {variable}")
        futures[variable] = executor.submit(
            monitor_manager.variable_monitoring_routine, variable, data_vector_length=360)

    # 保持主线程运行
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        executor.shutdown(wait=True)

if __name__ == "__main__":
    main()