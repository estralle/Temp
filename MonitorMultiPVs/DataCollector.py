import numpy as np
import time
from time import strftime, localtime, sleep
from epics import caget
from PVs import PVs

class DataCollector:
    def __init__(self):
        pass

    def collect_initial_data_online(self, PVname, vector_length, Freq):
        """
        Collect the initial data points for the given PVname.
        """
        data_vector, time_vector = self._collect_data(PVname, vector_length, Freq, initial=True)
        return data_vector, time_vector

    def update_data(self, data_vector, time_vector, max_value, min_value, PVname, Freq):
        """
        Update the data vector with a new data point.
        """
        updated_data_vector, updated_time_vector = self._collect_data(PVname, 1, Freq, initial=False, 
                                                                      data_vector=data_vector, time_vector=time_vector, 
                                                                      max_value=max_value, min_value=min_value)
        return updated_data_vector, updated_time_vector

    def _collect_data(self, PVname, vector_length, Freq, initial=True, data_vector=None, time_vector=None, max_value=None, min_value=None):
        """
        Private method to collect data. It supports both initial data collection and data update.
        """
        pvname = PVname.name
        if initial:
            data_vector = np.zeros(vector_length)  # Initialize data vector for initial collection
            time_vector = []  # Initialize time vector

        next_target_time = self._get_next_target_time(Freq)        
        for i in range(vector_length):
            self._wait_until(next_target_time)
            current_time = strftime("%Y-%m-%d %H:%M:%S", localtime())
            try:
                data_point = PVname.get()
                if not initial:
                    data_point = (data_point - min_value) / (max_value - min_value)
                    data_vector = np.roll(data_vector, -1)
                    data_vector[-1] = data_point
                    time_vector = time_vector[1:] + [current_time]
                else:
                    data_vector[i] = data_point
                    time_vector.append(current_time)
                #print(f"PVname:{pvname};Time: {current_time}, Data: {data_point}")  # For demonstration purposes
            except Exception as e:
                print(f"Error collecting data: {e}")
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


