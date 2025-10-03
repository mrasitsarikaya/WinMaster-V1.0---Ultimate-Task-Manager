import sys
import os
import psutil
import webbrowser
import winreg
import GPUtil
import platform
import subprocess
import shutil
from PyQt6 import QtWidgets, QtCore
import pyqtgraph as pg

pg.setConfigOption('background', 'k')
pg.setConfigOption('foreground', 'w')

class ResourceMonitor(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QHBoxLayout()
        self.cpu_plot = pg.PlotWidget(title="CPU Usage (%)")
        self.ram_plot = pg.PlotWidget(title="RAM Usage (%)")
        self.disk_plot = pg.PlotWidget(title="Disk Usage (%)")
        self.net_plot = pg.PlotWidget(title="Network KB/s")
        self.gpu_plot = pg.PlotWidget(title="GPU Usage (%)")
        self.gpu_temp_plot = pg.PlotWidget(title="GPU Temp (°C)")
        self.gpu_fan_plot = pg.PlotWidget(title="GPU Fan (%)")

        for p in [self.cpu_plot,self.ram_plot,self.disk_plot,self.net_plot,self.gpu_plot,self.gpu_temp_plot,self.gpu_fan_plot]:
            p.showGrid(x=True,y=True)
            p.setYRange(0,100)

        self.cpu_data=[0]*60
        self.ram_data=[0]*60
        self.disk_data=[0]*60
        self.net_data=[0]*60
        self.gpu_data=[0]*60
        self.gpu_temp_data=[0]*60
        self.gpu_fan_data=[0]*60

        self.cpu_curve = self.cpu_plot.plot(self.cpu_data, pen=pg.mkPen('#00aaff', width=2))
        self.ram_curve = self.ram_plot.plot(self.ram_data, pen=pg.mkPen('#00ff00', width=2))
        self.disk_curve = self.disk_plot.plot(self.disk_data, pen=pg.mkPen('#ffaa00', width=2))
        self.net_curve = self.net_plot.plot(self.net_data, pen=pg.mkPen('#ff00aa', width=2))
        self.gpu_curve = self.gpu_plot.plot(self.gpu_data, pen=pg.mkPen('#00ffff', width=2))
        self.gpu_temp_curve = self.gpu_temp_plot.plot(self.gpu_temp_data, pen=pg.mkPen('#ff5500', width=2))
        self.gpu_fan_curve = self.gpu_fan_plot.plot(self.gpu_fan_data, pen=pg.mkPen('#ff00ff', width=2))

        layout.addWidget(self.cpu_plot)
        layout.addWidget(self.ram_plot)
        layout.addWidget(self.disk_plot)
        layout.addWidget(self.net_plot)
        layout.addWidget(self.gpu_plot)
        layout.addWidget(self.gpu_temp_plot)
        layout.addWidget(self.gpu_fan_plot)
        self.setLayout(layout)

        self.last_net = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_usage)
        self.timer.start(1000)

    def update_usage(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('C:\\').percent
        net_total = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
        net_speed = (net_total - self.last_net)/1024
        self.last_net = net_total
        gpu = 0
        gpu_temp = 0
        gpu_fan = 0
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_obj = gpus[0]
                gpu = gpu_obj.load*100
                gpu_temp = gpu_obj.temperature
                gpu_fan = gpu_obj.fan_speed
        except: pass

        self.cpu_data=self.cpu_data[1:]+[cpu]
        self.ram_data=self.ram_data[1:]+[ram]
        self.disk_data=self.disk_data[1:]+[disk]
        self.net_data=self.net_data[1:]+[net_speed]
        self.gpu_data=self.gpu_data[1:]+[gpu]
        self.gpu_temp_data=self.gpu_temp_data[1:]+[gpu_temp]
        self.gpu_fan_data=self.gpu_fan_data[1:]+[gpu_fan]

        self.cpu_curve.setData(self.cpu_data)
        self.ram_curve.setData(self.ram_data)
        self.disk_curve.setData(self.disk_data)
        self.net_curve.setData(self.net_data)
        self.gpu_curve.setData(self.gpu_data)
        self.gpu_temp_curve.setData(self.gpu_temp_data)
        self.gpu_fan_curve.setData(self.gpu_fan_data)

class ProcessPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Filter by name or PID...")
        self.search_bar.textChanged.connect(self.refresh)
        layout.addWidget(self.search_bar)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["PID","Name","CPU%","Memory MB","Status","Path"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)
        self.refresh()
    def refresh(self):
        filter_text = self.search_bar.text().lower()
        procs = list(psutil.process_iter(['pid','name','cpu_percent','memory_info','status','exe']))
        if filter_text:
            procs = [p for p in procs if filter_text in (p.info.get('name') or '').lower() or filter_text in str(p.info.get('pid'))]
        self.table.setRowCount(len(procs))
        for i,p in enumerate(procs):
            pid=p.info.get('pid')
            name=p.info.get('name') or ''
            cpu=p.info.get('cpu_percent') or 0.0
            mem=0
            mi=p.info.get('memory_info')
            if mi: mem=mi.rss/1024/1024
            status=p.info.get('status') or ''
            path=p.info.get('exe') or ''
            for col,val in enumerate([pid,name,cpu,mem,status,path]):
                self.table.setItem(i,col,QtWidgets.QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
    def open_menu(self,pos):
        indexes=self.table.selectedIndexes()
        if not indexes: return
        row=indexes[0].row()
        pid=int(self.table.item(row,0).text())
        name=self.table.item(row,1).text()
        menu=QtWidgets.QMenu()
        kill_action=menu.addAction("Terminate")
        search_action=menu.addAction(f"Search '{name}' on Google")
        action=menu.exec(self.table.viewport().mapToGlobal(pos))
        try:
            proc=psutil.Process(pid)
            if action==kill_action: proc.terminate()
            elif action==search_action: webbrowser.open(f"https://www.google.com/search?q={name}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,"Error",str(e))

class StartupPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout=QtWidgets.QVBoxLayout()
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Filter by name or path...")
        self.search_bar.textChanged.connect(self.refresh)
        layout.addWidget(self.search_bar)
        self.table=QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name","Path","Location"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh()
    def refresh(self):
        filter_text = self.search_bar.text().lower()
        self.items=[]
        self.table.setRowCount(0)
        for root,loc in [(winreg.HKEY_CURRENT_USER,"HKCU"),(winreg.HKEY_LOCAL_MACHINE,"HKLM")]:
            try:
                key=winreg.OpenKey(root,r"Software\Microsoft\Windows\CurrentVersion\Run")
                for i in range(winreg.QueryInfoKey(key)[1]):
                    name,path,_=winreg.EnumValue(key,i)
                    self.items.append((name,path,loc))
            except: pass
        if filter_text:
            self.items = [item for item in self.items if filter_text in item[0].lower() or filter_text in item[1].lower()]
        self.table.setRowCount(len(self.items))
        for i,(name,path,loc) in enumerate(self.items):
            for j,val in enumerate([name,path,loc]):
                self.table.setItem(i,j,QtWidgets.QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()
    def open_menu(self,pos):
        indexes=self.table.selectedIndexes()
        if not indexes: return
        row=indexes[0].row()
        name,path,loc=self.items[row]
        menu=QtWidgets.QMenu()
        disable_action=menu.addAction("Disable")
        enable_action=menu.addAction("Enable")
        delete_action=menu.addAction("Delete Permanently")
        kill_action=menu.addAction("Kill Process Now")
        action=menu.exec(self.table.viewport().mapToGlobal(pos))
        try:
            if action==kill_action:
                for p in psutil.process_iter(['pid','name']):
                    if p.info['name']==name: p.terminate()
            elif action in [disable_action,delete_action]:
                root=winreg.HKEY_CURRENT_USER if loc=="HKCU" else winreg.HKEY_LOCAL_MACHINE
                key=winreg.OpenKey(root,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key,name)
            elif action==enable_action:
                root=winreg.HKEY_CURRENT_USER if loc=="HKCU" else winreg.HKEY_LOCAL_MACHINE
                key=winreg.OpenKey(root,r"Software\Microsoft\Windows\CurrentVersion\Run",0,winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key,name,0,winreg.REG_SZ,path)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,"Error",str(e))
        self.refresh()

class ServicesPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Filter by service name or status...")
        self.search_bar.textChanged.connect(self.refresh)
        layout.addWidget(self.search_bar)
        self.table=QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name","Display Name","Status"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.timer=QtCore.QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(5000)
        self.refresh()
    def refresh(self):
        filter_text = self.search_bar.text().lower()
        self.table.setRowCount(0)
        services=list(psutil.win_service_iter())
        if filter_text:
            services = [s for s in services if filter_text in s.name().lower() or filter_text in s.status().lower()]
        self.services=services
        self.table.setRowCount(len(services))
        for i,s in enumerate(services):
            self.table.setItem(i,0,QtWidgets.QTableWidgetItem(s.name()))
            self.table.setItem(i,1,QtWidgets.QTableWidgetItem(s.display_name()))
            self.table.setItem(i,2,QtWidgets.QTableWidgetItem(s.status()))
        self.table.resizeColumnsToContents()
    def open_menu(self,pos):
        indexes=self.table.selectedIndexes()
        if not indexes: return
        row=indexes[0].row()
        svc=self.services[row]
        menu=QtWidgets.QMenu()
        start_action=menu.addAction("Start")
        stop_action=menu.addAction("Stop")
        restart_action=menu.addAction("Restart")
        action=menu.exec(self.table.viewport().mapToGlobal(pos))
        try:
            if action==start_action: svc.start()
            elif action==stop_action: svc.stop()
            elif action==restart_action: svc.stop(); svc.start()
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,"Error",str(e))
        self.refresh()

class SystemInfoPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(20)
        layout.addWidget(self.create_info_card("Motherboard", self.get_motherboard_info()),0,0)
        layout.addWidget(self.create_info_card("CPU", self.get_cpu_info()),0,1)
        layout.addWidget(self.create_info_card("RAM", self.get_ram_info()),1,0)
        layout.addWidget(self.create_info_card("GPU", self.get_gpu_info()),1,1)
        layout.addWidget(self.create_info_card("Disks", self.get_disk_info()),2,0)
        layout.addWidget(self.create_info_card("Network", self.get_network_info()),2,1)
        self.setLayout(layout)
    def create_info_card(self,title,info_dict):
        group=QtWidgets.QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox { 
                background-color: #1e1e1e; 
                border: 1px solid #00aaff; 
                border-radius: 10px; 
                padding: 10px; 
                font-weight: bold; 
                color: #ffffff;
            }
        """)
        vbox=QtWidgets.QVBoxLayout()
        for k,v in info_dict.items():
            label=QtWidgets.QLabel(f"{k}: {v}")
            label.setStyleSheet("color: #ffffff;")
            vbox.addWidget(label)
        group.setLayout(vbox)
        return group
    def get_motherboard_info(self):
        info={}
        try:
            name=subprocess.check_output("wmic baseboard get product", shell=True).decode().split("\n")[1].strip()
            serial=subprocess.check_output("wmic baseboard get serialnumber", shell=True).decode().split("\n")[1].strip()
            vendor=subprocess.check_output("wmic baseboard get manufacturer", shell=True).decode().split("\n")[1].strip()
            info["Model"]=name
            info["Vendor"]=vendor
            info["Serial"]=serial
        except: info["Error"]="Unable to fetch"
        return info
    def get_cpu_info(self):
        info={}
        try:
            info["Model"]=platform.processor()
            info["Cores"]=psutil.cpu_count(logical=False)
            info["Threads"]=psutil.cpu_count(logical=True)
            info["Max Frequency MHz"]=psutil.cpu_freq().max
        except: info["Error"]="Unable to fetch"
        return info
    def get_ram_info(self):
        info={}
        try:
            mem=psutil.virtual_memory()
            info["Total GB"]=round(mem.total/1024/1024/1024,2)
        except: info["Error"]="Unable to fetch"
        return info
    def get_gpu_info(self):
        info={}
        try:
            gpus=GPUtil.getGPUs()
            if gpus:
                gpu=gpus[0]
                info["Name"]=gpu.name
                info["VRAM MB"]=gpu.memoryTotal
        except: info["Error"]="Unable to fetch"
        return info
    def get_disk_info(self):
        info={}
        try:
            for i,disk in enumerate(psutil.disk_partitions()):
                usage=psutil.disk_usage(disk.mountpoint)
                info[disk.device]=f"{round(usage.total/1024/1024/1024,2)} GB"
        except: info["Error"]="Unable to fetch"
        return info
    def get_network_info(self):
        info={}
        try:
            addrs=psutil.net_if_addrs()
            for iface, addr_list in addrs.items():
                for addr in addr_list:
                    if addr.family.name=="AF_INET":
                        info[iface]=addr.address
        except: info["Error"]="Unable to fetch"
        return info

class ProgramsPageV44(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Filter installed programs...")
        self.search_bar.textChanged.connect(self.refresh)
        layout.addWidget(self.search_bar)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name","Publisher","Install Location","UninstallString"])
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_menu)
        layout.addWidget(self.table)
        self.setLayout(layout)
        self.refresh()
    
    def refresh(self):
        filter_text = self.search_bar.text().lower()
        programs = []
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for path in [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
                try:
                    key = winreg.OpenKey(root, path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)
                        try:
                            name = winreg.QueryValueEx(subkey,"DisplayName")[0]
                            publisher = winreg.QueryValueEx(subkey,"Publisher")[0] if "Publisher" in [winreg.EnumValue(subkey,j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else ""
                            loc = winreg.QueryValueEx(subkey,"InstallLocation")[0] if "InstallLocation" in [winreg.EnumValue(subkey,j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else ""
                            uninstall = winreg.QueryValueEx(subkey,"UninstallString")[0] if "UninstallString" in [winreg.EnumValue(subkey,j)[0] for j in range(winreg.QueryInfoKey(subkey)[1])] else ""
                            programs.append((name,publisher,loc,uninstall))
                        except: pass
                except: pass
        if filter_text:
            programs = [p for p in programs if filter_text in p[0].lower() or filter_text in p[1].lower()]
        self.programs = programs
        self.table.setRowCount(len(programs))
        for i,(name,publisher,loc,uninstall) in enumerate(programs):
            for j,val in enumerate([name,publisher,loc,uninstall]):
                self.table.setItem(i,j,QtWidgets.QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()
    
    def open_menu(self,pos):
        indexes = self.table.selectedIndexes()
        if not indexes: return
        row = indexes[0].row()
        name,publisher,loc,uninstall = self.programs[row]
        menu = QtWidgets.QMenu()
        uninstall_action = menu.addAction("Uninstall Program")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == uninstall_action:
            reply = QtWidgets.QMessageBox.question(self,"Confirm Uninstall",
                        f"Are you sure you want to uninstall {name} and remove residual files?",
                        QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            if reply == QtWidgets.QMessageBox.StandardButton.Yes:
                self.uninstall_program(name, loc, uninstall)
    
    def uninstall_program(self,name,loc,uninstall_string):
        try:
            if uninstall_string:
                subprocess.run(uninstall_string, shell=True)
            else:
                subprocess.run(f'wmic product where "name=\'{name}\'" call uninstall /nointeractive', shell=True)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self,"Error",f"Failed to uninstall {name}:\n{e}")
        if loc and os.path.exists(loc):
            try: shutil.rmtree(loc)
            except: pass
        appdata = os.getenv('APPDATA')
        if appdata:
            for root_dir, dirs, files in os.walk(appdata):
                for d in dirs:
                    if name.lower() in d.lower():
                        try: shutil.rmtree(os.path.join(root_dir,d))
                        except: pass
        QtWidgets.QMessageBox.information(self,"Uninstall","Program uninstalled and residual files removed.")
        self.refresh()

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WinMaster V1.0 - Ultimate Task Manager by @mrasitsarikaya")
        self.resize(1800,1000)
        self.setStyleSheet("background-color: #121212; color: #ffffff;")
        central=QtWidgets.QWidget()
        layout=QtWidgets.QVBoxLayout()
        central.setLayout(layout)
        self.monitor=ResourceMonitor()
        layout.addWidget(self.monitor,1)
        self.tabs=QtWidgets.QTabWidget()
        self.tabs.addTab(ProcessPage(),"Processes")
        self.tabs.addTab(StartupPage(),"Startup Apps")
        self.tabs.addTab(ServicesPage(),"Services")
        self.tabs.addTab(SystemInfoPage(),"System Info")
        self.tabs.addTab(ProgramsPageV44(),"Installed Programs")
        layout.addWidget(self.tabs,3)
        self.setCentralWidget(central)

if __name__=="__main__":
    app=QtWidgets.QApplication(sys.argv)
    app.setStyle('Fusion')
    w=MainWindow()
    w.show()
    sys.exit(app.exec())