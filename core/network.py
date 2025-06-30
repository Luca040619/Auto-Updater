from scapy.all import *
import psutil

from collections import defaultdict
import os

import pandas as pd
from utils.functions import get_size

class NetUsagePerProcess():
    def __init__(self):
        # get the all network adapter's MAC addresses
        self.all_macs = {iface.mac for iface in ifaces.values()}
        # A dictionary to map each connection to its correponding process ID (PID)
        self.connection2pid = {}
        # A dictionary to map each process ID (PID) to total Upload (0) and Download (1) traffic
        self.pid2traffic = defaultdict(lambda: [0, 0])
        self.pid_info_cache = {}
        # the global Pandas DataFrame that's used to track previous traffic stats
        self.global_df = None
        # global boolean for status of the program
        self.is_monitoring = True

    def process_packet(self, packet):
        try:
            # get the packet source & destination IP addresses and ports
            packet_connection = (packet.sport, packet.dport)
        except (AttributeError, IndexError):
            # sometimes the packet does not have TCP/UDP layers, we just ignore these packets
            pass
        else:
            # get the PID responsible for this connection from our `connection2pid` global dictionary
            packet_pid = self.connection2pid.get(packet_connection)
            if packet_pid:
                if packet.src in self.all_macs:
                    # the source MAC address of the packet is our MAC address
                    # so it's an outgoing packet, meaning it's upload
                    self.pid2traffic[packet_pid][0] += len(packet)
                else:
                    # incoming packet, download
                    self.pid2traffic[packet_pid][1] += len(packet)

    def get_connections(self):
        """A function that keeps listening for connections on this machine 
        and adds them to `connection2pid` global variable"""
        while self.is_monitoring:
            # using psutil, we can grab each connection's source and destination ports
            # and their process ID
            for c in psutil.net_connections():
                if c.laddr and c.raddr and c.pid:
                    # if local address, remote address and PID are in the connection
                    # add them to our global dictionary
                    self.connection2pid[(c.laddr.port, c.raddr.port)] = c.pid
                    self.connection2pid[(c.raddr.port, c.laddr.port)] = c.pid
            # sleep for a second, feel free to adjust this
            time.sleep(1)
    
    def print_pid2traffic(self):
        # initialize the list of processes
        processes = []
        for pid, traffic in list(self.pid2traffic.items()):
            # `pid` is an integer that represents the process ID
            # `traffic` is a list of two values: total Upload and Download size in bytes
            
            if pid not in self.pid_info_cache:
                try:
                    p = psutil.Process(pid)
                    self.pid_info_cache[pid] = {
                        "name": p.name(),
                        "exe": p.exe(),
                        "create_time": p.create_time()
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            name = self.pid_info_cache[pid]["name"]
            exe = self.pid_info_cache[pid]["exe"]
                            
            # get the time the process was spawned
            try:
                create_time = datetime.fromtimestamp(self.pid_info_cache[pid]["create_time"])
            except OSError:
                create_time = datetime.fromtimestamp(psutil.boot_time())

            process = {
                "pid": pid, "name": name, "exe": exe, "create_time": create_time, "Upload": traffic[0],
                "Download": traffic[1]*1.1,
            }
            try:
                # calculate the upload and download speeds by simply subtracting the old stats from the new stats
                process["Upload Speed"] = traffic[0] - self.global_df.at[pid, "Upload"]
                process["Download Speed"] = traffic[1] *1.1 - self.global_df.at[pid, "Download"]
            except (KeyError, AttributeError):
                # If it's the first time running this function, then the speed is the current traffic
                # You can think of it as if old traffic is 0
                process["Upload Speed"] = traffic[0]
                process["Download Speed"] = traffic[1]*1.1

            processes.append(process)
        # construct our Pandas DataFrame
        df = pd.DataFrame(processes)
        try:
            # set the PID as the index of the dataframe
            df = df.set_index("pid")
            # sort by column, feel free to edit this column
            df.sort_values("Download", inplace=True, ascending=False)
        except KeyError as e:
            pass # when dataframe is empty
        
        printing_df = df.copy() # make another copy of the dataframe just for fancy printing
        try:
            # apply the function get_size to scale the stats like '532.6KB/s', etc.
            printing_df["Download"] = printing_df["Download"].apply(get_size)
            printing_df["Upload"] = printing_df["Upload"].apply(get_size)
            printing_df["Download Speed"] = printing_df["Download Speed"].apply(get_size).apply(lambda s: f"{s}/s")
            printing_df["Upload Speed"] = printing_df["Upload Speed"].apply(get_size).apply(lambda s: f"{s}/s")
        except KeyError as e:
            pass # when dataframe is empty again

        # update the global df to our dataframe
        self.global_df = df

    def get_pid2traffic_one_process(self, p_name): # Return the download speed of the process name entered
        processes = []
        down_process = 0
        print(self.pid2traffic.items())
        for pid, traffic in list(self.pid2traffic.items()):
            
            try: p = psutil.Process(pid)
            except psutil.NoSuchProcess: continue
                
            name = p.name()

            process = {
                "pid": pid, "name": name, "Upload": traffic[0],
                "Download": traffic[1]*1.1,
            }
            try:
                # calculate the upload and download speeds by simply subtracting the old stats from the new stats
                process["Upload Speed"] = traffic[0] - self.global_df.at[pid, "Upload"]
                process["Download Speed"] = traffic[1]*1.1 - self.global_df.at[pid, "Download"]
            except (KeyError, AttributeError):
                # If it's the first time running this function, then the speed is the current traffic
                process["Upload Speed"] = traffic[0]
                process["Download Speed"] = traffic[1]*1.1
            if name == p_name:
                down_process = process["Download Speed"]

            processes.append(process)

        # construct our Pandas DataFrame
        df = pd.DataFrame(processes)
        try:
            df = df.set_index("pid")
            df.sort_values("Download", inplace=True, ascending=False)
        except KeyError as e:    
            pass # when dataframe is empty

        self.global_df = df
                
        return down_process
    
    def get_pid2disk_activity(self, p_name): # Return the disk usage of the process name entered
        disk_activity = {"read_bytes": 0, "write_bytes": 0}
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            if proc.info['name'] == p_name:
                io_counters = proc.io_counters()
                disk_activity['read_bytes'] = io_counters.read_bytes
                disk_activity['write_bytes'] = io_counters.write_bytes
                break  # Interrompe il ciclo una volta trovato il processo
        return disk_activity
    
    def get_current_disk_activity(self, p_name):
        current_activity = self.get_pid2disk_activity(p_name)
        current_time = time.time()

        if not hasattr(self, 'previous_disk_activity'):
            self.previous_disk_activity = {}

        if p_name in self.previous_disk_activity:
            read_speed = (current_activity['read_bytes'] - self.previous_disk_activity[p_name]['read_bytes']) / (current_time - self.previous_disk_activity[p_name]['time'])
            write_speed = (current_activity['write_bytes'] - self.previous_disk_activity[p_name]['write_bytes']) / (current_time - self.previous_disk_activity[p_name]['time'])
        else:
            read_speed = write_speed = 0  # Nessuna attività precedente registrata, velocità impostata a 0

        self.previous_disk_activity[p_name] = {'read_bytes': current_activity['read_bytes'], 'write_bytes': current_activity['write_bytes'], 'time': current_time}

        return {"read_speed": read_speed, "write_speed": write_speed}
    
class NetUsageMonitor:
    def __init__(self):
        self.active_interface = self.get_active_interface()
        self._last_net_in = None
        self._last_net_out = None

    def get_active_interface(self):
        counters = psutil.net_io_counters(pernic=True)
        return max(counters.items(), key=lambda x: x[1].bytes_recv + x[1].bytes_sent)[0]

    def get_net_speed(self):
        """Restituisce (download_speed, upload_speed) in byte/s"""
        inf = self.active_interface
        counters = psutil.net_io_counters(pernic=True, nowrap=True)[inf]

        net_in = counters.bytes_recv
        net_out = counters.bytes_sent

        if self._last_net_in is None:
            self._last_net_in = net_in
            self._last_net_out = net_out
            return 0, 0

        delta_in = net_in - self._last_net_in
        delta_out = net_out - self._last_net_out

        self._last_net_in = net_in
        self._last_net_out = net_out

        return delta_in, delta_out