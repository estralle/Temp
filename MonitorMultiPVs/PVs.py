from epics import PV

class PVs:
    def __init__(self, name):
        self.name = name
        self.channel = PV(self.name)
        self.value = None

    def get(self):
        # 从EPICS中获取数值
        return self.channel.get()

    def put(self, value):
        self.channel.put(value)

       
