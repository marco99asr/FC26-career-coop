# server_master.py
import pymem
import paho.mqtt.client as mqtt
import json
import threading
import time
import subprocess
import psutil
from collections import defaultdict
import struct

class FCServerMaster:
    def __init__(self, broker_ip="localhost", game_path="fc26.exe"):
        self.broker_ip = broker_ip
        self.game_path = game_path
        self.pm = None
        self.game_pid = None
        
        # Mappa memoria e stati
        self.memory_regions = []
        self.memory_snapshot = {}
        self.dirty_pages = set()
        self.page_size = 4096
        
        # Input
        self.local_inputs = {}
        self.remote_inputs = {}
        
        # Configurazione MQTT
        self.client = mqtt.Client("FC26_Master")
        self.setup_mqtt()
        
        # Sincronizzazione
        self.sync_interval = 0.016  # 60fps
        self.input_interval = 0.008  # 120Hz
        self.running = True
        
    def setup_mqtt(self):
        """Configurazione MQTT Master"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_ip, 1883, 60)
        
        # Topic configurazione
        self.topics = {
            'memory_delta': 'fc26/master/memory_delta',
            'input_from_client': 'fc26/client/input',
            'input_to_client': 'fc26/master/input',
            'control': 'fc26/control'
        }
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"✅ Master connesso al broker MQTT")
        # Iscrizione agli input del client
        self.client.subscribe(self.topics['input_from_client'])
        self.client.subscribe(self.topics['control'])
        
    def on_message(self, client, userdata, msg):
        """Gestione messaggi in arrivo"""
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == self.topics['input_from_client']:
                # Input dal client remoto (Controller 2)
                self.remote_inputs = payload['inputs']
                self.inject_remote_inputs()
                
            elif msg.topic == self.topics['control']:
                # Messaggi di controllo
                if payload.get('command') == 'client_ready':
                    print("🔄 Client pronto, avvio sincronizzazione...")
                    self.send_initial_snapshot()
                    
        except Exception as e:
            print(f"❌ Errore messaggio MQTT: {e}")
    
    def launch_game(self):
        """Avvia il processo di gioco identico"""
        try:
            print("🎮 Avvio FC26...")
            process = subprocess.Popen([self.game_path])
            self.game_pid = process.pid
            time.sleep(5)  # Attendi caricamento
            
            # Connetti alla memoria del gioco
            self.pm = pymem.Pymem()
            self.pm.open_process_from_id(self.game_pid)
            
            print(f"✅ Gioco avviato (PID: {self.game_pid})")
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio gioco: {e}")
            return False
    
    def identify_memory_regions(self):
        """Identifica le regioni di memoria del gioco"""
        print("🔍 Identificazione regioni memoria...")
        
        # Filtra solo moduli del gioco
        for module in self.pm.list_modules():
            if any(name in module.name.lower() for name in ['fc26', 'game', 'main']):
                print(f"📦 Modulo trovato: {module.name}")
                
                base_addr = module.lpBaseOfDll
                size = module.SizeOfImage
                
                # Aggiungi tutte le pagine del modulo
                for page_start in range(base_addr, base_addr + size, self.page_size):
                    self.memory_regions.append(page_start)
                    
        print(f"📍 Trovate {len(self.memory_regions)} pagine di memoria")
    
    def create_initial_snapshot(self):
        """Crea snapshot iniziale di tutta la memoria"""
        print("📸 Creazione snapshot iniziale...")
        
        for page_addr in self.memory_regions:
            try:
                data = self.pm.read_bytes(page_addr, self.page_size)
                self.memory_snapshot[page_addr] = data
            except Exception:
                continue  # Salva pagine non leggibili
                
        print(f"✅ Snapshot creato: {len(self.memory_snapshot)} pagine")
    
    def send_initial_snapshot(self):
        """Invia snapshot completo al client"""
        print("🚀 Invio snapshot iniziale al client...")
        
        snapshot_data = {
            'type': 'full_snapshot',
            'timestamp': time.time(),
            'pages': {}
        }
        
        # Invia a blocchi per non saturare MQTT
        pages_sent = 0
        for page_addr, data in self.memory_snapshot.items():
            snapshot_data['pages'][hex(page_addr)] = data.hex()
            pages_sent += 1
            
            # Invia ogni 100 pagine
            if pages_sent % 100 == 0:
                self.client.publish(
                    self.topics['memory_delta'], 
                    json.dumps(snapshot_data)
                )
                snapshot_data['pages'] = {}
                time.sleep(0.01)
        
        # Invia pagine rimanenti
        if snapshot_data['pages']:
            self.client.publish(
                self.topics['memory_delta'], 
                json.dumps(snapshot_data)
            )
        
        print("✅ Snapshot iniziale inviato")
    
    def memory_sync_loop(self):
        """Loop principale sincronizzazione memoria"""
        print("🔄 Avvio sincronizzazione memoria...")
        
        while self.running:
            try:
                changes = self.detect_memory_changes()
                if changes:
                    self.send_memory_changes(changes)
                    
                time.sleep(self.sync_interval)
                
            except Exception as e:
                print(f"❌ Errore sync memoria: {e}")
                time.sleep(0.1)
    
    def detect_memory_changes(self):
        """Rileva cambiamenti nella memoria"""
        changes = {}
        
        for page_addr in self.memory_regions:
            try:
                current_data = self.pm.read_bytes(page_addr, self.page_size)
                old_data = self.memory_snapshot.get(page_addr)
                
                if old_data and current_data != old_data:
                    # Trova byte modificati
                    byte_changes = []
                    for i, (old_byte, new_byte) in enumerate(zip(old_data, current_data)):
                        if old_byte != new_byte:
                            byte_changes.append((i, new_byte))
                    
                    if byte_changes:
                        changes[page_addr] = {
                            'changes': byte_changes,
                            'full_size': len(current_data)
                        }
                        self.memory_snapshot[page_addr] = current_data
                        
            except Exception:
                continue
                
        return changes
    
    def send_memory_changes(self, changes):
        """Invia delta changes al client"""
        delta_data = {
            'type': 'delta_changes',
            'timestamp': time.time(),
            'changes': {}
        }
        
        for page_addr, change_info in changes.items():
            delta_data['changes'][hex(page_addr)] = change_info
        
        self.client.publish(
            self.topics['memory_delta'], 
            json.dumps(delta_data)
        )
    
    def input_capture_loop(self):
        """Loop cattura input locale (Controller 1)"""
        print("🎮 Avvio cattura input locale...")
        
        while self.running:
            try:
                # Cattura input controller locale
                local_inputs = self.capture_local_inputs()
                
                if local_inputs != self.local_inputs:
                    self.local_inputs = local_inputs
                    
                    # Invia input al client
                    input_data = {
                        'controller_id': 1,  # Master = Controller 1
                        'inputs': local_inputs,
                        'timestamp': time.time()
                    }
                    self.client.publish(
                        self.topics['input_to_client'],
                        json.dumps(input_data)
                    )
                    
                time.sleep(self.input_interval)
                
            except Exception as e:
                print(f"❌ Errore cattura input: {e}")
                time.sleep(0.1)
    
    def capture_local_inputs(self):
        """Cattura input dal controller locale"""
        # IMPLEMENTA: Usa pywin32, pygame, o altra libreria
        # Esempio struttura:
        return {
            'left_x': 0.0,      # -1.0 to 1.0
            'left_y': 0.0,
            'right_x': 0.0,
            'right_y': 0.0,
            'a_button': False,
            'b_button': False,
            'x_button': False,
            'y_button': False,
            'l_trigger': 0.0,   # 0.0 to 1.0
            'r_trigger': 0.0,
            'l_bumper': False,
            'r_bumper': False
        }
    
    def inject_remote_inputs(self):
        """Inietta input remoti nel gioco (Controller 2)"""
        # IMPLEMENTA: Scrivi input nella memoria del gioco
        # per il controller 2 remoto
        pass
    
    def start(self):
        """Avvia tutto il sistema master"""
        print("🚀 Avvio Server Master FC26...")
        
        if not self.launch_game():
            return False
        
        self.identify_memory_regions()
        self.create_initial_snapshot()
        
        # Avvia thread
        threads = [
            threading.Thread(target=self.memory_sync_loop, daemon=True),
            threading.Thread(target=self.input_capture_loop, daemon=True),
        ]
        
        for thread in threads:
            thread.start()
        
        print("✅ Master pronto in attesa del client...")
        self.client.loop_forever()
        
        return True

if __name__ == "__main__":
    server = FCServerMaster(broker_ip="localhost")  # Cambia con IP broker
    server.start()