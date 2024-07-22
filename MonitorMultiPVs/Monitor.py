import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
from DataCollector import DataCollector
from ModelEvaluator import ModelEvaluator
from time import sleep, strftime, localtime, time
from sklearn.cluster import KMeans
from epics import caget, caput, PV, ca
import pv_channel
import threading
from threading import Lock  # 添加这个导入

class Monitor:
    def __init__(self, config_path, print_lock, context):
        self.config_path = config_path
        self.print_lock = print_lock
        self.context = context
        self.config = {
            'variables_to_monitor': [],
            'models_and_scalers': {},
            'PVname': {},
            'Outputname': {},
            'Freq': {}
        }
        self.variable_data = {}
        self.last_config_check_time = datetime.min
        self.data_collector = DataCollector()
        self.model_evaluators = {}
        self.data_lock = threading.Lock()  # 添加这个属性
        print("config start:", strftime("%Y-%m-%d %H:%M:%S", localtime()))
        self.load_config()
        print("config finished:", strftime("%Y-%m-%d %H:%M:%S", localtime()))
        self.initialize_models_and_scalers()
        self.initialize_model_evaluators()
        self.init_channel()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                self.config = json.load(file)
            for variable in self.config['variables_to_monitor']:
                self.variable_data[variable] = {
                    'data_vector': np.zeros(360),
                    'time_vector': [],
                    'results_df': pd.DataFrame(columns=['Time', 'Anomaly']),
                    'last_save_time': datetime.min
                }
            return self.config
        except FileNotFoundError:
            print("Config file not found. Please check the path.")
        except json.JSONDecodeError:
            print("Error parsing the config file. Please check the file format.")

    def initialize_models_and_scalers(self):
        """直接使用配置中的模型和缩放器对象，不需要加载。"""
        for k, v in self.config['models_and_scalers'].items():
            model_path = v[0] if isinstance(v[0], str) else None
            scaler_path = v[1] if isinstance(v[1], str) else None

            model = joblib.load(model_path) if model_path else v[0]
            scaler = joblib.load(scaler_path) if scaler_path else v[1]

            self.config['models_and_scalers'][k] = (model, scaler)

    def initialize_model_evaluators(self):
        for variable_name, (model, scaler) in self.config['models_and_scalers'].items():
            self.model_evaluators[variable_name] = ModelEvaluator(model, scaler, self.print_lock, self.context)

    def init_channel(self):
        self.input_channel = pv_channel.PvChannel(self.print_lock, self.context)
        self.output_channel = pv_channel.PvChannel(self.print_lock, self.context)
        self.input_channel_old = {}
        self.output_channel_old = {}
        self.push_pvs()

    def push_pvs(self):
        self.input_channel_old = self.input_channel.channelDict.copy()
        self.output_channel_old = self.output_channel.channelDict.copy()
        self.push_channels(self.input_channel, self.input_channel_old, "PVname")
        self.push_channels(self.output_channel, self.output_channel_old, "Outputname")

    def push_channels(self, channel, channel_old, define_name):
        for variable_name in list(channel_old):
            if variable_name not in self.config["variables_to_monitor"]:
                channel.remove(variable_name)
        
        pv_list = [(variable_name, self.config[define_name][variable_name]) 
                   for variable_name in self.config["variables_to_monitor"]]
        
        self.create_pv_channels(channel, pv_list)

    def create_pv_channels(self, pv_channel, pv_list):
        threads = []
        for variable_name, pv_name in pv_list:
            thread = threading.Thread(target=pv_channel.push, args=(variable_name, pv_name))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def variable_monitoring_routine(self, variable_name, data_vector_length=360):
        # 在每个线程中附加到主线程的上下文
        ca.attach_context(self.context)

        print(f"Monitoring started for {variable_name}.")
        try:
            variable_info = self.variable_data[variable_name]
            print(f"Monitoring {variable_name}")
            variable_info['data_vector'] = np.zeros(data_vector_length)  # 初始化数据向量
            variable_info['time_vector'] = []  # 时间向量
            config = self.config
            inputpv = self.input_channel.channelDict[variable_name]
            outputpv = self.output_channel.channelDict[variable_name]
            Freq_Init = config['Freq']['initial']
            Freq_Collect = config['Freq']['collect']
            variable_info['data_vector'], variable_info['time_vector'] = self.data_collector.collect_initial_data_online(CheckPV=inputpv, vector_length=data_vector_length, Freq=Freq_Init)
            print(variable_name + " Initial data collection complete.")
            max_value = np.mean(variable_info['data_vector']) +0.5
            min_value = np.mean(variable_info['data_vector']) -0.5
            variable_info['data_vector'] = (variable_info['data_vector'] - min_value) / (max_value - min_value)
            while True:
                with self.data_lock:
                    #print(f"Updating data for {variable_name}")
                    self.data_collector.update_data(variable_info['data_vector'], variable_info['time_vector'], max_value, min_value, CheckPV=inputpv, Freq=Freq_Collect)
                    #print(f"Data updated for {variable_name}")
                    model_evaluator = self.model_evaluators[variable_name]
                    #print(f"Evaluating anomalies for {variable_name}")
                    anomalies = model_evaluator.judge_anomalies(variable_info['data_vector'])
                    #print(f"Anomalies tested by model for {variable_name}: {anomalies}")
                    outputpv.put(anomalies)
                    #print(f"Anomalies put to output PV for {variable_name}")
                sleep(Freq_Collect)  # 更新频率
        except Exception as e:
            print(f"Error while monitoring {variable_name}: {e}")
        print(f"Monitoring completed for {variable_name}.")

