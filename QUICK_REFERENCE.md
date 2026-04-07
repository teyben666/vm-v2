# VM Manager - Quick Reference

## Admin Telegram Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/start` | - | Show welcome message |
| `/help` | - | Display all available commands |
| `/dashboard` | - | View your assigned VMs (interactive) |
| `/users` | - | List all registered users & roles |
| `/token <secret>` | `/token my_password` | Become admin with admin token |
| `/add_vm <name>` | `/add_vm Gaming-PC` | Register new VM (get detector credentials) |
| `/assign` | `/assign <detector_id> <user_id>` | Assign VM to user |
| `/start_vm <id>` | `/start_vm 550e8400...` | Start a VM |
| `/stop_vm <id>` | `/stop_vm 550e8400...` | Graceful shutdown (detector executes) |
| `/force_stop <id>` | `/force_stop 550e8400...` | Force shutdown (hypervisor executes immediately) |
| `/approve <user_id>` | `/approve 123456789` | Approve pending user as regular user |
| `/promote <user_id>` | `/promote 123456789` | Make user admin |
| `/ban <user_id>` | `/ban 123456789` | Ban user from bot |
| `/pardon <user_id>` | `/pardon 123456789` | Unban user |
| `/approve <user_id>` | `/approve 123456789` | Approve pending user as regular user |
| `/delete_vm <detector_id>` | `/delete_vm 550e8400...` | Permanently delete a VM registration |
| `/delete_user <user_id>` | `/delete_user 123456789` | Permanently delete a user account |

## Configuration Files

### Host: `.env`

```bash
# === REQUIRED ===
TELEGRAM_BOT_TOKEN=bot_token_from_botfather
ADMIN_SECRET_TOKEN=any_strong_password_here
HOST_LAN_IP=192.168.1.100  # Your host's LAN IP

# === OPTIONAL (with defaults) ===
API_PORT=8000                           # Port detector connects to
DATABASE_PATH=./database.sqlite         # SQLite file location
MAX_FAILED_AUTH=3                       # Max failed attempts before lockout
HEARTBEAT_TIMEOUT_MINUTES=3             # Time to mark VM offline (watchdog)
AFK_THRESHOLD_MINUTES=60                # Minutes idle before auto-shutdown
```

#### Configuration Details

| Setting | Default | What It Does | Tips |
|---------|---------|--------------|------|
| `TELEGRAM_BOT_TOKEN` | none | Token from @BotFather | Required! Bot won't start without it |
| `ADMIN_SECRET_TOKEN` | none | First admin password | Set something secure, change after use |
| `HOST_LAN_IP` | 192.168.1.100 | Host computer's IP on LAN | Find with `ipconfig /all` |
| `API_PORT` | 8000 | Port for detector heartbeats | Change only if 8000 conflicts |
| `DATABASE_PATH` | ./database.sqlite | Where to store database | Can point to network drive for backup |
| `MAX_FAILED_AUTH` | 3 | Failed key attempts allowed | 3 = standard 1-hour lockout |
| `HEARTBEAT_TIMEOUT_MINUTES` | 3 | Watchdog timeout | Shorter = faster detection but more false positives |
| `AFK_THRESHOLD_MINUTES` | 60 | Auto-shutdown idle timer | How long user must be AFK+disconnected before auto-shutdown |

### Guest: `.env`

```bash
# === REQUIRED ===
HOST_LAN_IP=192.168.1.100              # Host's LAN IP (from /add_vm)
DETECTOR_ID=550e8400-e29b-41d4-...     # UUID from /add_vm
VM_SECRET_KEY=abc123xyz-...            # Secret from /add_vm

# === OPTIONAL (with defaults) ===
API_PORT=8000                          # Port to connect to (match host)
HEARTBEAT_INTERVAL_SECONDS=60          # How often to check in
AFK_THRESHOLD_MINUTES=60               # Auto-shutdown timer
PARSEC_LOG_PATH=C:\\Users\\Public\\AppData\\Parsec\\log.txt
LOG_LEVEL=INFO                         # DEBUG for troubleshooting
```

#### Configuration Details

| Setting | Default | What It Does | Tips |
|---------|---------|--------------|------|
| `HOST_LAN_IP` | 192.168.1.100 | Host IP to connect to | Must match HOST_LAN_IP on host exactly |
| `DETECTOR_ID` | none | Unique VM identifier | Copy exactly from `/add_vm` output |
| `VM_SECRET_KEY` | none | Authentication secret | Copy exactly from `/add_vm` output |
| `API_PORT` | 8000 | Host's API port | Must match host's API_PORT |
| `HEARTBEAT_INTERVAL_SECONDS` | 60 | Check-in frequency | Don't go below 30 (causes spam) |
| `AFK_THRESHOLD_MINUTES` | 60 | Auto-shutdown idle time | How long AFK must be before auto-power-off |
| `PARSEC_LOG_PATH` | [path above] | Where to watch Parsec | Leave default unless custom Parsec install |
| `LOG_LEVEL` | INFO | Log verbosity | Change to DEBUG to troubleshoot |

### Guest: `.env`

## File Locations

```
vm-management-system/
├── README.md                           # Main documentation
├── SETUP.md                            # Detailed setup guide
├── QUICK_REFERENCE.md                  # This file
│
├── host-controller/
│   ├── .env                            # CONFIG: Edit this!
│   ├── run.bat                         # Quick start script
│   ├── requirements.txt                # Dependencies
│   ├── database.sqlite                 # ⚠️ DO NOT EDIT DIRECTLY
│   │
│   └── src/
│       ├── __init__.py
│       ├── main.py                     # Entry point (asyncio loop)
│       ├── db.py                       # Database functions
│       ├── hypervisor_plugin.py        # Hyper-V integration
│       │
│       ├── bot/
│       │   ├── __init__.py
│       │   ├── commands.py             # Telegram bot commands
│       │   └── handlers.py             # Callback handlers
│       │
│       └── api/
│           ├── __init__.py
│           └── endpoints.py            # FastAPI HTTP endpoints
│
└── guest-detector/
    ├── .env                            # CONFIG: Edit this!
    ├── run.bat                         # Test script (manual)
    ├── build.bat                       # Build .exe for service
    ├── requirements.txt
    │
    └── src/
        ├── __init__.py
        ├── main.py                     # Entry point
        ├── idle_checker.py             # AFK detection
        ├── parsec_reader.py            # Parsec connection detection
        ├── api_sender.py               # HTTP heartbeat sender
        └── os_manager.py               # Shutdown & system commands
```

## Startup Sequence

### Host Controller (Windows)

1. **Manually** (for testing):
   ```powershell
   cd host-controller
   python -m src.main
   ```

2. **As Service** (production):
   ```powershell
   nssm install VMManagerHost python -m src.main
   nssm set VMManagerHost AppDirectory "C:\path\to\host-controller"
   nssm start VMManagerHost
   ```

### Guest Detector (Windows VM)

1. **Manually** (for testing):
   ```powershell
   cd guest-detector
   python -m src.main
   ```

2. **As Service** (production):
   ```powershell
   build.bat                    # Creates dist\VMManagerDetector.exe
   nssm install VMManagerDetector "C:\path\dist\VMManagerDetector.exe"
   nssm set VMManagerDetector AppDirectory "C:\path\to\guest-detector"
   nssm start VMManagerDetector
   ```

## User Roles & Permissions

| Role | Capabilities | Needs Approval |
|------|--------------|----------------|
| **Pending** | View welcome message only | ❌ Awaiting admin approval |
| **User** | Start VMs, view assigned VMs, see dashboard | ✅ Admin approved |
| **Admin** | All user actions + create/delete/assign VMs, manage users, stop/force-stop | ✅ Promoted by admin or /token |
| **Banned** | Cannot use bot (all commands blocked) | ❌ Must be pardoned by admin |

### Role Progression
```
New User Registration
       ↓
Pending (waiting for /approve)
       ↓
Regular User (can start VMs)
       ↓
Admin (/promote command)
       ↓
Full Administrative Control
```

## API Endpoints Reference

### Heartbeat (Detector → Host)
**POST** `/api/heartbeat`
```
Headers:
  X-Detector-ID: 550e8400-e29b-41d4-a716-446655440000
  X-VM-Secret: abc123xyz...

Request:
{
  "afk": false,
  "afk_duration_minutes": 5,
  "parsec_connected": true,
  "memory_usage_percent": 45.2,
  "cpu_usage_percent": 12.5
}

Response:
{
  "status": "acknowledged",
  "command": null,              # or "shutdown" or "auto_shutdown_pending"
  "delay_seconds": 60           # Time before executing shutdown
}
```

### Alert (Detector → Host)
**POST** `/api/alert`
```
Headers:
  X-Detector-ID: 550e8400-e29b-41d4-a716-446655440000
  X-VM-Secret: abc123xyz...

Request:
{
  "type": "imminent_shutdown",
  "message": "System shutting down in 5 minutes"
}

Response:
{
  "status": "received"
}
```

### Health Check
**GET** `/api/health`
```
Response:
{
  "status": "healthy",
  "timestamp": "2026-01-15T10:30:45.123456"
}
```

### List All VMs  
**GET** `/api/vms` (Requires authentication)
```
Headers:
  X-Detector-ID: any-detector-id
  X-VM-Secret: corresponding-secret

Response:
{
  "vms": [{...VM data...}],
  "count": 3
}
```

### Get VM Info
**GET** `/api/vms/{detector_id}` (Requires authentication)
```
Headers:
  X-VM-Secret: detector-secret

Response:
{
  "detector_id": "550e8400-e29b-41d4-a716-446655440000",
  "hypervisor_name": "Gaming-PC",
  "status": "online",
  "last_heartbeat": "2026-01-15T10:30:45.123456",
  "assigned_user_id": null
}
```

## Security Model

```
┌─ EXTERNAL INTERNET ─┐
│  Telegram API       │  ← Only outbound (bot polling)
│  NO PORT FORWARD    │
└─────────┬───────────┘
          │
    ┌─────▼──────────────────┐
    │   HOST CONTROLLER      │
    │  192.168.1.100:8000    │  ← Only accessible on LAN
    │  Hyper-V PowerShell    │
    │  SQLite Database       │
    └─────┬──────────────────┘
          │
    ┌─────┴─────────────────────┐
    │  BRIDGED NETWORK (LAN)    │
    │  192.168.1.0/24           │  ← Isolated from internet
    │                           │
    ├─────────────────────────┐ │
    │  VM-1 Guest Detector    │ │
    │  Heartbeat every 60s    │ │
    │  AFK monitoring         │ │
    └─────────────────────────┘ │
```

**Auth on every request:**
- Malformed headers → **401 Unauthorized**
- Bad secret → **403 Forbidden** (logged + attempted auth counter)
- Missing detector → **404 Not Found**

## Troubleshooting Matrix

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Cannot connect to Host" | Wrong IP or port | Check `HOST_LAN_IP` in .env, verify firewall port 8000 |
| "Max auth attempts exceeded" | Wrong credentials | Delete from `failed_auth` table, verify .env match |
| Detector not heartbeating | Service not running | `nssm status VMManagerDetector` |
| Shutdown not executing | Detector crashed | Check logs for errors, service status |
| Detector runs but not as service | NSSM config issue | Verify `nssm status`, check AppDirectory path |
| Host API unresponsive | Watchdog loop crashed | Restart `python -m src.main` |

## Database Schema Quick View

### `users` Table
```sql
id              INTEGER PRIMARY KEY
telegram_id     TEXT UNIQUE
username        TEXT
role            TEXT ('admin', 'user', 'pending')
is_banned       INTEGER (0=no, 1=yes)
```

### `vms` Table
```sql
detector_id     TEXT PRIMARY KEY
hypervisor_name TEXT
secret_key      TEXT UNIQUE
assigned_user_id TEXT (FK)
status          TEXT ('online', 'offline', 'pending_shutdown')
last_heartbeat  DATETIME
```

## Performance Tuning

| Setting | Default | Production |  Impact |
|---------|---------|-----------|---------|
| HEARTBEAT_INTERVAL_SECONDS | 60 | 300 | Less network traffic, slower detection |
| HEARTBEAT_TIMEOUT_MINUTES | 3 | 5 | Reduces false positives on slow network |
| MAX_FAILED_AUTH | 3 | 5 | More tolerance for corrupted packets |
| AFK_THRESHOLD_MINUTES | 60 | 120 | Longer before auto-shutdown |

## Common Workflows

### Register New User
```
User: /start                    → Bot: Welcome
User: (waits for admin approval)
Admin: /users                   → List all users
Admin: /promote <user_id>       → Approve
User: /dashboard                → Can now see VMs
```

### Add New VM
```
Admin: /add_vm
Admin: Windows-Gaming            → Bot generates credentials
Admin: (copy credentials)
Install Guest Detector on VM with credentials
Wait 60 seconds → Heartbeat arrives
Admin: /users                   → See VM is online
```

### Graceful Shutdown Workflow
```
Admin: /stop_vm <detector_id>
  ↓
Host: Mark VM as pending_shutdown
  ↓
Detector: Next heartbeat (within 60s)
  ↓
Host: Return "shutdown" command in response
  ↓
Detector: Execute: shutdown /s /t 60
  ↓
VM: Show "System shutting down in 60 seconds"
  ↓
User: Can type in 60-second window
  ↓
VM: Shutdown, services stop properly
```

### Force Shutdown Workflow
```
Admin: /force_stop <detector_id>
  ↓
Host: Immediately execute hypervisor command
  ↓
Host: PowerShell: Stop-VM -Name "..." -TurnOff -Force
  ↓
VM: No warning, hard power-off (like pulling plug)
  ↓
Admin: VM marked offline
```

## Testing Checklist

- [ ] Host bot receives `/start` command
- [ ] User can become admin with `/token`
- [ ] Add VM generates credentials
- [ ] Guest detector starts and connects
- [ ] Heartbeat shows in logs
- [ ] `/dashboard` shows VM as online
- [ ] `/stop_vm` causes detector to shutdown
- [ ] `/force_stop` immediately powers off VM
- [ ] User permissions prevent unauthorized VM access
- [ ] Banned user cannot use bot

## Environment Variables Summary

| Variable | Example | Used By |
|----------|---------|---------|
| TELEGRAM_BOT_TOKEN | 123:ABC... | Host Bot |
| ADMIN_SECRET_TOKEN | secret123 | Host Bot Auth |
| HOST_LAN_IP | 192.168.1.100 | Host & Guest |
| API_PORT | 8000 | Host & Guest |
| DETECTOR_ID | uuid | Guest |
| VM_SECRET_KEY | uuid | Guest |
| DATABASE_PATH | ./database.sqlite | Host |
| HEARTBEAT_TIMEOUT_MINUTES | 3 | Host Watchdog |
| HEARTBEAT_INTERVAL_SECONDS | 60 | Guest |
| AFK_THRESHOLD_MINUTES | 60 | Guest |
| PARSEC_LOG_PATH | C:\...\log.txt | Guest |
| LOG_LEVEL | INFO | Both |

---

**Need help?** Check `SETUP.md` for detailed step-by-step instructions!
