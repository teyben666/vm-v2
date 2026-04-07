# 🚀 Getting Started - Your VM Manager Awaits!

Welcome to your **complete, enterprise-grade VM Management System**. Everything is built, tested, and ready to deploy.

## 📍 You Are Here

Your project is located at:
```
C:\Users\example\Desktop\VM software\vm-management-system\
```

## 🎯 What You Have

✅ **Complete source code** for:
- Telegram Bot with admin commands
- FastAPI HTTP server for VM communication
- SQLite database with full schema
- Hyper-V PowerShell integration
- Guest VM detector service
- AFK monitoring & graceful shutdown
- Anti-tampering watchdog

✅ **Production-ready files**:
- All required .env templates
- Quick-start batch scripts
- Service installation tools
- PyInstaller build system

✅ **Comprehensive documentation**:
- README (architecture overview)
- SETUP guide (step-by-step)
- QUICK_REFERENCE (command cheat sheet)
- IMPLEMENTATION summary
- DEPLOYMENT_CHECKLIST
- This getting started guide

## 🚦 3 Ways to Get Started

### Option A: Fastest (30 minutes, on your test VM)
If you already know your Telegram token and want to test quickly:
1. Get Telegram bot token (@BotFather)
2. Edit `host-controller/.env`
3. Run `host-controller/run.bat`
4. Send bot: `/token YOUR_SECRET`
5. Follow the bot prompts

**Time needed:** 30 minutes
**Best for:** Testing & learning

### Option B: Complete Setup (2 hours, full deployment)
If you're ready for production:
1. Follow `SETUP.md` (detailed step-by-step)
2. Deploy Host Controller
3. Deploy Guest Detector
4. Install both as Windows services
5. Test all features

**Time needed:** 2 hours
**Best for:** Production deployment

### Option C: Deep Dive (4 hours, understand everything)
If you want to understand the architecture:
1. Read `README.md` (understand architecture)
2. Review `QUICK_REFERENCE.md` (commands)
3. Read source code comments
4. Follow `SETUP.md` for deployment
5. Test edge cases

**Time needed:** 4 hours
**Best for:** Maintenance & customization

---

## 📚 Documentation Reading Order

Start here for fastest understanding:

```
1. THIS FILE (5 min)
   ↓ What you have, where to go
   
2. README.md (10 min)
   ↓ Architecture, features, security model
   
3. SETUP.md (30 min follow, 2 hours total)
   ↓ Step-by-step deployment guide
   
4. QUICK_REFERENCE.md (5 min)
   ↓ Commands cheat sheet, config reference
   
5. Source code (30+ min)
   ↓ Host/Guest implementation details
```

## 🎬 Quick Start (Choose One)

### I Want to Test It NOW (30 min)

```powershell
# 1. Get Telegram token
# - Message @BotFather
# - /newbot
# - Copy token

# 2. Start host controller
cd "C:\Users\example\Desktop\VM software\vm-management-system\host-controller"

# Edit .env file:
# TELEGRAM_BOT_TOKEN=<your_token>
# ADMIN_SECRET_TOKEN=mysecret123
# HOST_LAN_IP=192.168.1.100

# 3. Run it
python -m src.main

# 4. In Telegram, find your bot and:
# /start
# /token mysecret123
# /help
```

**You're done testing!** Stop with Ctrl+C when ready.

### I Want Full Setup (Follow SETUP.md)

Read: `SETUP.md`

This has detailed instructions for:
- Phase 1: Telegram Bot Setup (5 min)
- Phase 2: Host Controller (15 min)
- Phase 3: Admin Registration (5 min)
- Phase 4: Add VM (10 min)
- Phase 5: Deploy Guest (20 min)
- Phase 6: Test Everything (10 min)

Total: **65 minutes + 1 coffee break** ☕

---

## 🔑 5 Critical Things to Know

1. **Your Host Needs a Static IP**
   ```
   Example: 192.168.1.100
   All Guest VMs must be able to ping it
   ```

2. **Telegram Bot Token is Required**
   ```
   Get from: @BotFather in Telegram
   Format: 123456:ABCDefGHIjklmnoPQRstUVwxyz
   Keep it secret!
   ```

3. **VM Names Must Match Exactly**
   ```
   /add_vm Gaming-PC
   ↓
   Must match exactly in Hyper-V
   ```

4. **Detector Credentials Are Per-VM**
   ```
   Each VM gets unique:
   - Detector_ID (UUID)
   - VM_SECRET_KEY (UUID)
   Keep both saved securely
   ```

5. **Heartbeat Must Work**
   ```
   VM can reach Host on 192.168.1.100:8000
   If not: Check firewall rules
   ```

---

## 📁 Important Files

| File | Purpose | Edit? |
|------|---------|-------|
| `host-controller/.env` | Host config | ✅ **YES** |
| `guest-detector/.env` | Guest config | ✅ **YES** |
| `SETUP.md` | How to deploy | ❌ Read |
| `src/main.py` | Source code | ⚠️ Only if customizing |
| `database.sqlite` | Live database | ❌ Let app manage |

## ⚠️ Common Mistakes (Avoid These!)

- ❌ Running Host and Guest on same machine (won't work for testing)
- ❌ Not editing .env files (won't have bot token)
- ❌ Wrong HOST_LAN_IP (detector can't reach host)
- ❌ Firewall blocking port 8000 (no API communication)
- ❌ VM name doesn't match Hyper-V exactly (VM not recognized)
- ❌ Using HTTP instead of HTTPS (it's LAN-only, so HTTP is okay)
- ❌ Forgetting /token command (won't become admin)

---

## 🔍 Verify Setup Works

After deploying, check these with `Ctrl+C` breakpoints:

```powershell
# 1. Can Guest reach Host?
ping 192.168.1.100          # Should work

# 2. Is API running?
Invoke-WebRequest http://192.168.1.100:8000/api/health

# 3. Is database created?
dir host-controller\database.sqlite

# 4. Bot responds?
# In Telegram: /start → Should get response
```

---

## 📞 Need Help?

### Issue: Bot doesn't respond
1. Check Host Controller still running (PowerShell window)
2. Verify TELEGRAM_BOT_TOKEN in .env is exactly right
3. Restart: Ctrl+C, then `python -m src.main`

### Issue: Detector can't connect
1. Verify HOST_LAN_IP is correct: `ipconfig /all`
2. Verify firewall allows port 8000
3. Verify credentials match from `/add_vm`

### Issue: Shutdown not working
1. Check Detector service is running
2. Check `last_heartbeat` is recent (within 60s)
3. Try `/force_stop` instead

See: **DEPLOYMENT_CHECKLIST.md** for 40+ scenarios

---

## 🎓 Learning Resources

### Understanding the Architecture
- Read: `README.md` "Pillar 1-8" sections
- Diagrams show data flow and security zones
- About 15 minutes

### Command Reference
- Keep: `QUICK_REFERENCE.md` open
- Copy-paste commands from there
- About 5 minutes

### Troubleshooting
- Use: `DEPLOYMENT_CHECKLIST.md`
- Organized by phase + common issues
- Specific fixes for each error

### Source Code Tour
- Start: `host-controller/src/main.py` (entry point)
- Then: `src/db.py` (database operations)
- Then: `bot/commands.py` (Telegram commands)
- Comments explain everything

---

## ✨ Key Features at a Glance

| Feature | Status | Location |
|---------|--------|----------|
| Telegram Bot | ✅ Complete | `src/bot/` |
| FastAPI Server | ✅ Complete | `src/api/` |
| Database | ✅ Complete | `db.py` |
| Hyper-V Control | ✅ Complete | `hypervisor_plugin.py` |
| Guest Detector | ✅ Complete | `guest-detector/src/` |
| AFK Detection | ✅ Complete | `idle_checker.py` |
| Parsec Monitoring | ✅ Complete | `parsec_reader.py` |
| Graceful Shutdown | ✅ Complete | `os_manager.py` |
| Heartbeat Watchdog | ✅ Complete | `main.py` |
| RBAC/Permissions | ✅ Complete | `commands.py` |

---

## 🎯 Your Next 3 Steps

### STEP 1: Choose Your Path (2 min)
- [ ] Quick test (30 min, ignore Guest)
- [ ] Full setup (2 hours, complete deployment)

### STEP 2: Get Telegram Token (5 min)
- [ ] Message @BotFather in Telegram
- [ ] Follow /newbot prompts
- [ ] Copy and save the token

### STEP 3: Follow the Guide (30 min to 2 hours)
- [ ] If Quick: Run `host-controller/run.bat`
- [ ] If Full: Open `SETUP.md` and follow Phase 1-6

---

## 🚀 Ready to Begin?

### For Quick Test:
```
1. Open PowerShell
2. cd C:\Users\example\Desktop\VM software\vm-management-system\host-controller
3. Edit .env with your Telegram token (from @BotFather)
4. Run: python -m src.main
5. In Telegram: /start → /token YOUR_SECRET → /help
```

### For Full Setup:
```
1. Open SETUP.md (detailed guide)
2. Get Telegram token from @BotFather
3. Follow Phase 1-2 for Host setup
4. Test bot with /start and /token
5. Follow Phase 3-5 for Guest setup
```

---

## 💡 Pro Tips

- **Use static Host IP** - Write down 192.168.1.100 (or yours)
- **Save credentials** - Screenshot each VM's Detector_ID + Secret
- **Test manually first** - Run `run.bat` before using services
- **Monitor logs** - PowerShell console shows real-time status
- **Keep .env secure** - Contains bot token, don't share

---

## 📈 What Happens Next

### After 5 Minutes
You'll have a working Telegram bot connected to your host computer.

### After 30 Minutes (Quick Path)
You can test VM control commands in Telegram.

### After 2 Hours (Full Path)
- ✅ Host Controller running as service
- ✅ Guest Detector installed on VM
- ✅ Heartbeats flowing every 60 seconds
- ✅ Full command control via Telegram
- ✅ AFK monitoring active
- ✅ Ready for production

---

## 🎉 Success Looks Like

```
In PowerShell (Host Controller):
  ✅ "Starting VM Manager Host Controller"
  ✅ "API: http://192.168.1.100:8000"
  ✅ "Heartbeat from 550e8400-..." (every 60s)

In Telegram:
  ✅ Bot responds to /start
  ✅ Shows admin commands with /help
  ✅ /dashboard shows VMs as 🟢 online
  ✅ Can click buttons to control VMs

In Database:
  ✅ VMs registered with Detector IDs
  ✅ Last heartbeat timestamps recent
  ✅ User roles show "admin"
```

---

## 🔄 Now What?

Pick one:

**→ I want to test it** (30 min)
- Go to: `host-controller/` directory
- Edit: `.env` file (add Telegram token)
- Run: `run.bat`
- Test: Send `/start` in Telegram

**→ I want full setup** (2 hours)
- Read: `SETUP.md` (start with Phase 1)
- Follow: Step-by-step instructions
- Deploy: Both Host and Guest controllers
- Verify: All components working

**→ I want to understand first** (1 hour)
- Read: `README.md` (architecture overview)
- Check: `QUICK_REFERENCE.md` (commands)
- Review: Source code structure
- Then follow: `SETUP.md` for deployment

---

## 📞 Still Here?

All your questions are answered in:
- **Architecture questions** → README.md
- **Command questions** → QUICK_REFERENCE.md
- **Setup questions** → SETUP.md  
- **Deployment questions** → DEPLOYMENT_CHECKLIST.md
- **Code questions** → Source code (well-commented)

No configuration needed beyond editing `.env` files!

---

## 🎊 You're Ready!

Everything is built, documented, and tested. No additional code needed.

**Start now:** Choose your path above and follow the guide.

**Good luck!** 🚀

---

*Questions? Check the relevant documentation file above.*
*Stuck? Review DEPLOYMENT_CHECKLIST.md troubleshooting section.*
