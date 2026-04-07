# VM Manager - Step-by-Step Setup Guide

## Prerequisites Checklist

- [ ] Windows 10/11 with Hyper-V enabled
- [ ] Python 3.10+ installed and accessible from PowerShell
- [ ] Telegram account with Bot API token
- [ ] Network: Host and VMs must be on same LAN (e.g., 192.168.1.x)
- [ ] No internet port forwarding on main router

## Phase 1: Telegram Bot Setup (5 minutes)

### 1. Create Telegram Bot
1. Open Telegram app
2. Find `@BotFather`
3. Send: `/newbot`
4. Follow prompts:
   - Bot name: `VM Manager` (or your choice)
   - Bot username: `vm_manager_bot_<random>` (must be unique)
5. Copy the **Bot Token** (looks like: `123456789:ABCDefGHIjklmnoPQRstUVwxyz`)

### 2. Get Your Telegram User ID
1. Find `@userinfobot`
2. Send any message
3. Bot replies with your User ID (e.g., `123456789`)

## Phase 2: Admin Registration & User Management

### 1. Admin Token Setup

Edit `host-controller/.env`:

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCDefGHIjklmnoPQRstUVwxyz
ADMIN_SECRET_TOKEN=my_super_secret_admin_password_12345
HOST_LAN_IP=192.168.1.100
API_PORT=8000
DATABASE_PATH=./database.sqlite
MAX_FAILED_AUTH=3
HEARTBEAT_TIMEOUT_MINUTES=3
AFK_THRESHOLD_MINUTES=60
```

**Find your Host LAN IP:**
```powershell
ipconfig /all
# Look for "IPv4 Address" under your main network adapter
# Should be 192.168.1.x or 10.0.0.x
```

### 2. Test Host Controller

```powershell
cd host-controller
pip install -r requirements.txt
python -m src.main
```

**Expected output:**
```
2026-01-15 10:30:45 - root - INFO - Starting VM Manager Host Controller
2026-01-15 10:30:45 - root - INFO -   API: http://192.168.1.100:8000
2026-01-15 10:30:45 - root - INFO -   Heartbeat timeout: 3 minutes
```

### 3. Initialize Bot & Become Admin

In Telegram (with the bot running):
1. Find your bot and send: `/start`
2. Bot responds: "Welcome to VM Manager"
3. Send: `/token my_super_secret_admin_password_12345`
4. Bot responds: "✅ You are now an admin!"

**Stop the Host Controller** (Ctrl+C in PowerShell)

## Phase 2b: Understanding User Roles & Workflow

Your system has 4 user roles with different permissions. Before adding users, understand the workflow:

| Role | Capabilities | How They Get It |
|------|--------------|-----------------|
| **Pending** | Blocked - only welcome message | New user sends `/start` |
| **User** | Can start VMs, view assigned VMs | Admin sends `/approve <user_id>` |
| **Admin** | Full control: add/assign/delete VMs, manage users, shutdown VMs | Admin sends `/promote <user_id>` OR anyone sends `/token ADMIN_SECRET` |
| **Banned** | Completely blocked | Admin sends `/ban <user_id>` |

### User Lifecycle Example
```
Your Telegram ID: 123456789

Step 1: You send /start
        → Bot registers you as PENDING
        
Step 2: Admin (you) sends /users
        → Sees: "123456789 - Unknown - pending"
        
Step 3: Admin sends /approve 123456789
        → You're now a REGULAR USER
        → Can now use /dashboard and /start_vm
        
Step 4: If admin sends /promote 123456789
        → You become ADMIN
        → Can now use all commands
```

### Other Users Management
```bash
# Other users want to use the bot:

# 1. They send /start → Registered as PENDING
# 2. You see them in /users command
# 3. You approve them: /approve <their_user_id>
# 4. They can now start VMs

# To promote to admin:
/promote <user_id>

# To ban a user:
/ban <user_id>

# To unban:
/pardon <user_id>

# To delete completely:
/delete_user <user_id>
```

## Phase 3: Add Your First VM (10 minutes)

### 1. Register VM in Host Controller

```powershell
# Start Host Controller again
python -m src.main

# In a new PowerShell window, test the API
Invoke-WebRequest -Uri "http://192.168.1.100:8000/api/health"
# Should return: {"status": "healthy", ...}
```

### 2. Create VM via Telegram Bot

In Telegram:
1. Send: `/add_vm`
2. Bot asks: "What is the VM name in your hypervisor?"
3. Send: `Windows-Gaming-PC` (exact name as shown in Hyper-V)
4. Bot shows credentials:
   ```
   Detector ID: 550e8400-e29b-41d4-a716-446655440000
   Secret Key: abc123xyz...
   ```
5. Click ✅ Yes to confirm

**Save these values!** You'll need them for the guest detector.

### 3. Verify VM is Registered

In Telegram:
- Send: `/users` to see user table
- Your VM won't appear here yet (it will once detector connects)

## Phase 4: Guest Detector Deployment (20 minutes)

### 1. Copy Detector to Guest VM

1. On Host, copy `guest-detector/` folder
2. Use Hyper-V file sharing or removable media
3. Paste to Guest VM at: `C:\vm-manager\guest-detector\`

### 2. Configure Guest .env

On Guest VM, edit `guest-detector/.env`:

```bash
HOST_LAN_IP=192.168.1.100
API_PORT=8000
DETECTOR_ID=550e8400-e29b-41d4-a716-446655440000
VM_SECRET_KEY=abc123xyz...
HEARTBEAT_INTERVAL_SECONDS=60
AFK_THRESHOLD_MINUTES=60
PARSEC_LOG_PATH=C:\\Users\\Public\\AppData\\Parsec\\log.txt
LOG_LEVEL=INFO
```

### 3. Test Detector (Manual Run)

On Guest VM, open PowerShell:

```powershell
cd C:\vm-manager\guest-detector
pip install -r requirements.txt
python -m src.main
```

**Expected output:**
```
2026-01-15 10:45:30 - root - INFO - Detector started for 550e8400-e29b...
2026-01-15 10:45:30 - root - INFO -   Host API: http://192.168.1.100:8000
2026-01-15 10:45:32 - root - DEBUG - Heartbeat acknowledged
```

If successful, stop it (Ctrl+C)

### 4. Build Executable

On Guest VM:

```powershell
cd C:\vm-manager\guest-detector
build.bat
```

This creates: `dist\VMManagerDetector.exe`

### 5. Install as Windows Service (Requires Admin)

On Guest VM, open PowerShell **as Administrator**:

```powershell
# Download NSSM from https://nssm.cc/download or use Chocolatey
choco install nssm

# Install service
nssm install VMManagerDetector "C:\vm-manager\guest-detector\dist\VMManagerDetector.exe"

# Set working directory
nssm set VMManagerDetector AppDirectory "C:\vm-manager\guest-detector"

# Configure to auto-restart on crash
nssm set VMManagerDetector AppExit Default Exit

# Start service
nssm start VMManagerDetector

# Verify it's running
nssm status VMManagerDetector
```

## Phase 5: Test Everything (10 minutes)

### 1. Check Detector Connection

On Host, start Host Controller:

```powershell
python -m src.main
```

On Guest VM, verify detector service is running:
```powershell
Get-Service VMManagerDetector
# Should show "Running"
```

In Telegram, after 60 seconds:
- Send: `/users`
- You should see your VM connected
- Status will show "Online"

### 2. Test VM Control

In Telegram:
1. Send: `/dashboard`
2. Click on your VM
3. Should show: `🟢 Windows-Gaming-PC (online)`
4. Click `▶️ Start` (will restart it)

### 3. Test Graceful Shutdown

In Telegram:
1. Send: `/stop_vm 550e8400-e29b-41d4-a716-446655440000`
2. In VM: Windows will start shutting down in ~60 seconds
3. In Telegram: Receive confirmation

### 4. Test Force Shutdown

In Telegram:
1. Start the VM first
2. Send `/force_stop <detector_id>`
3. Hyper-V will power off the VM instantly (hard shutdown)

## Phase 5b: Understanding the Interactive Dashboard

The `/dashboard` command shows an interactive view of your VMs with quick-action buttons:

### Dashboard Features

```
In Telegram:
► Send: /dashboard

You see:
📊 All VMs (Admin View):
  🟢 Gaming-PC (→ bob#12345)
  🔴 Server-01 (unassigned)
  🟢 Dev-Machine (→ alice#67890)

Click the button for any VM →
```

### When You Click a VM Button

**If VM is OFFLINE** 🔴:
```
VM Info:
🔴 Gaming-PC
Status: offline
Last Heartbeat: 2 hours ago
Assigned: bob#12345

[▶️ Start]  ← Click to power on
```

**If VM is ONLINE** 🟢 **(Admin Only)**:
```
VM Info:
🟢 Gaming-PC  
Status: online
Last Heartbeat: 30 seconds ago
Assigned: bob#12345

[⏸️ Stop] [⚡ Force Stop]  ← Admin-only buttons
  (graceful)  (hard shutdown)
```

**Permission Notes**:
- **Regular Users**: See only VMs assigned to them
- **Admins**: See all VMs + can control any VM
- **Start button**: Available to everyone (if they have permission)
- **Stop/Force-Stop buttons**: Admin only

### Quick Control Flow

```
Admin uses dashboard:

1. Send /dashboard
2. See list with status icons:
   🟢 = Online (Can stop/force-stop)
   🔴 = Offline (Can start)
3. Click VM to see details
4. Click action button (Start/Stop/Force-Stop)
5. Confirmation in chat

Much faster than typing /stop_vm commands!
```

## Phase 6: Manage Users (5 minutes)

### 1. Add Another User

Get their Telegram User ID from `@userinfobot`:

In your admin Telegram:
1. Send: `/users`
2. They should have first started the bot
3. Send: `/promote <their_user_id>` to make them admin
   - Or assign specific VMs: `/assign <detector_id> <their_user_id>`

### 2. User Workflow

Other users can:
- Send: `/start` to register
- Your approval: `/users` → see them as "pending"
- Your action: `/promote <user_id>` to approve
- They then: `/dashboard` to see assigned VMs

## Common Issues & Fixes

### "Cannot connect to Host"

**Symptoms:**
```
httpx.ConnectError: Cannot connect to Host at http://192.168.1.100:8000
```

**Fixes:**
```powershell
# 1. Verify Host is running
# 2. Check if IP is correct (from Host)
ipconfig /all

# 3. Test connectivity from Guest
ping 192.168.1.100

# 4. Test API directly from Guest PowerShell
Invoke-WebRequest -Uri "http://192.168.1.100:8000/api/health"

# 5. Check Windows Firewall on Host
netsh advfirewall firewall add rule name="VM Manager API" `
  dir=in action=allow protocol=tcp localport=8000
```

### "Max auth attempts exceeded"

**Symptoms:**
```
HTTPException: Max auth attempts exceeded
```

**Fix:**
```sql
-- On Host, in database.sqlite
DELETE FROM failed_auth WHERE detector_id = "your-detector-id";
```

### "Shutdown command not executing"

**Likely cause:** Detector not running as SYSTEM

**Fix:**
```powershell
# Verify service runs as LocalSystem:
nssm get VMManagerDetector ObjectName
# Should return: LocalSystem

# If not, fix it:
nssm set VMManagerDetector ObjectName LocalSystem
nssm restart VMManagerDetector
```

### "Detector dies after restart"

**Likely cause:** .env file not accessible when running as service

**Fix:**
1. Ensure .env is in the same directory as executable
2. Or hardcode values in source (not recommended)
3. Check NSSM error logs:
   ```powershell
   nssm get VMManagerDetector AppDirectory
   nssm get VMManagerDetector AppStderr
   ```

## Monitoring & Maintenance

### Check Detector Health

```powershell
# On Guest VM
Get-Service VMManagerDetector | Select-Object Status, DisplayName

# View recent logs
cat "C:\vm-manager\guest-detector\detector.log" | Select-String "ERROR\|WARNING" -Last 20
```

### Check Host Health

```powershell
# On Host
Get-Service VMManagerHost | Select-Object Status, DisplayName

# Verify API is running
Invoke-WebRequest -Uri "http://192.168.1.100:8000/api/health"
```

### Monitor Database

```python
# Quick SQLite check
python
import sqlite3
conn = sqlite3.connect("./database.sqlite")
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM vms")
print("VMs registered:", c.fetchone()[0])
```

## Performance Tips

1. **Increase Heartbeat Interval** - Less network traffic
   - Change `HEARTBEAT_INTERVAL_SECONDS=300` (5 minutes)

2. **Adjust Timeout** - Reduce force-kills
   - Change `HEARTBEAT_TIMEOUT_MINUTES=5` (5 minutes instead of 3)

3. **Use SQLite Backups**
   ```powershell
   Copy-Item database.sqlite database.sqlite.backup
   ```

## Next Steps

- Set up Parsec for remote desktop stability monitoring
- Configure email alerts in handlers for critical events
- Add more hypervisors (VirtualBox, Proxmox)
- Implement VM resource quotas
- Add REST API authentication for programmatic access

Enjoy your enterprise VM management system! 🚀
