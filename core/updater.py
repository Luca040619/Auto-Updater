import os
import psutil
import subprocess
import threading
import time
from pathlib import Path
from utils.functions import get_size
from core.network import NetUsagePerProcess
from scapy.all import AsyncSniffer

class Updater:
    def __init__(self, launcher_configs: dict, inactivity_timeout: int = 10):
        self.launcher_configs = launcher_configs
        print(f"Configurazione dei launcher: {self.launcher_configs}")
        self.inactivity_timeout = inactivity_timeout
        self.cancelled = False
        self.current_status = {}
        self.launcher_status = {}
        self.current_launcher = None
        self.is_running = False
        self.sniffer = None
        self.on_complete = None
        self._lock = threading.Lock()

        self.net_monitor = NetUsagePerProcess()

    def mark_cancelled_launchers(self):
        for name, data in self.launcher_status.items():
            if data.get("status") == "in_progress":
                data["status"] = "cancelled"

    def _log(self, message):
        print("[Updater]", message)

    def stop_updating(self):
        self.is_running = False
        self.net_monitor.is_monitoring = False
        if hasattr(self, "sniffer") and self.sniffer.running:
            self.sniffer.stop()

    def start(self):
        with self._lock:
            if self.is_running:
                self._log("Avvio ignorato: già in esecuzione.")
                return
            self.is_running = True

        self._log("Avvio aggiornamento launcher...")

        self.net_monitor.is_monitoring = True

        # Thread per aggiornare le connessioni
        connections_thread = threading.Thread(target=self.net_monitor.get_connections, daemon=True)
        connections_thread.start()

        self.sniffer = AsyncSniffer(prn=self.net_monitor.process_packet, store=False)
        self.sniffer.start()

        # Thread per eseguire gli aggiornamenti
        thread = threading.Thread(target=self._run_all, daemon=True)
        thread.start()

    def stop(self):
        with self._lock:
            self.stop_updating()
            
        self._log("Aggiornamento interrotto manualmente.")

    def _run_all(self):
        for name, data in self.launcher_configs.items():
            if not data.get("enabled", False):
                continue

            origin_name = name   
            path = data.get("path")
            name = os.path.basename(path)

            if name.__eq__('UbisoftConnect.exe'):
                name = 'upc.exe'
            elif name.__eq__('Battle.net Launcher.exe'):
                name = 'Agent.exe'

            if not path or not Path(path).exists():
                self._log(f"{name}: percorso non valido, salto.")
                continue

            with self._lock:
                if not self.is_running:
                    break

            self._run_single_launcher(name, origin_name, path)

        self.stop_updating()

        if self.on_complete and not self.cancelled:
            self.on_complete()

        self._log("Tutti i launcher sono stati processati.")

    def _run_single_launcher(self, name, origin_name, path):
        self._log(f"Avvio di {name}...")
        proc = subprocess.Popen([path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        last_active_time = time.time()
        downloaded_total = 0

        while True:
            with self._lock:
                if not self.is_running:
                    self.launcher_status[origin_name]["status"] = "cancelled"
                    self._log(f"{name} terminato ma aggiornamento interrotto.")
                    return

            try:
                # Ottieni velocità rete e disco usando NetUsagePerProcess
                print(f"Monitoraggio di {origin_name}...")
                speed_recv = self.net_monitor.get_pid2traffic_one_process(name)
                disk_speeds = self.net_monitor.get_current_disk_activity(name)
                speed_read = max(0, disk_speeds.get("read_speed", 0))
                speed_write = max(0, disk_speeds.get("write_speed", 0))

                downloaded_total += speed_recv

                self._log(f"[{origin_name}] ↓ {get_size(speed_recv)}/s")
                self._log(f"[{origin_name}] Disk R {get_size(speed_read)}/s W {get_size(speed_write)}/s")

                # Attivo solo se scarica o scrive su disco
                active = (
                    speed_recv > 600 * 1024 or         # 600 KB/s
                    speed_write > 20 * 1024 * 1024     # 20 MB/s
                )

                now = time.time()
                if active:
                    last_active_time = now

                self.current_status = {
                    "launcher": origin_name,
                    "pid": proc.pid,
                    "speed_recv": speed_recv,
                    "speed_read": speed_read,
                    "speed_write": speed_write,
                    "inactive_for": int(now - last_active_time),
                }

                self.launcher_status[origin_name] = {
                    "download": downloaded_total,
                    "status": "in_progress"
                }

                if now - last_active_time > self.inactivity_timeout:
                    self._log(f"{name} inattivo per {self.inactivity_timeout}s. Chiusura...")
                    self._terminate_process(proc)
                    break

            except psutil.NoSuchProcess:
                self._log(f"{name} terminato manualmente.")
                break

            time.sleep(1)

        self.launcher_status[origin_name]["status"] = "done"
        proc.wait()

    def _terminate_process(self, process: subprocess.Popen):
        try:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

        for _ in range(10):
            if process.poll() is not None:
                break
            time.sleep(1)
