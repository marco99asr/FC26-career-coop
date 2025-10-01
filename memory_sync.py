# memory_sync.py
import pymem
import json
import time
import threading
from collections import defaultdict
import struct
import psutil

class MemorySyncEngine:
    """Motore di sincronizzazione memoria per FC24 Career Coop"""
    
    def __init__(self, process_handler, role="master"):
        self.pm = process_handler
        self.role = role
        self.memory_regions = []
        self.memory_snapshot = {}
        self.dirty_pages = set()
        self.page_size = 4096
        
        # Statistiche e monitoring
        self.sync_stats = {
            'total_changes': 0,
            'bytes_sent': 0,
            'sync_count': 0,
            'last_sync': 0
        }
        
        # Configurazione
        self.sync_interval = 0.016  # 60fps
        self.max_page_size = 1024 * 1024  # 1MB max per pagina
        self.compression_enabled = True
        
    def identify_game_memory(self):
        """Identifica le regioni di memoria critiche del gioco"""
        print("🔍 Scansione memoria gioco...")
        
        try:
            # Cerca moduli principali del gioco
            target_modules = ['fc24', 'game', 'main', 'engine']
            found_modules = []
            
            for module in self.pm.list_modules():
                module_name = module.name.lower()
                if any(target in module_name for target in target_modules):
                    print(f"📦 Trovato modulo: {module.name} (0x{module.lpBaseOfDll:X})")
                    found_modules.append(module)
                    
                    # Aggiungi tutte le pagine del modulo
                    base_addr = module.lpBaseOfDll
                    size = module.SizeOfImage
                    
                    for page_start in range(base_addr, base_addr + size, self.page_size):
                        if page_start not in self.memory_regions:
                            self.memory_regions.append(page_start)
            
            # Se non trova moduli specifici, usa euristica
            if not found_modules:
                self._heuristic_memory_scan()
            else:
                print(f"✅ Identificate {len(self.memory_regions)} pagine di memoria")
                
        except Exception as e:
            print(f"❌ Errore scansione memoria: {e}")
            self._heuristic_memory_scan()
    
    def _heuristic_memory_scan(self):
        """Scansione euristica delle regioni di memoria"""
        print("🔄 Scansione euristica memoria...")
        
        try:
            process = psutil.Process(self.pm.process_id)
            memory_maps = process.memory_maps()
            
            for memory_map in memory_maps:
                # Filtra regioni interessanti (eseguibili, scrivibili)
                perms = memory_map.perms
                path = memory_map.path.lower()
                
                # Prendi regioni RW o RWX che non siano stack/heap generici
                if ('r' in perms and 'w' in perms) and ('stack' not in path):
                    start_addr = int(memory_map.addr.split('-')[0], 16)
                    end_addr = int(memory_map.addr.split('-')[1], 16)
                    size = end_addr - start_addr
                    
                    # Aggiungi pagine di dimensioni ragionevoli
                    if size <= self.max_page_size:
                        for page in range(start_addr, end_addr, self.page_size):
                            if page not in self.memory_regions:
                                self.memory_regions.append(page)
            
            print(f"📍 Trovate {len(self.memory_regions)} pagine con euristica")
            
        except Exception as e:
            print(f"❌ Errore scansione euristica: {e}")
    
    def create_initial_snapshot(self):
        """Crea snapshot iniziale di tutta la memoria monitorata"""
        print("📸 Creazione snapshot iniziale...")
        
        successful_pages = 0
        for page_addr in self.memory_regions:
            try:
                data = self.pm.read_bytes(page_addr, self.page_size)
                self.memory_snapshot[page_addr] = data
                successful_pages += 1
            except Exception as e:
                # Rimuovi pagine non leggibili
                if page_addr in self.memory_regions:
                    self.memory_regions.remove(page_addr)
                continue
        
        print(f"✅ Snapshot creato: {successful_pages}/{len(self.memory_regions)} pagine")
        return successful_pages
    
    def detect_memory_changes(self):
        """Rileva cambiamenti nella memoria rispetto allo snapshot"""
        changes = {}
        
        for page_addr in self.memory_regions:
            try:
                current_data = self.pm.read_bytes(page_addr, self.page_size)
                old_data = self.memory_snapshot.get(page_addr)
                
                if old_data is None:
                    # Prima volta che leggiamo questa pagina
                    self.memory_snapshot[page_addr] = current_data
                    continue
                
                if current_data != old_data:
                    # Calcola delta efficiente
                    delta_changes = self._calculate_delta(old_data, current_data)
                    
                    if delta_changes:
                        changes[page_addr] = {
                            'changes': delta_changes,
                            'full_size': len(current_data),
                            'timestamp': time.time()
                        }
                        
                        # Aggiorna snapshot
                        self.memory_snapshot[page_addr] = current_data
                        
                        # Statistiche
                        self.sync_stats['total_changes'] += len(delta_changes)
                        self.sync_stats['bytes_sent'] += len(delta_changes) * 2  # approx
                        
            except Exception as e:
                # Page non più accessibile, rimuovi
                if page_addr in self.memory_regions:
                    self.memory_regions.remove(page_addr)
                if page_addr in self.memory_snapshot:
                    del self.memory_snapshot[page_addr]
                continue
        
        self.sync_stats['sync_count'] += 1
        self.sync_stats['last_sync'] = time.time()
        
        return changes
    
    def _calculate_delta(self, old_data, new_data):
        """Calcola i byte effettivamente cambiati"""
        changes = []
        
        # Assicurati che le lunghezze siano uguali
        min_len = min(len(old_data), len(new_data))
        
        for i in range(min_len):
            if old_data[i] != new_data[i]:
                changes.append((i, new_data[i]))
        
        return changes
    
    def apply_memory_changes(self, changes_data):
        """Applica cambiamenti di memoria ricevuti"""
        applied_changes = 0
        
        try:
            change_type = changes_data.get('type', 'delta_changes')
            
            if change_type == 'full_snapshot':
                applied_changes = self._apply_full_snapshot(changes_data)
            elif change_type == 'delta_changes':
                applied_changes = self._apply_delta_changes(changes_data)
            else:
                print(f"❌ Tipo di cambio sconosciuto: {change_type}")
                
        except Exception as e:
            print(f"❌ Errore applicazione cambiamenti: {e}")
        
        return applied_changes
    
    def _apply_full_snapshot(self, snapshot_data):
        """Applica uno snapshot completo"""
        applied_pages = 0
        
        for page_addr_hex, page_data_hex in snapshot_data.get('pages', {}).items():
            try:
                page_addr = int(page_addr_hex, 16)
                page_data = bytes.fromhex(page_data_hex)
                
                # Scrivi nella memoria
                self.pm.write_bytes(page_addr, page_data, len(page_data))
                
                # Aggiorna snapshot locale
                self.memory_snapshot[page_addr] = page_data
                
                # Aggiungi alle regioni se non presente
                if page_addr not in self.memory_regions:
                    self.memory_regions.append(page_addr)
                
                applied_pages += 1
                
            except Exception as e:
                print(f"⚠️ Errore scrittura pagina {page_addr_hex}: {e}")
        
        print(f"✅ Snapshot applicato: {applied_pages} pagine")
        return applied_pages
    
    def _apply_delta_changes(self, delta_data):
        """Applica cambiamenti delta"""
        applied_changes = 0
        
        for page_addr_hex, change_info in delta_data.get('changes', {}).items():
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
                        applied_changes += 1
                
                # Scrivi dati modificati
                self.pm.write_bytes(page_addr, bytes(current_data), len(current_data))
                
                # Aggiorna snapshot locale
                self.memory_snapshot[page_addr] = bytes(current_data)
                
            except Exception as e:
                print(f"⚠️ Errore applicazione delta {page_addr_hex}: {e}")
        
        return applied_changes
    
    def optimize_memory_regions(self, critical_addresses=None):
        """Ottimizza le regioni di memoria per sincronizzazione"""
        if critical_addresses:
            # Aggiungi indirizzi critici specifici
            for addr in critical_addresses:
                page_addr = (addr // self.page_size) * self.page_size
                if page_addr not in self.memory_regions:
                    self.memory_regions.append(page_addr)
        
        # Rimuovi duplicati e ordina
        self.memory_regions = sorted(set(self.memory_regions))
        
        print(f"🔧 Regioni ottimizzate: {len(self.memory_regions)} pagine")
    
    def get_sync_stats(self):
        """Restituisce statistiche di sincronizzazione"""
        stats = self.sync_stats.copy()
        stats['monitored_pages'] = len(self.memory_regions)
        stats['active_pages'] = len(self.memory_snapshot)
        
        if stats['sync_count'] > 0:
            stats['avg_changes_per_sync'] = stats['total_changes'] / stats['sync_count']
        else:
            stats['avg_changes_per_sync'] = 0
            
        return stats
    
    def cleanup(self):
        """Pulizia risorse"""
        self.memory_regions.clear()
        self.memory_snapshot.clear()
        self.dirty_pages.clear()


class MemorySignatureScanner:
    """Scanner per firme di memoria specifiche di FC24"""
    
    def __init__(self, process_handler):
        self.pm = process_handler
        self.signatures = {
            'player_data': [
                b'\x48\x8B\x05\x00\x00\x00\x00\x48\x85\xC0\x74\x00\x8B',  # Esempio
            ],
            'game_state': [
                b'\x40\x53\x48\x83\xEC\x00\x48\x8B\x05\x00\x00\x00\x00',
            ],
            'input_handler': [
                b'\x48\x8B\x0D\x00\x00\x00\x00\xE8\x00\x00\x00\x00\x84\xC0',
            ]
        }
    
    def scan_for_signatures(self):
        """Scansiona le firme di memoria conosciute"""
        found_addresses = {}
        
        for sig_name, patterns in self.signatures.items():
            for pattern in patterns:
                address = self._pattern_scan(pattern)
                if address:
                    found_addresses[sig_name] = address
                    print(f"🎯 Trovata firma {sig_name}: 0x{address:X}")
                    break
        
        return found_addresses
    
    def _pattern_scan(self, pattern):
        """Scansiona un pattern nella memoria"""
        try:
            # Implementazione semplificata pattern scanning
            modules = self.pm.list_modules()
            
            for module in modules:
                if any(name in module.name.lower() for name in ['fc24', 'game']):
                    base_address = module.lpBaseOfDll
                    module_size = module.SizeOfImage
                    
                    # Leggi tutto il modulo (attenzione: potrebbe essere grande)
                    try:
                        module_data = self.pm.read_bytes(base_address, min(module_size, 50 * 1024 * 1024))  # Max 50MB
                        
                        # Cerca pattern
                        for i in range(len(module_data) - len(pattern) + 1):
                            match = True
                            for j, byte in enumerate(pattern):
                                if byte != 0x00 and byte != module_data[i + j]:
                                    match = False
                                    break
                            
                            if match:
                                return base_address + i
                                
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"❌ Errore pattern scanning: {e}")
        
        return None


# Utility functions
def memory_address_to_page(address, page_size=4096):
    """Converte un indirizzo di memoria in indirizzo di pagina"""
    return (address // page_size) * page_size

def validate_memory_access(process_handler, address, size=4):
    """Valida se un'area di memoria è accessibile"""
    try:
        # Prova a leggere un byte
        process_handler.read_bytes(address, size)
        return True
    except:
        return False

def get_memory_region_info(process_handler, address):
    """Ottiene informazioni su una regione di memoria"""
    try:
        process = psutil.Process(process_handler.process_id)
        for memory_map in process.memory_maps():
            start_addr = int(memory_map.addr.split('-')[0], 16)
            end_addr = int(memory_map.addr.split('-')[1], 16)
            
            if start_addr <= address < end_addr:
                return {
                    'address_range': memory_map.addr,
                    'permissions': memory_map.perms,
                    'path': memory_map.path,
                    'size': end_addr - start_addr
                }
    except:
        pass
    
    return None