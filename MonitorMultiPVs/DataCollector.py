import numpy as np
import time
from time import strftime, localtime, sleep
from epics import caget

class DataCollector:
    def __init__(self):
        pass

    def collect_initial_data_online(self, CheckPV, vector_length, Freq):
        """
        Collect the initial data points for the given CheckPV.
        """
        data_vector, time_vector = self._collect_data(CheckPV, vector_length, Freq, initial=True)
        return data_vector, time_vector

    def update_data(self, data_vector, time_vector, max_value, min_value, CheckPV, Freq):
        """
        Update the data vector with a new data point.
        """
        updated_data_vector, updated_time_vector = self._collect_data(CheckPV, 1, Freq, initial=False, 
                                                                      data_vector=data_vector, time_vector=time_vector, 
                                                                      max_value=max_value, min_value=min_value)
        return updated_data_vector, updated_time_vector

    def _collect_data(self, CheckPV, vector_length, Freq, initial=True, data_vector=None, time_vector=None, max_value=None, min_value=None):
        if initial:
            data_vector = np.zeros(vector_length)  # Initialize data vector for initial collection
            time_vector = []  # Initialize time vector

        next_target_time = self._get_next_target_time(Freq)
        for i in range(vector_length):
            self._wait_until(next_target_time)
            current_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
            max_retries = 5
            retries = 0
            data_point = None

            while retries < max_retries:
                try:
                    data_point = CheckPV.get()
                    if data_point is not None:
                        break
                    else:
                        print(f"Data point is None, retrying... ({retries + 1}/{max_retries})")
                except Exception as e:
                    print(f"Error getting data point: {e}")

                CheckPV.reconnect()
                CheckPV.wait_for_connection()
                sleep(1)  # 添加延迟
                retries += 1

            if data_point is None:
                print("Failed to get valid data point after multiple retries")
                continue  # 跳过这个数据点，继续下一个

            try:
                if not initial:
                    data_point = (data_point - min_value) / (max_value - min_value)
                    data_vector = np.roll(data_vector, -1)
                    data_vector[-1] = data_point
                    time_vector = time_vector[1:] + [current_time]
                else:
                    data_vector[i] = data_point
                    time_vector.append(current_time)
                print(f"CheckPV:{CheckPV}; Time: {current_time}, Data: {data_point}")  # For demonstration purposes
            except Exception as e:
                print(f"Error processing data: {e}")

            next_target_time += Freq

        return data_vector, time_vector


    def _get_next_target_time(self, Freq):
        """
        Calculate the next target time point.
        """
        current_time = time.time()
        current_seconds = time.localtime(current_time).tm_sec
        seconds_to_wait = Freq - (current_seconds % Freq)
        if seconds_to_wait == Freq:
            seconds_to_wait = 0
        next_target_time = current_time + seconds_to_wait
        return next_target_time

    def _wait_until(self, target_time):
        """
        Wait until the target time.
        """
        while time.time() < target_time:
            sleep(0.01)