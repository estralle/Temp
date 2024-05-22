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
            
            predictions = self.model.predict(features_scaled)

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
            range_ = np.ptp(data_vector)
            features = np.array([[variance, range_]])
            features_scaled = self.scaler.transform(features)
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

