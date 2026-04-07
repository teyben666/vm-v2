# VM Manager - Hypervisor-Agnostic Python Management System

A complete enterprise-grade VM management system with:
- **Telegram Bot** for remote control and monitoring
- **FastAPI HTTP Server** for secure VM-Host communication
- **Guest Detector** as a Windows service for AFK monitoring and graceful shutdown
- **Hyper-V Support** (easily extensible to VirtualBox/Proxmox)
- **Anti-Tampering Features** - Heartbeat watchdog with force-kill capability

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL (Internet)                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Telegram Bot API (Outbound only, no port forwarding)     │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────────────┐
        │         HOST CONTROLLER (Windows)        │
        │  - Telegram Bot                          │
        │  - FastAPI Server (192.168.1.100:8000)   │
        │  - SQLite Database                       │
        │  - Watchdog Loop                         │
        │  - Hyper-V Manager                       │
        └──────────────────────────────────────────┘
                       │
           ┌───────────┼───────────┐
           │ Bridged Network (192.168.1.x)
           ▼           ▼           ▼
        ┌──────┐   ┌──────┐   ┌──────┐
        │ VM-1 │   │ VM-2 │   │ VM-3 │
        │      │   │      │   │      │
        │Guest │   │Guest │   │Guest │
        │Det.  │   │Det.  │   │Det.  │
        └──────┘   └──────┘   └──────┘
        (Hyper-V)  (Hyper-V)  (Hyper-V)
```

## 📋 Key Features

### Host Controller
- **Telegram Bot Commands** - `/start_vm`, `/stop_vm`, `/dashboard`, Admin controls
- **FastAPI HTTP API** - Receives heartbeats from guest detectors over LAN
- **SQLite Database** - User management, VM registration, audit logging
- **Watchdog** - Monitors heartbeat gaps, triggers force-kill if detector dies
- **Hyper-V Integration** - PowerShell commands for VM start/stop
- **Role-Based Access** - Admin/User/Pending roles with banning

### Guest Detector (Windows Service)
- **AFK Detection** - Windows API for keyboard/mouse monitoring
- **Parsec Integration** - Detects active remote desktop sessions
- **System Metrics** - Reports memory & CPU usage with each heartbeat
- **HTTP Heartbeat** - 60-second heartbeat with status reporting
- **Graceful Shutdown** - 5-minute warning before forced termination
- **Auto-Shutdown** - Exits if AFK + Parsec-disconnected for 1 hour
- **System Service** - Runs as LocalSystem via NSSM (unkillable)

## 🛡️ Monitoring & Security Features

### Real-Time Monitoring
- **Heartbeat Watchdog** - Checks every 30 seconds for missed heartbeats
- **Timeout Detection** - If detector misses 3 heartbeats (3+ minutes) → auto-alert
- **Live Status Dashboard** - Interactive Telegram UI with VM status icons
- **Last Heartbeat Timestamp** - Know exactly when detector last checked in
- **System Metrics** - Memory & CPU usage tracked with each heartbeat

### Watchdog Alerts
When detector becomes unresponsive:
```
Missed Heartbeat
      ↓
Watchdog Alert to Admin
      ↓
VM marked as offline
      ↓
Investigation possible (crashed detector? tampering?)
```

### Security Layers
1. **UUID Credentials** - Detector ID & Secret Key are unique per VM
2. **Per-Request Auth** - Every API call requires headers with valid credentials
3. **Failed Auth Counter** - After 3 failed attempts in 1 hour → lockout
4. **System Service** - Detector runs as SYSTEM (users cannot kill it)
5. **Zero Public Ports** - API only accessible on internal LAN (192.168.1.x)
6. **Telegram Bot Only** - External commands only via Telegram (no port forwarding needed)

### Interactive Dashboard
The Telegram dashboard shows:
- **Status Icons** - 🟢 online | 🔴 offline
- **Last Heartbeat** - Timestamp of last check-in
- **Assignment** - Which user controls each VM
- **Quick Actions** - Buttons to start/stop VMs directly from chat

## 🚀 Quick Start

### Prerequisites
- Windows 10/11 with Hyper-V enabled
- Python 3.10+
- Telegram bot token (get from @BotFather)
- Network with Router + Host + VMs on same LAN (e.g., 192.168.1.x)

### Step 1: Host Controller Setup

```powershell
# Navigate to host-controller
cd vm-management-system\host-controller

# Install dependencies
pip install -r requirements.txt

# Edit .env file
# - Set TELEGRAM_BOT_TOKEN
# - Set ADMIN_SECRET_TOKEN (any secure string)
# - Set HOST_LAN_IP (e.g., 192.168.1.100)

# Run the host controller
python -m src.main
```

### Step 2: Register First Admin

1. Start the Host Controller
2. In Telegram, find your bot and send: `/token <ADMIN_SECRET_TOKEN>`
3. You're now an admin!

### Step 3: Add a VM

1. Send: `/add_vm`
2. Enter the VM name (as shown in Hyper-V)
3. You'll receive:
   - `Detector_ID` (UUID)
   - `VM_SECRET_KEY` (UUID)

### Step 4: Deploy Guest Detector to VM

1. Copy `guest-detector/` folder to the VM
2. Edit `guest-detector/.env`:
   ```
   HOST_LAN_IP=192.168.1.100  (Your host's LAN IP)
   DETECTOR_ID=<from step 3>
   VM_SECRET_KEY=<from step 3>
   ```
3. Run `guest-detector\build.bat` to create executable
4. Install as service using NSSM (instructions in build output)

### Step 5: Start Managing

```
/dashboard                  - See your VMs
/start_vm <detector_id>    - Start VM
```

## 📚 Detailed Commands

### User Commands
```
/start - Show welcome
/register - Request access
/dashboard - View assigned VMs (interactive)
/start_vm <id> - Start a specific VM
/help - Show all commands
```

### Admin Commands
```
/add_vm - Create new VM registration
/delete_vm <detector_id> - Delete a registered VM
/assign <detector_id> <user_id> - Assign VM to user
/stop_vm <id> - Graceful shutdown (detector executes)
/force_stop <id> - Force shutdown (hypervisor executes)
/users - List all registered users
/ban <user_id> - Ban user
/pardon <user_id> - Unban user
/promote <user_id> - Make user admin
/token <secret> - Become admin with secret token
```

## 🔧 Configuration

### Host Controller (.env)
```
TELEGRAM_BOT_TOKEN=<your-bot-token>
ADMIN_SECRET_TOKEN=<secure-string>
HOST_LAN_IP=192.168.1.100
API_PORT=8000
DATABASE_PATH=./database.sqlite
MAX_FAILED_AUTH=3
HEARTBEAT_TIMEOUT_MINUTES=3
AFK_THRESHOLD_MINUTES=60
```

### Guest Detector (.env)
```
HOST_LAN_IP=192.168.1.100
API_PORT=8000
DETECTOR_ID=<your-detector-id>
VM_SECRET_KEY=<your-secret-key>
HEARTBEAT_INTERVAL_SECONDS=60
AFK_THRESHOLD_MINUTES=60
PARSEC_LOG_PATH=C:\\Users\\Public\\AppData\\Parsec\\log.txt
LOG_LEVEL=INFO
```

## 🔒 Security Details

### Payload Authentication
Every HTTP request includes:
```python
Headers:
  X-Detector-ID: "550e8400-e29b-41d4-a716-446655440000"
  X-VM-Secret: "abc123xyz..."
```

Bad credentials = immediate rejection + failed auth logged.

### Heartbeat Watchdog
- VM on "Online" must heartbeat every 60 seconds
- Miss 3 heartbeats (3 minutes) = security alert
- Detector assumed compromised = **Force-Kill** via hypervisor
- Admin notified via Telegram

### Graceful Shutdown Protocol
```
Admin: /stop_vm <id>
  ▼
Host: Sets VM status to "pending_shutdown" in DB
  ▼
Detector: Checks status on 60-second heartbeat
  ▼
Detector: Receives shutdown command in HTTP response
  ▼
Detector: Executes: shutdown /s /t 60 (60 second warning)
  ▼
VM: User sees "System shutting down in 60 seconds"
  ▼
VM: Clean shutdown, services stop gracefully
```

## 📊 API Endpoints

### Heartbeat (VM → Host)
```
POST /api/heartbeat
Headers: X-Detector-ID, X-VM-Secret
Body: {afk: bool, afk_duration_minutes: int, parsec_connected: bool}
Response: {status: "acknowledged", command?: "shutdown"}
```

### Alert (VM → Host)
```
POST /api/alert
Headers: X-Detector-ID, X-VM-Secret
Body: {type: "shutdown_imminent", message: "string"}
```

### Health Check
```
GET /api/health
Response: {status: "healthy", timestamp: "ISO8601"}
```

## 🛠️ Troubleshooting

### "Cannot connect to Host"
- Check HOST_LAN_IP is correct
- Verify firewall allows port 8000 on Host
- Ping from VM to Host: `ping 192.168.1.100`

### "Max auth attempts exceeded"
- Detector credentials are wrong
- Check .env on Guest matches values from Host
- Clear `failed_auth` table in database

### "Detector not heartbeating"
- Check detector process is running
- Check logs for errors
- Verify network connectivity
- If service: `nssm status VMManagerDetector`

### "Shutdown not executing"
- Check detector has Windows shutdown permission
- Check VM isn't already shutting down
- Try `/force_stop` instead (hypervisor-level)

## 📦 Dependencies

**Host Controller:**
- `python-telegram-bot` - Telegram bot interface
- `fastapi` + `uvicorn` - HTTP server
- `aiosqlite` - Async SQLite
- `python-dotenv` - Config management

**Guest Detector:**
- `httpx` - Async HTTP client
- `watchdog` - File monitoring (Parsec log)
- `pynput` - Keyboard/mouse detection (Alternative to ctypes)
- `pyinstaller` - Build to .exe

## 🔐 Production Deployment

### Host Controller
```powershell
# Install as Windows Service
nssm install VMManagerHost python -m src.main
nssm set VMManagerHost AppDirectory "C:\path\to\host-controller"
nssm set VMManagerHost AppEnvironmentExtra DATABASE_PATH=C:\data\database.sqlite
nssm start VMManagerHost
```

### Guest Detector
```powershell
# Build and install
cd guest-detector
build.bat
nssm install VMManagerDetector "C:\path\to\dist\VMManagerDetector.exe"
nssm set VMManagerDetector AppDirectory "C:\path\to\guest-detector"
nssm set VMManagerDetector ObjectName LocalSystem
nssm set VMManagerDetector AppExit Default Exit

# Start
nssm start VMManagerDetector
```

## 📝 License

Enterprise use - Modify as needed for your infrastructure.

## 🤝 Support

For issues:
1. Check logs in both Host and Guest
2. Verify network connectivity (LAN)
3. Confirm credentials in .env files match database
4. Check firewall on Host port 8000
