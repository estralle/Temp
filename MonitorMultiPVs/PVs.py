from epics import PV
from epics.ca import ChannelAccessException

class PVs:
    def __init__(self, name):
        self.name = name
        self.channel = PV(self.name)
        self.value = None

    def get(self, timeout=1.0):
        try:
            # 从EPICS中获取数值，设置超时时间
            return self.channel.get(timeout=timeout)
        except CAException as e:
            print(f"Error getting value from PV {self.name}: {e}")
            return None

  #  def put(self, value):
  #      self.channel.put(value)
    def put(self, value, wait=True, timeout=1.0):
        try:
            # 尝试将值写入 PV，设置等待时间和超时时间
            success = self.channel.put(value, wait=wait, timeout=timeout)
            if success:
                print(f"Successfully put value {value} to PV {self.name}")
            else:
                print(f"Failed to put value {value} to PV {self.name}")
            return success
        except CAException as e:
            print(f"Error putting value to PV {self.name}: {e}")
            return False


       
