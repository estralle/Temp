import numpy as np

class ModelEvaluator:
    def __init__(self, model, scaler):
        self.model = model
        self.scaler = scaler

    def judge_anomalies(self, data_vector):
        """
        Judge anomalies using the K-means clustering model.
        """
        try:
            features_scaled = self.calculate_features(data_vector)
            if features_scaled is None:
                print("Error: Feature scaling failed.")
                return None
            print(f"Features scaled for prediction: {features_scaled}") 
            predictions = self.model.predict(features_scaled)
            print(f"Prediction is {predictions}")

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
           # variance = np.var(data_vector)
           # range_ = np.ptp(data_vector)
            #features = np.array([[variance, range_]])
            # 提取特征 (最大值 - 最小值) 和 方差
            #features = np.zeros((data_vector.shape[0], 2))
            #features[:, 0] = np.max(data_vector, axis=1) - np.min(data_vector, axis=1)  
            #features[:, 1] = np.var(data_vector, axis=1)  # 方差
            
            # 确保 data_vector 是一个一维数组
            if data_vector.ndim != 1:
                raise ValueError("data_vector should be a one-dimensional array.")
            
            # 提取特征 (最大值 - 最小值) 和 方差
            range_ = np.max(data_vector) - np.min(data_vector)  # 最大值 - 最小值
            variance = np.var(data_vector)  # 方差
            features = np.array([[range_, variance]])  # 创建一个形状为 (1, 2) 的特征数组
            print(f"Before sacled features {features}")
            features_scaled = self.scaler.transform(features)
            print(f"After sacled features {features_scaled}")
            return features_scaled
        except Exception as e:
            print(f"Error calculating features: {e}")
            return None

    def _find_max_cluster(self):
        """
        Find the index of the largest cluster.
        """
        unique, counts = np.unique(self.model.labels_, return_counts=True)
        max_cluster = unique[np.argmax(counts)]
        return max_cluster

