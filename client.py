# client_slave.py
import pymem
import paho.mqtt.client as mqtt
import json
import threading
import time
import subprocess
import struct

class FCClientSlave:
    def __init__(self, broker_ip="localhost", game_path="fc26.exe"):
        self.broker_ip = broker_ip
        self.game_path = game_path
        self.pm = None
        self.game_pid = None
        
        # Memoria
        self.memory_snapshot = {}
        self.memory_regions_map = {}
        
        # Input
        self.local_inputs = {}
        self.remote_inputs = {}
        
        # Configurazione MQTT
        self.client = mqtt.Client("FC26_Client")
        self.setup_mqtt()
        
        # Sincronizzazione
        self.running = True
        self.ready = False
        
    def setup_mqtt(self):
        """Configurazione MQTT Client"""
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(self.broker_ip, 1883, 60)
        
        self.topics = {
            'memory_delta': 'fc26/master/memory_delta',
            'input_from_master': 'fc26/master/input',
            'input_to_master': 'fc26/client/input',
            'control': 'fc26/control'
        }
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"✅ Client connesso al broker MQTT")
        # Iscrizione ai topic del master
        self.client.subscribe(self.topics['memory_delta'])
        self.client.subscribe(self.topics['input_from_master'])
        
    def on_message(self, client, userdata, msg):
        """Gestione messaggi dal master"""
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == self.topics['memory_delta']:
                self.process_memory_update(payload)
                
            elif msg.topic == self.topics['input_from_master']:
                # Input dal master (Controller 1 remoto)
                self.remote_inputs = payload['inputs']
                self.inject_remote_inputs()
                
        except Exception as e:
            print(f"❌ Errore messaggio MQTT: {e}")
    
    def launch_game(self):
        """Avvia processo gioco identico"""
        try:
            print("🎮 Avvio FC26 (Client)...")
            process = subprocess.Popen([self.game_path])
            self.game_pid = process.pid
            time.sleep(5)  # Attendi caricamento
            
            # Connetti alla memoria
            self.pm = pymem.Pymem()
            self.pm.open_process_from_id(self.game_pid)
            
            print(f"✅ Gioco client avviato (PID: {self.game_pid})")
            
            # Notifica al master che siamo pronti
            ready_msg = {'command': 'client_ready'}
            self.client.publish(
                self.topics['control'],
                json.dumps(ready_msg)
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Errore avvio gioco client: {e}")
            return False
    
    def process_memory_update(self, update_data):
        """Processa aggiornamenti memoria dal master"""
        update_type = update_data.get('type')
        
        if update_type == 'full_snapshot':
            self.apply_full_snapshot(update_data)
            self.ready = True
            print("✅ Snapshot applicato - Sincronizzato!")
            
        elif update_type == 'delta_changes':
            if self.ready:
                self.apply_delta_changes(update_data)
    
    def apply_full_snapshot(self, snapshot_data):
        """Applica snapshot completo dal master"""
        print("📥 Ricezione snapshot completo...")
        
        pages_applied = 0
        for page_addr_hex, page_data_hex in snapshot_data['pages'].items():
            try:
                page_addr = int(page_addr_hex, 16)
                page_data = bytes.fromhex(page_data_hex)
                
                # Scrivi nella memoria
                self.pm.write_bytes(page_addr, page_data, len(page_data))
                self.memory_snapshot[page_addr] = page_data
                pages_applied += 1
                
            except Exception as e:
                print(f"⚠️ Errore scrittura pagina {page_addr_hex}: {e}")
        
        print(f"✅ Snapshot applicato: {pages_applied} pagine")
    
    def apply_delta_changes(self, delta_data):
        """Applica cambiamenti delta alla memoria locale"""
        changes = delta_data.get('changes', {})
        
        for page_addr_hex, change_info in changes.items():
            try:
                page_addr = int(page_addr_hex, 16)
                byte_changes = change_info['changes']
                
                # Leggi dati correnti
                current_data = bytearray(
                    self.pm.read_bytes(page_addr, change_info['full_size'])
                )
                
                # Applica cambiamenti
                for offset, new_byte in byte_changes:
                    if offset < len(current_data):
                        current_data[offset] = new_byte
                
                # Scrivi dati modificati
                self.pm.write_bytes(page_addr, bytes(current_data), len(current_data))
                self.memory_snapshot[page_addr] = bytes(current_data)
                
            except Exception as e:
                print(f"⚠️ Errore applicazione delta: {e}")
    
    def input_capture_loop(self):
        """Loop cattura input locale (Controller 2)"""
        print("🎮 Avvio cattura input client...")
        
        while self.running:
            try:
                if not self.ready:
                    time.sleep(0.1)
                    continue
                
                # Cattura input controller locale
                local_inputs = self.capture_local_inputs()
                
                if local_inputs != self.local_inputs:
                    self.local_inputs = local_inputs
                    
                    # Invia input al master
                    input_data = {
                        'controller_id': 2,  # Client = Controller 2
                        'inputs': local_inputs,
                        'timestamp': time.time()
                    }
                    self.client.publish(
                        self.topics['input_to_master'],
                        json.dumps(input_data)
                    )
                    
                time.sleep(0.008)  # 120Hz
                
            except Exception as e:
                print(f"❌ Errore cattura input client: {e}")
                time.sleep(0.1)
    
    def capture_local_inputs(self):
        """Cattura input dal controller locale del client"""
        # IMPLEMENTA: Stessa struttura del master
        return {
            'left_x': 0.0,
            'left_y': 0.0,
            'right_x': 0.0,
            'right_y': 0.0,
            'a_button': False,
            'b_button': False,
            'x_button': False,
            'y_button': False,
            'l_trigger': 0.0,
            'r_trigger': 0.0,
            'l_bumper': False,
            'r_bumper': False
        }
    
    def inject_remote_inputs(self):
        """Inietta input remoti nel gioco (Controller 1 dal master)"""
        # IMPLEMENTA: Scrivi input nella memoria del gioco
        # per il controller 1 remoto
        pass
    
    def start(self):
        """Avvia tutto il sistema client"""
        print("🚀 Avvio Client Slave FC26...")
        
        if not self.launch_game():
            return False
        
        # Avvia thread input
        input_thread = threading.Thread(target=self.input_capture_loop, daemon=True)
        input_thread.start()
        
        print("✅ Client pronto in attesa sincronizzazione...")
        self.client.loop_forever()
        
        return True

if __name__ == "__main__":
    client = FCClientSlave(broker_ip="localhost")  # Cambia con IP broker
    client.start()