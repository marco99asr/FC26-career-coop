# FC26 Career Coop - Carriera Cooperativa Online

![FC26 Career Coop](https://img.shields.io/badge/Game-FC26%20Career%20Coop-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-yellow)

## 🎯 Obiettivo del Progetto

**FC26 Career Coop** è un tool innovativo che permette di giocare la modalità **carriera cooperativa** di FC26 da remoto, trasformando l'esperienza locale in un'avventura online condivisa.

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
│ • FC26 Process  │                   │ • FC26 Process  │
│ • Controller 1  │                   │ • Controller 2  │
│ • Memoria Sync  │                   │ • Memoria Apply │
└─────────────────┘                   └─────────────────┘
</pre>

### Flusso di Sincronizzazione

1. **Avvio Identico**: Entrambi i processi FC26 partono identici
2. **Snapshot Iniziale**: Il master invia lo stato memoria completo
3. **Delta Sync**: Solo i cambiamenti vengono trasmessi
4. **Input Bidirezionali**: Controller locali iniettati nel gioco remoto

## 📋 Requisiti di Sistema

### Software Richiesto
- **FC26** (versione identica su entrambi i PC)
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
    game_path="C:/Program Files/FC26/FC26.exe"
)
server.start()
```
### client_slave.py  
```py
client = FCClientSlave(
    broker_ip="192.168.1.100",  # IP del broker MQTT
    game_path="C:/Program Files/FC26/FC26.exe"
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
Eventuali porte del gioco: Consulta documentazione FC26<br>

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
✅ Copie Legittime: Richiede FC26 originale <br>
⚠️ Firewall: Configura appropriatamente le porte <br>
⚠️ Anti-Cheat: Usa solo in modalità offline/carriera <br>

### 📁 Struttura del Progetto
```text
FC26-career-coop/
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
Questo progetto è fornito a scopo educativo. Gli utenti sono responsabili dell'uso conforme ai termini di licenza di FC26.

### ⚠️ Disclaimer
<pre>
Nessuna Affiliazione o Approvazione
Questo progetto "FC26 Career Coop" è un tool di terze parti sviluppato indipendentemente 
e NON è affiliato, approvato, sponsorizzato o supportato in alcun modo da:
- Electronic Arts Inc.
- EA Sports
- FIFA o qualsiasi sua entità correlata
- Qualsiasi detentore di diritti di proprietà intellettuale correlato a FC26
"FC26", "EA Sports", "FIFA" e tutti i marchi correlati sono proprietà dei rispettivi 
titolari. Tutti i diritti riservati.


Scopo Educativo e di Ricerca
Questo software è fornito ESCLUSIVAMENTE per scopi educativi, di ricerca e 
di interoperabilità tecnica. L'obiettivo è consentire a utenti che possiedono 
legalmente una copia del gioco di estendere funzionalità esistenti in modalità 
non supportate ufficialmente.
NON è destinato a:
- Violare diritti d'autore o di proprietà intellettuale
- Consentire la pirateria software
- Eludere sistemi di protezione o anti-cheat
- Utilizzare il gioco senza possedere una copia legittima


Responsabilità dell'Utente
L'utente finale è l'unico responsabile per:
- Possedere una copia legittima e legalmente acquistata di FC26
- Utilizzare il software in conformità con i Termini di Servizio di EA
- Qualsiasi conseguenza derivante dall'uso di questo tool
- Violazioni dei diritti di proprietà intellettuale
- Problemi tecnici causati dall'uso del software
Gli sviluppatori di questo progetto NON sono responsabili per:
- Ban, sospensioni o altre azioni intraprese da EA
- Danni al software o all'hardware
- Perdita di dati o account
- Violazioni dei ToS commesse dagli utenti


Limitazioni Tecniche e Rischi
AVVERTENZE TECNICHE:
- Questo tool potrebbe violare i Termini di Servizio di FC26
- L'uso potrebbe risultare in ban o sospensioni dell'account
- Non garantiamo compatibilità con aggiornamenti futuri
- Il software è fornito "COSÌ COM'È" senza garanzie di alcun tipo
- Potrebbero verificarsi instabilità o malfunzionamenti


Conformità Legale
Gli utenti sono tenuti a:
- Utilizzare solo copie legalmente acquistate del gioco
- Rispettare tutte le leggi sul copyright applicabili
- Utilizzare il tool solo per sessioni private tra amici
- Non utilizzare per scopi commerciali o di lucro
- Disporre di tutte le licenze necessarie per il software
IN NESSUN CASO gli sviluppatori saranno responsabili per danni diretti, 
indiretti, incidentali o consequenziali derivanti dall'uso di questo software.


Raccomandazioni per l'Uso Sicuro
Per ridurre i rischi:
- Utilizza account secondari non collegati al tuo account principale
- Gioca solo in sessioni private con persone fidate
- Non utilizzare in combinazione con altri mod o cheat
- Monitora lo stato del tuo account EA regolarmente
- Interrompi l'uso immediatamente in caso di problemi
</pre>