# app.py
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading
import time
import epics
import json
import sys
sys.path.append('/home/pengna/Workspace/General_info/scripts/Temp/MonitorMultiPVs/')
from Monitor import Monitor

app = Flask(__name__)
socketio = SocketIO(app)

# 全局变量
output_pv_data = {}
print_lock = threading.Lock()

# 初始化 EPICS 上下文
epics.ca.initialize_libca()
context = epics.ca.current_context()

# 创建 Monitor 实例
config_path = '/home/control/Workspace/GeneralInfo/scripts/Temp/MonitorMultiPVs/T_config.json'
monitor_manager = Monitor(config_path, print_lock, context)

# 定义要监控的PV字典
pvs_to_monitor = {
    "LINAC_KlyT2": "LINAC:KlyT2::Alarm:Tmp",
    "LINAC_KlyT1": "LINAC:KlyT1::Alarm:Tmp",
    "LINAC_DTL2BackT": "LINAC:DTL2BackT::Alarm:Tmp",
    "LINAC_RFRefWallT1": "LINAC:RFRefWallT1::Alarm:Tmp",
    "LINAC_DbnchT1": "LINAC:DbnchT1::Alarm:Tmp",
    "LINAC_RFRefT1": "LINAC:RFRefT1::Alarm:Tmp",
    "LINAC_DTL1InT": "LINAC:DTL1InT::Alarm:Tmp",
    "LINAC_DTL3BackT": "LINAC:DTL3BackT::Alarm:Tmp",
    "LINAC_RFQWallInT": "LINAC:RFQWallInT::Alarm:Tmp",
    "LINAC_RFQWallBackT": "LINAC:RFQWallBackT::Alarm:Tmp",
    "LINAC_DTL2InT": "LINAC:DTL2InT::Alarm:Tmp",
    "LINAC_RFQVaneInT": "LINAC:RFQVaneInT::Alarm:Tmp",
    "LINAC_DTL4InT": "LINAC:DTL4InT::Alarm:Tmp",
    "LINAC_DTL1BackT": "LINAC:DTL1BackT::Alarm:Tmp",
    "LINAC_DTL3InT": "LINAC:DTL3InT::Alarm:Tmp",
    "LINAC_BnchBackT": "LINAC:BnchBackT::Alarm:Tmp",
    "LINAC_BnchT1": "LINAC:BnchT1::Alarm:Tmp",
    "LINAC_DTL4BackT": "LINAC:DTL4BackT::Alarm:Tmp",
    "RCS_RFCavBackT1": "RCS:RFCavBackT1::Alarm:Tmp",
    "RCS_BCPSBackT1": "RCS:BCPSBackT1::Alarm:Tmp",
    "RCS_IEPPST1": "RCS:IEPPST1::Alarm:Tmp",
    "RCS_MagInT1": "RCS:MagInT1::Alarm:Tmp",
    "RCS_BCPSInT1": "RCS:BCPSInT1::Alarm:Tmp",
    "RCS_RFPSInT1": "RCS:RFPSInT1::Alarm:Tmp",
    "RCS_MagBackT1": "RCS:MagBackT1::Alarm:Tmp",
    "RCS_RFCavInT1": "RCS:RFCavInT1::Alarm:Tmp",
    "LRBT_MagInT1": "LRBT:MagInT1::Alarm:Tmp",
    "LRBT_MagBackT1": "LRBT:MagBackT1::Alarm:Tmp",
    "RTBT_MagInT1": "RTBT:MagInT1::Alarm:Tmp",
    "RTBT_MagBackT1": "RTBT:MagBackT1::Alarm:Tmp"
}

def monitor_pv(variable_name, pv_name):
    epics.ca.attach_context(context)
    while True:
        value = epics.caget(pv_name)
        with print_lock:
            output_pv_data[variable_name] = value
        socketio.emit('update_data', {'variable_name': variable_name, 'value': value})
        time.sleep(1)  # 更新频率

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    with print_lock:
        data = output_pv_data.copy()
    return jsonify(data)

@socketio.on('connect')
def handle_connect():
    with print_lock:
        for variable_name, value in output_pv_data.items():
            emit('update_data', {'variable_name': variable_name, 'value': value})

if __name__ == '__main__':
    for variable_name, pv_name in pvs_to_monitor.items():
        thread = threading.Thread(target=monitor_pv, args=(variable_name, pv_name))
        thread.start()
    socketio.run(app, host='0.0.0.0', port=5009)