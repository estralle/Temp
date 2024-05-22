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
from epics import caget, caput, PV
from PVs import PVs

class Monitor:
    def __init__(self, config_path):
        self.config_path = config_path
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
        self.load_config()
        self.initialize_models_and_scalers()
        self.initialize_model_evaluators()
        self.inputPV = {}
        self.outputPV = {}
        self.initialize_PVs()

    def load_config(self):
        try:
            with open(self.config_path, 'r') as file:
                self.config = json.load(file)
            print("Config loaded:", self.config)
            for variable in self.config['variables_to_monitor']:
                self.variable_data[variable] = {
                    'data_vector': np.zeros(360),
                    'time_vector': [],
                    'results_df': pd.DataFrame(columns=['Time', 'Anomaly']),
                    'last_save_time': datetime.min
                }
            return self.config  # 确保返回新的配置 
        except FileNotFoundError:
            print("Config file not found. Please check the path.")
        except json.JSONDecodeError:
            print("Error parsing the config file. Please check the file format.")

    def initialize_model_evaluators(self):
        for variable_name, (model, scaler) in self.config['models_and_scalers'].items():
            self.model_evaluators[variable_name] = ModelEvaluator(model, scaler)

    def initialize_models_and_scalers(self):
        """直接使用配置中的模型和缩放器对象，不需要加载。"""
        for k, v in self.config['models_and_scalers'].items():
            model = v[0] if isinstance(v[0], KMeans) else joblib.load(v[0])
            scaler = v[1] if hasattr(v[1], 'transform') else joblib.load(v[1])
            self.config['models_and_scalers'][k] = (model, scaler)

    def initialize_PVs(self):
        for variable_name, inputname in self.config['PVname'].items():
            self.inputPV[variable_name] = PVs(inputname)
        for variable_name, outputname in self.config['Outputname'].items():
            self.outputPV[variable_name] = PVs(outputname)

    def variable_monitoring_routine(self, variable_name, data_vector_length=360):
        """
        封装的预测逻辑，用于监控特定变量。
        """
        print(f"Monitoring started for {variable_name}.")
        try:
            variable_info = self.variable_data[variable_name]
            print(f"Monitoring {variable_name}")
            variable_info['data_vector'] = np.zeros(data_vector_length)  # 初始化数据向量
            variable_info['time_vector'] = []  # 时间向量
            config = self.config
            #use_saved_data = config['Use_saved_data'][variable_name]
            model = config['models_and_scalers'][variable_name][0]
            scaler = config['models_and_scalers'][variable_name][1]
            pvname = self.inputPV[variable_name]
            outputname = self.outputPV[variable_name]
            Freq_Init = config['Freq']['initial']
            Freq_Collect = config['Freq']['collect']
            #print(f"Before initial Monitoring {variable_name}")
            self.data_collector.collect_initial_data_online(PVname=pvname, vector_length=data_vector_length, Freq=Freq_Init)
            print(variable_name + " Initial data collection complete.")
            # 计算最大值和平均值
            max_value = np.mean(variable_info['data_vector']) + 0.5
            min_value = np.mean(variable_info['data_vector']) - 0.5
            variable_info['data_vector'] = (variable_info['data_vector'] - min_value) / (max_value - min_value)
            while True:
                self.data_collector.update_data(variable_info['data_vector'], variable_info['time_vector'], max_value, min_value, PVname=pvname, Freq=Freq_Collect)
                model_evaluator = self.model_evaluators[variable_name]
                anomalies = model_evaluator.judge_anomalies(variable_info['data_vector'])
                outputname.put(anomalies)
                sleep(Freq_Collect)  # 更新频率
        except Exception as e:
            print(f"Error while monitoring {variable_name}: {e}")
        print(f"Monitoring completed for {variable_name}.")
       