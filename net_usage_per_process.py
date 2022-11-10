'''
<Auto updater is a program which help you to update many apps installed on your pc,
monitor the network usage for every process and shutdown the system when has finished>
Copyright (C) 2022-present Luca Porzio

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
from scapy.all import *
import psutil

from collections import defaultdict
import os
from threading import Thread

import pandas as pd

class NetUsagePerProcess():
    def __init__(self):
        # get the all network adapter's MAC addresses
        self.all_macs = {iface.mac for iface in ifaces.values()}
        # A dictionary to map each connection to its correponding process ID (PID)
        self.connection2pid = {}
        # A dictionary to map each process ID (PID) to total Upload (0) and Download (1) traffic
        self.pid2traffic = defaultdict(lambda: [0, 0])
        # the global Pandas DataFrame that's used to track previous traffic stats
        self.global_df = None
        # global boolean for status of the program
        self.is_monitoring = True

    def get_size(self, bytes):
        """
        Returns size of bytes in a nice format
        """
        for unit in ['', 'K', 'M', 'G', 'T', 'P']:
            if bytes < 1024:
                return f"{bytes:.2f}{unit}B"
            bytes /= 1024

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
        for pid, traffic in self.pid2traffic.items():
            # `pid` is an integer that represents the process ID
            # `traffic` is a list of two values: total Upload and Download size in bytes
            try: p = psutil.Process(pid)
            except psutil.NoSuchProcess: continue
                
            name = p.name()
            # get the time the process was spawned
            try:
                create_time = datetime.fromtimestamp(p.create_time())
            except OSError:
                # system processes, using boot time instead
                create_time = datetime.fromtimestamp(psutil.boot_time())

            process = {
                "pid": pid, "name": name, "create_time": create_time, "Upload": traffic[0],
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
            printing_df["Download"] = printing_df["Download"].apply(self.get_size)
            printing_df["Upload"] = printing_df["Upload"].apply(self.get_size)
            printing_df["Download Speed"] = printing_df["Download Speed"].apply(self.get_size).apply(lambda s: f"{s}/s")
            printing_df["Upload Speed"] = printing_df["Upload Speed"].apply(self.get_size).apply(lambda s: f"{s}/s")
        except KeyError as e:
            pass # when dataframe is empty again
        
        os.system("cls") if "nt" in os.name else os.system("clear") # clear the screen based on your OS

        print(printing_df.to_string())
        # update the global df to our dataframe
        self.global_df = df

    def get_pid2traffic_one_process(self, p_name): # Return the download speed of the process name entered
        processes = []
        down_process = 0
        for pid, traffic in self.pid2traffic.items():
            
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
            
    def print_stats(self):
        """Simple function that keeps printing the stats"""
        while self.is_monitoring:
            time.sleep(1)
            if self.is_monitoring: # in the second of sleep the value can change
                self.print_pid2traffic()
                print('\n (premi CTRL + C per uscire)')

    def view_all_programs(self):
        printing_thread = Thread(target=self.print_stats)
        printing_thread.start()
        # start the get_connections() function to update the current connections of this machine
        connections_thread = Thread(target=self.get_connections)
        connections_thread.start()
        # start sniffing
        sniff(prn=self.process_packet, store=False)
        # setting the global variable to False to exit the program
