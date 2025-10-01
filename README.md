# FC24 Career Coop - Carriera Cooperativa Online

![FC24 Career Coop](https://img.shields.io/badge/Game-FC24%20Career%20Coop-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow)

## 🎯 Obiettivo del Progetto

**FC24 Career Coop** è un tool innovativo che permette di giocare la modalità **carriera cooperativa** di FC24 da remoto, trasformando l'esperienza locale in un'avventura online condivisa.

> ⚠️ **Nota Importante**: Questo progetto è creato a scopo educativo e di ricerca. Utilizzalo solo se possiedi una copia legittima del gioco.

## 🚀 Caratteristiche Principali

- **🎮 Carriera Coop Online**: Gioca la carriera cooperativa con un amico da remoto
- **🔄 Sincronizzazione Real-Time**: Memoria del gioco sincronizzata istantaneamente
- **👥 Doppio Controller Remoti**: Entrambi i giocatori hanno il proprio controller
- **📡 Architettura Client-Server**: Configurazione master-slave per stabilità
- **⚡ Bassa Latenza**: Ottimizzato per esperienza di gioco fluida

## 🛠️ Come Funziona

### Architettura Tecnica
<pre>
┌─────────────────┐    MQTT Broker    ┌─────────────────┐
│  MASTER Host    │ ◄───────────────► │   CLIENT Slave  │
│                 │                   │                 |
│ • FC24 Process  │                   │ • FC24 Process  │
│ • Controller 1  │                   │ • Controller 2  │
│ • Memoria Sync  │                   │ • Memoria Apply │
└─────────────────┘                   └─────────────────┘
</pre>

### Flusso di Sincronizzazione

1. **Avvio Identico**: Entrambi i processi FC24 partono identici
2. **Snapshot Iniziale**: Il master invia lo stato memoria completo
3. **Delta Sync**: Solo i cambiamenti vengono trasmessi
4. **Input Bidirezionali**: Controller locali iniettati nel gioco remoto

## 📋 Requisiti di Sistema

### Software Richiesto
- **FC24** (versione identica su entrambi i PC)
- **Python 3.8+**
- **Broker MQTT** (Mosquitto raccomandato)
- **Stessa configurazione gioco** su entrambe le macchine

### Librerie Python
```bash
pip install pymem paho-mqtt psutil pygame
# Installazione Mosquitto (Windows)
# Scarica da: https://mosquitto.org/download/

# Installazione Mosquitto (Linux)
sudo apt-get install mosquitto mosquitto-clients

# Avvio broker
mosquitto -c mosquitto.conf
```

### server_master.py
```py
server = FCServerMaster(
    broker_ip="192.168.1.100",  # IP del broker MQTT
    game_path="C:/Program Files/FC24/fc24.exe"
)
server.start()
```
### client_slave.py  
```py
client = FCClientSlave(
    broker_ip="192.168.1.100",  # IP del broker MQTT
    game_path="C:/Program Files/FC24/fc24.exe"
)
client.start()
```

## 🎮 Utilizzo
Sequenza di Avvio Corretta
Avvia Broker MQTT

```bash
mosquitto -c mosquitto.conf
```
Avvia il MASTER per primo
```bash
python server_master.py
```
Avvia il CLIENT dopo

```bash
python client_slave.py
```
Aspetta sincronizzazione iniziale <br>
Il master invierà lo snapshot completo <br>
Il client applicherà lo stato iniziale <br>
Gioca!<br>
Entrambi i controller funzionano in remoto<br>
La partita è perfettamente sincronizzata<br>

## ⚙️ Configurazione Avanzata
Ottimizzazione Latenza

### Modifica questi valori in base alla tua connessione
```py
self.sync_interval = 0.016    # 60fps per memoria
self.input_interval = 0.008   # 120Hz per input
```

### Port Forwarding (Gioco da Internet)
Porte da aprire sul router: <br>
MQTT: 1883 (TCP) <br>
Eventuali porte del gioco: Consulta documentazione FC24<br>

### 🐛 Risoluzione Problemi
 Problemi Comuni e Soluzioni
<pre>
❌Problema	                   Soluzione
❌ Connessione MQTT fallita	   Verifica IP broker e firewall
🔄 Sincronizzazione lenta	    Riduci sync_interval
🎮 Input non funzionanti	    Verifica configurazione controller
💾 Memory access error	        Esegui come Amministratore
</pre>
### Log di Debug
Abilita i log dettagliati modificando:

```py
import logging
logging.basicConfig(level=logging.DEBUG)
```
### 🔒 Considerazioni sulla Sicurezza
✅ Uso Personale: Solo per sessioni private <br>
✅ Copie Legittime: Richiede FC24 originale <br>
⚠️ Firewall: Configura appropriatamente le porte <br>
⚠️ Anti-Cheat: Usa solo in modalità offline/carriera <br>

### 📁 Struttura del Progetto
```text
fc24-career-coop/
├── server_master.py      # Host principale
├── client_slave.py       # Client remoto
├── input_manager.py      # Gestione controller
├── memory_sync.py        # Sincronizzazione memoria
├── config.json           # Configurazioni
└── README.md
```

### 🤝 Contribuire
Le contribuzioni sono benvenute! Aree di miglioramento:<br>
Migliore gestione errori<br>
Interfaccia grafica di configurazione<br>
Supporto per più giochi<br>
Ottimizzazioni di rete<br>

### 📄 Licenza
Questo progetto è fornito a scopo educativo. Gli utenti sono responsabili dell'uso conforme ai termini di licenza di FC24.

### ⚠️ Disclaimer
Questo tool non è affiliato, associato o autorizzato da Electronic Arts Inc. o dalla FIFA. "FC24" è un trademark di EA Sports. Utilizza questo software a tuo rischio.<br>
Divertiti a giocare la carriera coop con i tuoi amici da remoto! 🎉⚽<br>
Per supporto o domande, apri una issue sul repository del progetto.