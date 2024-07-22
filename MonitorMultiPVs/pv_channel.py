import epics
import time
import threading

class PvChannel:
    def __init__(self, print_lock, context) -> None:
        self.channelDict = {}
        self.lock = threading.Lock()  # 用于保护 channelDict 的线程锁
        self.print_lock = print_lock  # 用于保护输出的线程锁
        self.context = context  # 用于保存上下文信息

    def push(self, variable_name, pv_name):

        epics.ca.attach_context(self.context)  # 附加上下文信息，用于区分不同 PV 连接

        # 创建 PV 对象
        pv_name_channel = epics.PV(pv_name)
        
        # 等待 PV 连接
        while not pv_name_channel.wait_for_connection(timeout=5.0):
            with self.print_lock:  # 使用线程锁保护输出
                print(f'Connecting to PV {pv_name}...')
            time.sleep(0.5)
        
        if pv_name_channel.connected:
            with self.print_lock:  # 使用线程锁保护输出
                print(f'Connected to PV {pv_name}')
            # print(f'Connected to PV {pv_name}')
            with self.lock:  # 使用线程锁保护对 channelDict 的访问
                self.channelDict[variable_name] = pv_name_channel
        else:
            with self.print_lock:  # 使用线程锁保护输出
                print(f'Failed to connect to PV {pv_name} after multiple attempts')

    def remove(self, variable_name):
        with self.lock:  # 使用线程锁保护对 channelDict 的访问
            if self.exist(variable_name):
                self.channelDict.pop(variable_name)

    def exist(self, variable_name):
        with self.lock:  # 使用线程锁保护对 channelDict 的访问
            return variable_name in self.channelDict

    def get(self, variable_name):
        with self.lock:  # 使用线程锁保护对 channelDict 的访问
            if self.exist(variable_name):
                return self.channelDict[variable_name].get()
            else:
                with self.print_lock:  # 使用线程锁保护输出
                    print(f'{__file__}: PV {variable_name} does not exist! Please check out!')

    def put(self, variable_name, value):
        with self.lock:  # 使用线程锁保护对 channelDict 的访问
            if self.exist(variable_name):
                self.channelDict[variable_name].put(value)
            else:
                with self.print_lock:  # 使用线程锁保护输出
                    print(f'{__file__}: PV {variable_name} does not exist! Please check out!')