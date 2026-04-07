# Deployment Checklist & Troubleshooting Guide

## Pre-Deployment Checklist

### Environment Setup
- [ ] Windows 10/11 with Hyper-V enabled (Host)
- [ ] Python 3.10+ installed (`python --version`)
- [ ] pip package manager working (`pip --version`)
- [ ] PowerShell available (for Hyper-V commands)
- [ ] Telegram account created
- [ ] Router set to static IP for Host PC

### Network Setup
- [ ] Host has static LAN IP (e.g., 192.168.1.100)
- [ ] VMs configured for Bridged Network adapter
- [ ] VMs have IPs on same subnet (192.168.1.x)
- [ ] Ping from VM to Host works: `ping 192.168.1.100`
- [ ] No firewall blocking port 8000 on Host
  ```powershell
  # Add firewall rule:
  netsh advfirewall firewall add rule name="VM Manager" dir=in action=allow protocol=tcp localport=8000
  ```

### Telegram Setup
- [ ] Created bot via @BotFather
- [ ] Copied Bot Token (format: `123456789:ABCDefGHIjklmnoPQRstUVwxyz`)
- [ ] Found your Telegram User ID via @userinfobot
- [ ] Created admin secret token (any secure string)

### File Preparation
- [ ] Downloaded/extracted `vm-management-system/` folder
- [ ] Verified all files present (check with: `ls vm-management-system/`)
- [ ] Both `.env` files editable

---

## Phase 1: Host Controller Deployment

### Configuration
```powershell
# 1. Navigate to host-controller
cd vm-management-system\host-controller

# 2. Edit .env file - SET THESE VALUES:
# - TELEGRAM_BOT_TOKEN=your_token_from_botfather
# - ADMIN_SECRET_TOKEN=any_secure_string
# - HOST_LAN_IP=192.168.1.100 (YOUR HOST'S IP)
# - API_PORT=8000
```

### Testing (Manual Run)
```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the host controller
python -m src.main

# Expected output:
# "Starting VM Manager Host Controller"
# "API: http://192.168.1.100:8000"
# "Heartbeat timeout: 3 minutes"
```

### Checklist
- [ ] Dependencies installed without errors
- [ ] Host controller starts (no Python errors)
- [ ] No message: "TELEGRAM_BOT_TOKEN not set in .env file"
- [ ] No message: "Cannot bind to port 8000" (firewall issue)
- [ ] Console shows no errors, just INFO messages
- [ ] Watchdog loop is running (should see "Watchdog started" in output)

## Watchdog & Monitoring Features

### What is the Watchdog?
The watchdog is a background thread that continuously monitors all connected VMs:
- **Checks every 30 seconds** - Looks for missed heartbeats
- **3-minute timeout** - If detector doesn't heartbeat in 3 minutes, it's considered offline
- **Admin alerts** - When timeout occurs, admin receives Telegram alert
- **Auto-detection** - Automatically marks VM as offline

### Watchdog Alert Example

You'll receive alert in Telegram:
```
🚨 **Heartbeat Timeout**

VM: Gaming-PC
Detector ID: 550e8400-e29b-41d4-a716-446655440000
Last heartbeat: 180s ago

This may indicate detector process crash or tampering.
```

### When Watchdog Triggers
- Detector service crashed unexpectedly
- Network connectivity lost on VM
- Detector process was killed (though SYSTEM service prevents this)
- VM was powered off via Hyper-V
- Possible tampering/attack

### What Happens After Timeout
```
Detector misses heartbeat
        ↓
Watchdog detects (after 3 min)
        ↓
Admin receives alert
        ↓
VM marked offline
        ↓
Dashboard shows 🔴 offline
        ↓
Can /force_stop or restart detector
```

### Monitoring System Metrics

Each heartbeat includes system metrics:
- **Memory Usage %** - RAM usage at time of heartbeat
- **CPU Usage %** - CPU load at time of heartbeat

These are optional but helpful for:
- Detecting resource exhaustion
- Planning VM upgrades
- Identifying performance issues

Example heartbeat with metrics:
```
Memory: 75%
CPU: 45%
AFK: False
Parsec: Connected
```

### Troubleshooting

**Error: "ModuleNotFoundError: No module named 'telegram'"**
```powershell
pip install -r requirements.txt
# Re-run
```

**Error: "OSError: [WinError 10048] Only one usage of each socket address"**
```powershell
# Port 8000 already in use
netstat -ano | findstr :8000
taskkill /PID <PID> /F
# Or change API_PORT in .env
```

**Error: "TELEGRAM_BOT_TOKEN not set"**
```powershell
# .env file exists but token not set
# Edit host-controller/.env - add actual token value
```

---

## Phase 2: Admin Registration

### Telegram Bot Setup
```
1. KEEP Host Controller running in PowerShell
2. Open Telegram app
3. Search for your bot by name (from @BotFather setup)
4. Send: /start
   → Bot responds: "Welcome to VM Manager"
5. Send: /token your_admin_secret_from_env
   → Bot responds: "✅ You are now an admin!"
6. Send: /help
   → Shows all commands
```

### Checklist
- [ ] Bot responds to /start
- [ ] Bot responds to /token with confirmation
- [ ] Bot shows admin commands with /help
- [ ] No error messages in PowerShell console

### Troubleshooting

**Bot doesn't respond**
- Verify TELEGRAM_BOT_TOKEN is correct (copy from BotFather)
- Verify Host Controller still running (check PowerShell)
- Restart Host Controller: Ctrl+C, then `python -m src.main`

**"✅ You are now an admin!" but /token not working**
- Token is correct but wrong value
- Double-check ADMIN_SECRET_TOKEN in .env matches what you typed

---

## Phase 3: Register VM

### Add VM via Bot
```
In Telegram:
1. Send: /add_vm
2. Bot asks: "What is the VM name in your hypervisor?"
3. Send: Gaming-PC (exact name from Hyper-V)
4. Bot shows credentials:
   Detector ID: 550e8400-e29b-41d4-a716-446655440000
   Secret Key: abc123xyz...890def456...
5. Click: ✅ Yes to confirm
```

### Save Credentials
```
⚠️ IMPORTANT - Save these values!

Detector ID: ______________________
Secret Key:  ______________________
```

### Checklist
- [ ] /add_vm command recognized
- [ ] Credentials generated
- [ ] Credentials saved in safe location

---

## Phase 4: Deploy Guest Detector

### Copy Files to Guest VM
```powershell
# On Host:
1. Copy: C:\...\vm-management-system\guest-detector\
2. Paste to Guest VM at: C:\vm-manager\guest-detector\
   (Alternative: use Hyper-V file copy, USB, or network share)
```

### Configure Guest .env
```
# On Guest VM, edit C:\vm-manager\guest-detector\.env

HOST_LAN_IP=192.168.1.100      (Your Host's LAN IP)
DETECTOR_ID=550e8400-e29b...   (From /add_vm output)
VM_SECRET_KEY=abc123xyz...     (From /add_vm output)
HEARTBEAT_INTERVAL_SECONDS=60
AFK_THRESHOLD_MINUTES=60
PARSEC_LOG_PATH=C:\\Users\\Public\\AppData\\Parsec\\log.txt
LOG_LEVEL=INFO
```

### Test Manual Run (On Guest VM)
```powershell
cd C:\vm-manager\guest-detector
pip install -r requirements.txt
python -m src.main

# Expected output:
# "Detector started for 550e8400-..."
# "Host API: http://192.168.1.100:8000"
# "DEBUG - Heartbeat acknowledged"
```

### Checklist
- [ ] Dependencies installed on Guest
- [ ] Detector starts without errors
- [ ] "Heartbeat acknowledged" appears in logs
- [ ] No "Cannot connect to Host" message
- [ ] No "Invalid secret key" message
- [ ] Press Ctrl+C to stop

### Troubleshooting

**Error: "httpx.ConnectError: Cannot connect to Host"**
```powershell
# On Guest VM:
ping 192.168.1.100        # Does this work?
telnet 192.168.1.100 8000 # Can reach port 8000?

# If ping fails: Network/IP issue
# If telnet fails: Firewall or wrong port

# On Host: Verify API running
# Keep checking PowerShell console for "API:" line
```

**Error: "HTTPException: Invalid secret key"**
```powershell
# Credentials don't match VM registered in Host

# Double-check in Guest .env:
# - DETECTOR_ID exactly matches /add_vm output
# - VM_SECRET_KEY exactly matches /add_vm output
# - No extra spaces

# Clear failed auth attempts:
# Log into Host PowerShell and run:
# sqlite3 database.sqlite "DELETE FROM failed_auth WHERE detector_id='550e8400-...';"
```

**Error: "Max auth attempts exceeded"**
```powershell
# Too many failed attempts - locked out

# Clear the lock:
sqlite3 database.sqlite "DELETE FROM failed_auth WHERE detector_id='550e8400-...';"

# Try again
```

### Understanding Failed Auth Security

This is a **security feature** to prevent brute-force attacks:
- **3-strike lockout** - After 3 wrong secret keys, detector is locked for 1 hour
- **1-hour rolling window** - Failed attempts older than 1 hour expire automatically
- **Logged in database** - Admins can review failed attempts for auditing

**Why it might happen:**
- Wrong secret key in `guest-detector/.env`
- Copy-paste error when configuring detector
- Old VM with outdated credentials

**How to fix:**
1. Check output from `/add_vm` for correct Detector ID and Secret Key
2. Edit `guest-detector/.env` with exact values (copy-paste, don't type)
3. Restart detector service
4. If still locked, clear failed_auth table: `DELETE FROM failed_auth WHERE detector_id='...'`
5. Restart detector again

---

## Phase 5: Install as Windows Service

### Build Executable (On Guest VM)
```powershell
cd C:\vm-manager\guest-detector

# Run the build script (creates dist\VMManagerDetector.exe)
build.bat

# Expected output:
# "Build successful!"
# "Executable location: .\dist\VMManagerDetector.exe"
```

### Install Service (Admin Required)
```powershell
# Open PowerShell AS ADMINISTRATOR

# Option 1: If NSSM not installed
choco install nssm
# or download from https://nssm.cc/download

# Option 2: Install service
nssm install VMManagerDetector "C:\vm-manager\guest-detector\dist\VMManagerDetector.exe"

# Set working directory
nssm set VMManagerDetector AppDirectory "C:\vm-manager\guest-detector"

# Auto-restart on crash
nssm set VMManagerDetector AppExit Default Exit

# Start service
nssm start VMManagerDetector

# Verify running
nssm status VMManagerDetector
# Should show: SERVICE_RUNNING

# Optional: Set to auto-start on reboot
sc config VMManagerDetector start= delayed-auto
```

### Checklist
- [ ] PyInstaller compiled .exe successfully
- [ ] NSSM installed
- [ ] Service installed with nssm
- [ ] Service shows "SERVICE_RUNNING"
- [ ] Can reboot VM and service auto-starts

### Troubleshooting

**Error: "File not found: C:\vm-manager\dist\VMManagerDetector.exe"**
```powershell
# build.bat didn't complete successfully
# Check for errors in PyInstaller output
# Try again: build.bat
```

**Error: "nssm: command not found"**
```powershell
# NSSM not installed
choco install nssm
# Or manually add to PATH
```

**Service won't start: "Error: The application exited immediately"**
```powershell
# Check errors:
nssm get VMManagerDetector AppStderr
nssm get VMManagerDetector AppStdout

# Common cause: .env file not found in AppDirectory
# Verify C:\vm-manager\guest-detector\.env exists
```

**Service runs but not sending heartbeats**
```powershell
# Check detector can connect to Host
# From Guest PowerShell:
Invoke-WebRequest -Uri "http://192.168.1.100:8000/api/health"
# Should return JSON response

# If fails: Network connectivity issue
```

---

## Phase 6: Verify End-to-End

### From Host Controller
```
1. Verify Guest detected as "Online"
   In Telegram: /users
   Or query database:
   sqlite3 database.sqlite "SELECT detector_id, status FROM vms;"
   
2. Check heartbeat is recent:
   sqlite3 database.sqlite "SELECT detector_id, last_heartbeat FROM vms;"
   Should show time within last 60 seconds
```

### From Telegram Bot
```
1. Send: /dashboard
   Should show: 🟢 Gaming-PC (online)

2. Click on VM for details
   Should show status, last heartbeat time

3. Test start/stop:
   /stop_vm <detector_id>
   Watch Guest VM start shutdown sequence
```

### Checklist
- [ ] /users shows VM in database
- [ ] /dashboard shows 🟢 online status
- [ ] Last heartbeat is recent (<1 min old)
- [ ] /stop_vm triggers shutdown on Guest
- [ ] /force_stop immediately powers off

---

## Phase 7: Production Deployment (Host as Service)

### Install Host as Windows Service
```powershell
# On Host, in PowerShell as ADMINISTRATOR

nssm install VMManagerHost "python" "-m src.main"
nssm set VMManagerHost AppDirectory "C:\vm-manager\host-controller"
nssm set VMManagerHost AppEnvironmentExtra DATABASE_PATH=C:\data\database.sqlite
nssm set VMManagerHost AppExit Default Exit

# Start service
nssm start VMManagerHost

# Verify running
nssm status VMManagerHost
```

### Checklist
- [ ] Both services running: VMManagerHost + VMManagerDetector
- [ ] Services auto-restart on crash
- [ ] Services auto-start after reboot
- [ ] Can manage VMs via Telegram bot
- [ ] `/dashboard` shows online status

---

## Monitoring & Maintenance

### Daily Checks
```powershell
# 1. Verify services running
Get-Service VMManagerHost, VMManagerDetector | Select-Object Name, Status

# 2. Check recent errors
Get-EventLog -LogName System -Source nssm -Newest 10 | Format-Table

# 3. Verify database integrity
sqlite3 C:\data\database.sqlite "SELECT COUNT(*) FROM vms;"
```

### Weekly Checks
```powershell
# 1. Backup database
Copy-Item C:\data\database.sqlite C:\data\database.sqlite.backup

# 2. Check failed auth attempts
sqlite3 C:\data\database.sqlite "SELECT COUNT(*) FROM failed_auth WHERE attempt_time > datetime('now', '-7 days');"

# 3. Check service restart count
nssm query VMManagerHost
```

### Monthly Tasks
- [ ] Review and archive old heartbeat data
- [ ] Test /force_stop functionality
- [ ] Verify graceful shutdown works
- [ ] Update .env tokens if needed
- [ ] Review banned/pending users

---

## Disaster Recovery

### Service Won't Start
```powershell
# 1. Check errors
nssm status VMManagerDetector
nssm get VMManagerDetector AppStderr

# 2. Test manually
python -m src.main

# 3. Check .env file
# 4. Check file permissions
# 5. Reinstall service
nssm stop VMManagerDetector
nssm remove VMManagerDetector
nssm install VMManagerDetector ...
```

### Database Corrupted
```powershell
# 1. Restore from backup
Remove-Item database.sqlite
Copy-Item database.sqlite.backup database.sqlite

# 2. Or reinitialize
# (Detector will recreate schema on startup)
```

### Detector Keeps Crashing
```powershell
# 1. Check logs
Get-Content "C:\vm-manager\guest-detector\src\main.py" -Tail 50

# 2. Test manually
cd C:\vm-manager\guest-detector
python -m src.main

# 3. Common issues
# - Network unreachable
# - .env not found
# - Permissions issues
# - Port conflicts
```

---

## Final Verification

- [ ] ✅ Host Controller running (service or manual)
- [ ] ✅ Guest Detector running (service or manual)
- [ ] ✅ Telegram bot responds to commands
- [ ] ✅ Database has VMs registered
- [ ] ✅ Heartbeats flowing every 60 seconds
- [ ] ✅ Can see VM status in Telegram
- [ ] ✅ Can start/stop VMs from Telegram
- [ ] ✅ USB/Network test successful

---

## Success! 🎉

If all checks pass, your VM Manager is ready for production!

**Need help?** Review `SETUP.md` or `README.md` for detailed explanations.
