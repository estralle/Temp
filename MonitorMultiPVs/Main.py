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
import json 

def main():
    config_path = '/home/pengn/Workspace/General_info/config/config.json'
    monitor_manager = Monitor(config_path)
    executor = ThreadPoolExecutor(max_workers=100)
    #executor = ThreadPoolExecutor()

    # 启动初始配置中的所有监控
    initial_variables = monitor_manager.config.get('variables_to_monitor', [])
    futures = {}
    for variable in initial_variables:
        futures[variable] = executor.submit(
            monitor_manager.variable_monitoring_routine, variable, data_vector_length=360)
        #futures[variable] = future

if __name__ == "__main__":
    main()
