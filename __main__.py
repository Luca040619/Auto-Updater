'''
Auto updater is a program which help you to update many apps installed on your pc,
monitor the network usage for every process and shutdown the system when has finished

Copyright (C) <2022-present>  <Luca Porzio>

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

__title__ = 'Auto Updater'
__author__ = 'Luca040619'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2022-present Luca Porzio'
__version__ = '1.0'

import os
import sys
import signal
import pandas

from threading import Thread
from scapy.all import *
from net_usage_per_process import NetUsagePerProcess

import logging
import json

import time
from datetime import timedelta
import msvcrt

import psutil
import subprocess
import ctypes

from termcolor import colored

from os import system
system("title " + __title__)

#from tendo import singleton
#me = singleton.SingleInstance() # will sys.exit(-1) if other instance is running

class Updater(NetUsagePerProcess):
    def __init__(self):
        self.prompt = print
        self.programs = []
        self.default_programs = []
        self.file = 'programs.txt'
        self.config_file = 'config.json'
        logging.basicConfig(filename="logfile.log", level=logging.INFO, format = '[%(asctime)s] %(levelname)s : %(message)s', datefmt = '%d/%m/%Y - %H:%M:%S')

        self.config_data = {
            'auto-shutdown' : True,
            'upload-monitor' : False,
            'net-interface' : self.default_net_adapter(),
            'down-speed' : 80,
            'up-speed' : 50
        }

        self.options = {1 : self.start_updating,
                        2 : self.shutdown_after_download,
                        3 : self.view_active_processes,
                        4 : self.app_management_menu,
                        5 : self.edit_options,
                        6 : self.print_EULA,
                        0 : self.exit
                        }
        
        self.all_macs = {iface.mac for iface in ifaces.values()}
        # A dictionary to map each connection to its correponding process ID (PID)
        self.connection2pid = {}
        # A dictionary to map each process ID (PID) to total Upload (0) and Download (1) traffic
        self.pid2traffic = defaultdict(lambda: [0, 0])
        # the global Pandas DataFrame that's used to track previous traffic stats
        self.global_df = None
        # global boolean for status of the program
        self.is_monitoring = True
    
    def read(self):
        """Reads the file and load the programs in the list
        """
        if not os.path.exists(self.file):
            try:
                with open(self.file, "x") as f: f.close()
                logging.warning('File programs.txt not found, successfully recreated')
            except FileExistsError: None
        
        with open('logfile.log', 'r') as lf:
            log = lf.readlines()
        
        if len(log) > 250:
            with open('logfile.log', 'w') as lf:
                lf.write('')
                lf.close()
                logging.info('Reached 250 log lines, log file reset')
                
        reading = open(self.file, "r").readlines()
        for line in reading:
            line.replace("\n", "")
            self.programs.append(line)

    def write(self, dir):
        """Write in the file the directory entered

        Parameters
        -----------
        dir: class: `str`
            the directory of the executable
        """
        writing = open(self.file, "a")
        writing.write(dir + "\n")
        writing.close()
        logging.info('Successfully added new program')
    
    def re_write_all(self):
        writing = open(self.file, "w")
        for path in self.programs:
            writing.write(path)
        
        writing.close()
    
    def file_in_list(self, dir):
        """Check if the dir is in the programs list

        Parameters
        -----------
        dir: class: `str`
            the directory of the executable
        """
        is_present = False

        for path in self.programs:
            str_path = str(os.path.basename(path)).strip()
            str_new_file = str(os.path.basename(dir)).strip()

            if str_path.__eq__(str_new_file):
                is_present = True
                break
        
        return is_present
    
    def verify_dir(self, dir):
        """Check if the directory exists

        Parameters
        -----------
        dir: class: `str`
            the directory of the executable
        """
        return os.path.isfile(dir) if os.path.exists(dir) else False

    def print_programs(self):
        """Print all programs name on the prompt
        """
        os.system('cls')

        if len(self.programs) > 0:
            self.prompt(" ----- LISTA PROGRAMMI -----")

            i = 0
            for program in self.programs:
                i = i + 1
                self.prompt(" ", end = "")
                self.prompt(str(i), os.path.basename(program), sep=' - ', end = "")
        else:
            self.prompt(" La lista dei programmi è vuota!")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding='utf-8-sig') as json_file:
                    self.config_data = json.load(json_file)

                logging.info('Successfully loaded configuration file')
            
            except json.decoder.JSONDecodeError:
                self.prompt(' File di configurazione corrotto, ripristino delle impostazioni predefinite...')
                logging.error('Unable to load configuration file, reset to default settings')
                
                self.write_config_options()
                self.sleep(5)
                os.system('cls')
                self.load_config()
        else:
            self.setup()
            logging.info('Setup completed')
    
    def write_config_options(self):
        with open(self.config_file, "w") as json_file:
            json.dump(self.config_data, json_file, 
                    indent=4,  
                    separators=(',',': '))
    
    def sleep(self, t):
        """It's time.sleep() but ignore inputs while sleeps"""
        time.sleep(t)
        while msvcrt.kbhit(): flush = input() #ignore input during time.sleep
    
    def search_default_programs(self):
        """Search the default apps in the PC
        """
        default_programs = [None]*26
        default_programs[0] = r"C:\Program Files (x86)\Steam\steam.exe"
        default_programs[1] = r"D:\Program Files (x86)\Steam\steam.exe"
        default_programs[2] = r"C:\Program Files\Steam\steam.exe"
        default_programs[3] = r"D:\Program Files\Steam\steam.exe"
        default_programs[4] = r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"
        default_programs[5] = r"D:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"
        default_programs[6] = r"C:\Program Files\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"
        default_programs[7] = r"D:\Program Files\Epic Games\Launcher\Portal\Binaries\Win32\EpicGamesLauncher.exe"
        default_programs[8] = r"C:\Program Files (x86)\Riot Games\Riot Client\RiotClientServices.exe"
        default_programs[9] = r"D:\Program Files (x86)\Riot Games\Riot Client\RiotClientServices.exe"
        default_programs[10] = r"C:\Program Files\Riot Games\Riot Client\RiotClientServices.exe"
        default_programs[11] = r"D:\Program Files\Riot Games\Riot Client\RiotClientServices.exe"
        default_programs[12] = r"C:\Riot Games\Riot Client\RiotClientServices.exe"
        default_programs[13] = r"D:\Riot Games\Riot Client\RiotClientServices.exe"
        default_programs[14] = r"C:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\UbisoftConnect.exe"
        default_programs[15] = r"D:\Program Files (x86)\Ubisoft\Ubisoft Game Launcher\UbisoftConnect.exe"
        default_programs[16] = r"C:\Program Files\Ubisoft\Ubisoft Game Launcher\UbisoftConnect.exe"
        default_programs[17] = r"D:\Program Files\Ubisoft\Ubisoft Game Launcher\UbisoftConnect.exe"
        default_programs[18] = r"C:\Program Files (x86)\Origin\Origin.exe"
        default_programs[19] = r"D:\Program Files (x86)\Origin\Origin.exe"
        default_programs[20] = r"C:\Program Files\Origin\Origin.exe"
        default_programs[21] = r"D:\Program Files\Origin\Origin.exe"
        default_programs[22] = r"C:\Program Files\Battle.net\Battle.net Launcher.exe"
        default_programs[23] = r"D:\Program Files\Battle.net\Battle.net Launcher.exe"
        default_programs[24] = r"C:\Program Files (x86)\Battle.net\Battle.net Launcher.exe"
        default_programs[25] = r"D:\Program Files (x86)\Battle.net\Battle.net Launcher.exe"

        for program in default_programs:
            if self.verify_dir(program):
                self.default_programs.append(program)

        default_programs.clear()

    def setup(self):
        os.system('cls')
        self.prompt(" Benvenuto in Auto Updater, questo programma ti consentirà di aggiornare in automatico i\n"
                    " tuoi programmi preferiti, spegnere il computer al termine dell'attività di rete,\n"
                    " modificare le app e launcher da aggiornare in qualsiasi momento e molto altro ancora\n")
        
        self.prompt(" Quando sei pronto premi il tasto invio ed iniziamo la configurazione!\n")
        
        input(" NOTA BENE: è necessario che le app abbiano un'opzione di aggiornamento\n"
            " automatico all'avvio abilitata, i launcher sono i più consigliati\n")

        with open(self.file, 'w') as f:
            f.write('')
            f.close()
        
        self.edit_auto_shutdown()
        
        os.system('cls')

        self.choose_net_adapter()
        
        os.system('cls')

        self.config_data["upload-monitor"] = False
        self.write_config_options()
        
        self.search_default_programs()
        self.prompt(" Auto Updater ha trovato questi launcher in automatico:\n")

        i = 0
        for program in self.default_programs:
            i = i + 1
            print(" ", end = "")
            print(str(i), os.path.basename(program), sep=' - ')

        ok = False
        while not ok:
            x = str(input("\n Desideri mantenerli nella lista? (Y/N) (puoi modificarla in qualsiasi momento)\n Input: "))

            if x.lower() == "y":
                for program in self.default_programs:
                    self.write(program)

                ok = True

            elif x.lower() == "n":
                self.programs = []
                ok = True

            else: self.prompt("\n Valore inserito non valido!")
        
        self.prompt("\n Setup completato! Benvenuto in Auto Updater!\n")
        self.sleep(2)
        os.system('cls')
    
    def start(self):
        self.prompt("Benvenuto in Auto Updater! Cosa vuoi fare?")
        while True:
            self.start_menu()

    def start_menu(self):
        self.prompt(" ------------- AUTO UPDATER -------------")

        self.prompt(" 1 - Avvia aggiornamenti\t\t|\n 2 - Spegni PC a fine attività di rete\t|\n 3 - Visualizza processi di rete attivi\t|\n 4 - Gestione applicazioni\t\t|\n 5 - Impostazioni\t\t\t|\n"
            " 6 - EULA ed informazioni dettagliate\t|\n 0 - Esci\t\t\t\t|\n")
        
        try: choice = input(" Scelta: ") 
        except KeyboardInterrupt: return os.system('cls')

        try: self.options[int(choice)]()
        except (KeyError, ValueError):
            self.prompt("\n Opzione non valida!", end = "")
            self.sleep(1.5)
                
        except KeyboardInterrupt:
            if int(choice) == 2: logging.info('Network monitoring interrupted by user')
            else: pass
        
        os.system('cls')
    
    def updating(self):
        os.system('cls')
        if self.config_data['auto-shutdown']: auto_off = 'SI'    
        else: auto_off = 'NO'

        self.prompt("\n ------- AGGIORNAMENTO ------- " + colored('[Min: {}KB/s]'.format(self.config_data['down-speed']), 'cyan') + '|' + colored('[Auto off: {}]'.format(auto_off), 'cyan') + '\n')

        start_time = time.time()
        logging.info('Started updating')
        
        i = 1
        for app in self.programs:
            if self.is_monitoring:
                self.delete_last_lines(1)
                
                app = app.strip()
                name = os.path.basename(app)
                self.prompt('\n Avvio di {} in corso...      \n\n'.format(name))#, end = '\r')
                process = subprocess.Popen(r"{}".format(app))

                if name.__eq__('UbisoftConnect.exe'): name = 'upc.exe'
                elif name.__eq__('Battle.net Launcher.exe'): name = 'Agent.exe'
                    
                self.delete_last_lines(1)
                
                sec_inactivity = 0
                while sec_inactivity < 240 and self.is_monitoring:
                    bytes_in = self.get_pid2traffic_one_process(name)
                    net_usage = f" Current net-usage: {self.humansize(bytes_in)}/s"

                    sec_inactivity = self.seconds_of_inactivity(sec_inactivity, bytes_in, None)
                    color, none = self.set_color(bytes_in, None)
                    
                    self.delete_last_lines(3)
                    self.prompt("\n {} - {} in download: {}          \n\n{}".format(i, os.path.basename(app), colored(net_usage, color), colored(' (premi CTRL + C per interrompere)', 'cyan')))#, end = '\r')

                    while msvcrt.kbhit(): flush = input()
                    self.sleep(1)
                    self.delete_last_lines(1)

                if self.is_monitoring:
                    self.delete_last_lines(3)
                    self.prompt("\n {} - {} {}                                           \
                                                        ".format(i, os.path.basename(app), colored('download completato', 'green')))
                
                process.kill() #try to kill the process in two different mode
                os.system(f'taskkill /IM "{name}" /F')
                self.delete_last_lines(1)

                i += 1

        end_time = time.time()

        if self.is_monitoring:
            self.is_monitoring = False
            logging.info('Finished updating, all download completed')
            
            self.delete_last_lines(1)
            self.prompt(colored("\n DOWNLOAD COMPLETATI                       ", 'green'))
            self.prompt(' Tempo trascorso: ', timedelta(seconds = end_time - start_time), sep = ' ')
            if auto_off:
                logging.info('PC shutting down')
                os.system('shutdown -t 0 -f -s')
            
            input('\n (premi invio per continuare)')

            os.kill(os.getpid(), signal.CTRL_C_EVENT)
        else:
            logging.info('Updating interrupted by user')
    
    def start_updating(self):
        self.is_monitoring = True
        printing_thread = Thread(target = self.updating)
        printing_thread.start()
        # start the get_connections() function to update the current connections of this machine
        connections_thread = Thread(target = self.get_connections)
        connections_thread.start()
        sniff(prn=self.process_packet, store=False)
        self.is_monitoring = False
        self.sleep(1)
        
    def seconds_of_inactivity(self, sec_inactivity, bytes_in, bytes_out):
        """Return the value increased or reset of sec_inactivity according to the parameters"""
        if bytes_out is not None:
            if bytes_in < self.config_data['down-speed']*1000:
                sec_inactivity += 0.5
            else:
                sec_inactivity = 0
        
            if bytes_out < self.config_data['up-speed']*1000:
                sec_inactivity += 0.5
            else:
                sec_inactivity = 0
        
        else:
            if bytes_in < self.config_data['down-speed']*1000:
                sec_inactivity += 1
            else:
                sec_inactivity = 0
        
        return sec_inactivity
    
    def set_color(self, bytes_in, bytes_out):
        if bytes_in < self.config_data['down-speed']*1000:
            color_in = 'red'
        else:
            color_in = 'green'
        
        color_out = None
        if bytes_out is not None:
            if bytes_out < self.config_data['up-speed']*1000:
                color_out = 'red'
            else:
                color_out = 'green'
        
        return color_in, color_out
    
    def delete_last_lines(self, times):
        """Delete the last lines in the console according to the parameter
        
        Parameters
        -----------
        times: class: `int`
            the number of lines to delete
        """
        for i in range(times):
            sys.stdout.write('\x1b[1A')
            sys.stdout.write('\x1b[2K')

    def value_net_usage(self, inf, up):
        net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[inf]
        net_in_1 = net_stat.bytes_recv
        net_out_1 = net_stat.bytes_sent

        self.sleep(1)

        net_stat = psutil.net_io_counters(pernic=True, nowrap=True)[inf]
        net_in_2 = net_stat.bytes_recv
        net_out_2 = net_stat.bytes_sent
        
        if not up: return net_in_2 - net_in_1
        else: return net_in_2 - net_in_1, net_out_2 - net_out_1
        #return f" Current net-usage: {net_in_human}/s"#, OUT: {net_out}/s")
    
    def humansize(self, nbytes):
        """Returns in human sizes the entered bytes

        Parameters
        -----------
        nbytes: class: `int`
            the number of bytes to convert in "human size"
        """
        suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        i = 0

        while nbytes >= 1024 and i < len(suffixes)-1:
            nbytes /= 1024.
            i += 1

        f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])
    
    def default_net_adapter(self):
        addresses = psutil.net_if_addrs()

        for interface, addr_list in addresses.items():
            return interface
    
    def choose_net_adapter(self):
        addresses = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        available_networks = []
        for intface, addr_list in addresses.items():
            if any(getattr(addr, 'address').startswith("169.254") for addr in addr_list):
                continue
            elif intface in stats and getattr(stats[intface], "isup"):
                available_networks.append(intface)

        self.prompt(' ----- INTERFACCE DI RETE -----')
        i = 1
        for net in available_networks:
            print(" " + str(i), net, sep = ' - ')
            i = i + 1
        
        ok = False
        while not ok:
            x = str(input("\n Inserisci il numero corrispondente all'interfaccia di rete da monitorare durante i download\n Input: "))

            try:
                if int(x) > 0:
                    selected_ni = available_networks[int(x) - 1]
                    ok = True
                    self.config_data["net-interface"] = selected_ni
                
                else:
                    self.prompt("\n Valore inserito non valido!")
                    self.sleep(1.5)
                    self.delete_last_lines(5)
                
            except:
                self.prompt("\n Valore inserito non valido!")
                self.sleep(1.5)
                self.delete_last_lines(5)
        
        logging.info('Changed network adapter')
    
    def edit_auto_shutdown(self):
        ok = False
        while not ok:
            x = str(input(" Vuoi che il computer venga spento al termine dei download? (Y/N)\n Input: "))

            if x.lower() == "y":
                self.config_data["auto-shutdown"] = True
                ok = True
            elif x.lower() == "n":
                self.config_data["auto-shutdown"] = False
                ok = True
            else:
                self.prompt("\n Valore inserito non valido!")
                self.sleep(1.5)
                self.delete_last_lines(4)
    
    def upload_monitor(self):
        ok = False
        while not ok:
            x = str(input(" Vuoi monitorare anche l'upload prima di spegnere il PC? (Y/N)\n Input: "))

            if x.lower() == "y":
                self.config_data["upload-monitor"] = True
                ok = True
            elif x.lower() == "n":
                self.config_data["upload-monitor"] = False
                ok = True
            else:
                self.prompt("\n Valore inserito non valido!")
                self.sleep(1.5)
                self.delete_last_lines(4)
    
    def download_speed(self):
        ok = False
        while not ok:
            speed = str(input(" Inserisci in KB/s la velocità di download minima che verrà monitorata\n (sotto tale soglia non verrà considerata attività di rete)\n Input: "))

            try:
                if float(speed) > 0:
                    self.config_data["down-speed"] = float(speed)
                    ok = True
            
                else:
                    self.prompt("\n Inserisci un valore numerico valido!")
                    self.sleep(1.5)
                    self.delete_last_lines(5)
            
            except:
                self.prompt("\n Inserisci un valore numerico valido!")
                self.sleep(1.5)
                self.delete_last_lines(5)
    
    def upload_speed(self):
        ok = False
        while not ok:
            speed = str(input(" Inserisci in KB/s la velocità di upload minima che verrà monitorata\n (sotto tale soglia non verrà considerata attività di rete)\n Input: "))

            try:
                if float(speed) > 0:
                    self.config_data["up-speed"] = float(speed)
                    ok = True
            
                else:
                    self.prompt("\n Inserisci un valore numerico valido!")
                    self.sleep(1.5)
                    self.delete_last_lines(5)
            
            except:
                self.prompt("\n Inserisci un valore numerico valido!")
                self.sleep(1.5)
                self.delete_last_lines(5)
    
    def view_log_file(self):
        os.system('cls')

        log = open('logfile.log', 'r').readlines()
        for line in log:
            self.prompt(' ' + line, end = '')

        input('\n (premi invio per uscire)')
    
    def restore_app(self):
        self.prompt(" Attenzione! L'app verrà resettata e tutti i dati andranno persi, scrivi CONFERMA per continuare")
        confirm = str(input(' Input: '))

        if confirm.__eq__('CONFERMA'):
            try:
                os.remove('programs.txt')
                os.remove('config.json')
            except: None

            self.prompt("\n L'app verrà riavviata...")
            self.sleep(2)

            os.system('cls')
            start()
        else:
            self.prompt('\n Procedura di ripristino annullata!')

            self.sleep(2)
    
    def shutdown_after_download(self):
        os.system('cls')
       
        net = self.config_data['net-interface']
        up_monitor = self.config_data['upload-monitor']

        if up_monitor: up = str(self.config_data['up-speed']) + 'KB/s'
        else: up = 'NO'

        logging.info('Started network monitoring')

        self.prompt("\n SPEGNIMENTO AL TERMINE DELL'ATTIVITA' DI RETE - "+ colored('Min:[', 'cyan') + colored('Down: {}KB/s'.format(self.config_data['down-speed']), 'green') + '|' + colored(f'Up: {up}', 'red') + colored(']', 'cyan'))
        self.prompt(' _____________________________________________________________________________\n\n\n\n\n\n')

        sec_inactivity = 0
        while sec_inactivity < 360:
            data = []
            io = psutil.net_io_counters(pernic=True, nowrap=True)
            
            bytes_in, bytes_out = self.value_net_usage(net, True)
            
            if up_monitor:
                sec_inactivity = self.seconds_of_inactivity(sec_inactivity, bytes_in, bytes_out)
            
            else:
                sec_inactivity = self.seconds_of_inactivity(sec_inactivity, bytes_in, None)
            
            data.append({
                "Interface|": net + '|', "Download|": self.humansize(io[net].bytes_recv) + '|',
                "Upload|": self.humansize(io[net].bytes_sent) + '|',
                "Upload Speed|": f"{self.humansize(bytes_out)}/s|",
                "Download Speed|": f"{self.humansize(bytes_in)}/s|",
            })

            self.delete_last_lines(6)

            df = pandas.DataFrame(data)
            print(df.to_string())

            print('\n Tempo mancante allo spegnimento: ' + colored(str(int(360 - sec_inactivity)) + ' secondi','red'))

            print(colored('\n (premi CTRL + C per interrompere)', 'cyan'))
        
        logging.info('Finished network monitoring, shutting down')
        
        os.system('shutdown -t 0 -f -s')
    
    def view_active_processes(self):
        self.is_monitoring = True
        os.system('cls')
        self.view_all_programs()
        self.is_monitoring = False
    
    def app_management_menu(self):
        choice = 1
        while choice != '0':
            os.system('cls')

            self.prompt( ' ------- GESTIONE APPLICAZIONI -------')
            self.prompt(' 1 - Visualizza launcher e programmi  |')
            self.prompt(' 2 - Aggiungi applicazione\t      |')
            self.prompt(' 3 - Rimuovi applicazione\t      |')
            self.prompt(' 0 - Indietro\t\t\t      |')

            try:
                choice = input('\n Scelta: ')
                print()

                edit_options = {1 : lambda:[self.print_programs(),input("\n (premi invio per continuare)")],
                                2 : self.add_program,
                                3 : self.del_program,
                                0 : self.back
                                }

                edit_options[int(choice)]()
                
            except:
                self.prompt(' Opzione non valida!')
                self.sleep(2)

    
    def add_program(self):
        self.prompt(" Inserisci il percorso del file da aggiungere alla lista:")
        dir = input(" Percorso: ")
        
        if self.verify_dir(dir):
            if not self.file_in_list(dir):
                self.programs.append(dir + "\n")
                self.write(dir)
                self.prompt("\n Il file è stato aggiunto alla lista dei programmi")
            else:
                self.prompt("\n Il file è già presente nella lista!")
        else:
            self.prompt("\n Il percorso specificato non è valido!")

        self.sleep(2)
    
    def del_program(self):
        self.print_programs()

        if len(self.programs) > 0:
            try:
                self.prompt("\n Inserisci l'indice del programma da eliminare")
                i = int(input("\n Indice: "))
            except:
                self.prompt("\n Posizione indicata non valida!")
                return self.sleep(2)

            if i > 0 and i <= len(self.programs):
                self.programs.pop(i-1)
                self.re_write_all()
                self.prompt("\n App eliminata dalla lista")

                logging.info('Successfully deleted app from the list')
            else:
                self.prompt("\n Posizione indicata non valida!")
        
        self.sleep(2)
        return os.system('cls')

    def back(self):
        return
    
    def edit_options(self):
        choice = 1
        while choice != '0':
            os.system('cls')

            self.prompt( ' --------- IMPOSTAZIONI ---------')
            self.prompt(' 1 - Spegnimento automatico\t |')
            self.prompt(' 2 - Modifica adattatore di rete |')
            self.prompt(' 3 - Monitora upload\t\t |')
            self.prompt(' 4 - Velocità download\t\t |')
            self.prompt(' 5 - Velocità upload\t\t |')
            self.prompt(' 6 - Visualizza log\t\t |')
            self.prompt(' 7 - Ripristina e riesegui setup |')
            self.prompt(' 0 - Indietro\t\t\t |')

            try:
                choice = input('\n Scelta: ')
                print()

                edit_options = {1 : lambda:[self.edit_auto_shutdown(), self.write_config_options(), print('\n Impostazione salvata!')],
                                2 : lambda:[self.choose_net_adapter(), self.write_config_options(), print('\n Impostazione salvata!')],
                                3 : lambda:[self.upload_monitor(), self.write_config_options(), print('\n Impostazione salvata!')],
                                4 : lambda:[self.download_speed(), self.write_config_options(), print('\n Impostazione salvata!')],
                                5 : lambda:[self.upload_speed(), self.write_config_options(), print('\n Impostazione salvata!')],
                                6 : self.view_log_file,
                                7 : self.restore_app,
                                0 : self.back
                                }

                edit_options[int(choice)]()

                if not int(choice).__eq__(0) and not int(choice).__eq__(6) and not int(choice).__eq__(7):
                    self.sleep(2)
                
            except:
                self.prompt(' Opzione non valida!')
                self.sleep(2)
            
    def print_EULA(self):
        os.system('cls')
        self.prompt(' :author: Luca Porzio\n :license: GPL\n :version: 1.0\n :copyright: (C) 2022-present Luca Porzio\n ------------------------')
        self.prompt(' END USER LICENSE AGREMENT\n'
                    ' Auto updater è un programma open-source distribuito con licenza GPL (più dettagli nel\n'
                    ' file LICENSE) che permette di aggiornare e monitorare i propri programmi da un comodo\n'
                    ' menu di scelta rapida con molte opzioni di personalizzazione.\n\n'
                    " È consigliato l'uso per soli launcher ma può funzionare con tutti gli eseguibili, il\n"
                    " creatore non è responsabile per eventuali perdite di dati riguardanti l'app o esterni.\n\n"
                    " Utilizzando l'app l'utente afferma di aver preso visione dell'EULA e del file LICENSE\n"
                    " comprendendo le clausole e rispettando i diritti d'autore.\n")

        input(' (premi invio per uscire)')
    
    def exit(self): quit()

def start():
    updater = Updater()
    updater.load_config()
    updater.read()
    updater.start()

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if __name__ == '__main__':
    if is_admin():start()
    else: ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1) # Re-run the program with admin rights
