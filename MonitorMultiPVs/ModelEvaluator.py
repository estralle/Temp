import numpy as np
from epics import ca
import threading
from threading import Lock  # 添加这个导入

class ModelEvaluator:
    def __init__(self, model, scaler, print_lock, context):
        self.model = model
        self.scaler = scaler
        self.print_lock = print_lock
        self.context = context
        self.local = threading.local()  # 使用线程本地存储

    def judge_anomalies(self, data_vector):
        """
        Judge anomalies using the K-means clustering model.
        """
        # 在每个线程中附加到主线程的上下文
        ca.attach_context(self.context)
        # 确保每个线程都有独立的模型和缩放器实例
        if not hasattr(self.local, 'model'):
            self.local.model = self.model
            self.local.scaler = self.scaler
        try:
            features_scaled = self.calculate_features(data_vector)
            if features_scaled is None:
                print("Error: Feature scaling failed.")
                return None
            
            predictions = self.local.model.predict(features_scaled)
            #print(f"Prediction is {predictions}")
            # 判断预测结果是否属于最大的簇（正常），否则为异常
            max_cluster = self._find_max_cluster()
            return 0 if predictions == max_cluster else 1
        except Exception as e:
            print(f"Error judging anomalies: {e}")
            return None

    def calculate_features(self, data_vector):
        """
        Calculate features from the data vector.
        """
        try:
            variance = np.var(data_vector)
            range_ = np.max(data_vector) - np.min(data_vector)  # 最大值 - 最小值
            features = np.array([[range_, variance]])
            #print(f"Before scaled features {features}")
            features_scaled = self.local.scaler.transform(features)
            #print(f"After scaled features {features_scaled}")
            return features_scaled
        except Exception as e:
            print(f"Error calculating features: {e}")
            return None

    def _find_max_cluster(self):
        """
        Find the index of the largest cluster.
        """
        unique, counts = np.unique(self.local.model.labels_, return_counts=True)
        max_cluster = unique[np.argmax(counts)]
        return max_cluster