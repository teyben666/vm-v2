# 📚 VM Manager - Documentation Index

Welcome to the complete VM Management System! This index will help you navigate all documentation and code.

---

## 🚀 START HERE

### First Time Users
1. **[GETTING_STARTED.md](GETTING_STARTED.md)** ← Start here! (10 min read)
   - What you have
   - How to choose your path
   - Quick 3-step setup

2. **[README.md](README.md)** (15 min read)
   - Architecture overview  
   - Features explanation
   - Security model
   - Quick start guide

3. **[SETUP.md](SETUP.md)** (30 min follow, 2 hours total)
   - Step-by-step deployment
   - 6 phases with detailed instructions
   - Troubleshooting for each phase
   - Telegram bot setup guide

---

## 📖 Documentation by Purpose

### I Want to Understand How It Works
- **[README.md](README.md)** - Architecture & design
- **[Source Code](host-controller/src/main.py)** - Well-commented implementation

### I Want to Deploy It
- **[SETUP.md](SETUP.md)** - Complete step-by-step guide
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Pre-deploy checklist

### I Want to Use It (Command Reference)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - All commands & config

### I Want to Fix a Problem
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - 40+ troubleshooting scenarios
- **[README.md](README.md)** - Security & architecture details

### I Want to Customize or Extend It
- **[Source Code](host-controller/src/)** - All components with comments
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Database schema reference

---

## 📁 Project Structure

```
vm-management-system/
│
├── 📖 DOCUMENTATION (You are here)
│   ├── GETTING_STARTED.md           ← Quick introduction (5 min)
│   ├── README.md                    ← Full documentation (15 min)
│   ├── SETUP.md                     ← Step-by-step guide (2 hours)
│   ├── QUICK_REFERENCE.md           ← Command cheat sheet (5 min)
│   ├── DEPLOYMENT_CHECKLIST.md      ← Pre/post deployment checks
│   ├── IMPLEMENTATION.md             ← Project status & features
│   └── INDEX.md                     ← This file
│
├── 🖥️ HOST CONTROLLER
│   ├── .env                         ← CONFIG: Edit this!
│   ├── run.bat                      ← Quick start script
│   ├── requirements.txt             ← Python dependencies
│   │
│   └── src/
│       ├── main.py                  ← Entry point (asyncio loop)
│       ├── db.py                    ← Database & ORM operations
│       ├── hypervisor_plugin.py     ← Hyper-V PowerShell integration
│       │
│       ├── bot/
│       │   ├── commands.py          ← Telegram slash commands
│       │   └── handlers.py          ← Inline button callbacks
│       │
│       └── api/
│           └── endpoints.py         ← FastAPI HTTP routes
│
└── 🎮 GUEST DETECTOR
    ├── .env                         ← CONFIG: Edit this!
    ├── run.bat                      ← Test script (manual)
    ├── build.bat                    ← Build .exe for service
    ├── requirements.txt
    │
    └── src/
        ├── main.py                  ← Entry point (monitoring loop)
        ├── idle_checker.py          ← AFK detection via Windows API
        ├── parsec_reader.py         ← Parsec log file monitor
        ├── api_sender.py            ← HTTP heartbeat sender
        └── os_manager.py            ← OS shutdown & commands
```

---

## 🗺️ Quick Navigation

### By File Type

#### 📝 Documentation Files
| File | Purpose | Read Time |
|------|---------|-----------|
| [GETTING_STARTED.md](GETTING_STARTED.md) | Quick intro & path selection | 5 min |
| [README.md](README.md) | Complete architecture & features | 15 min |
| [SETUP.md](SETUP.md) | Step-by-step deployment guide | ー |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Commands & config cheat sheet | 5 min |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Pre-deployment & troubleshooting | ー |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Project status summary | 10 min |

#### 🐍 Python Source Code
| File | Purpose | Lines |
|------|---------|-------|
| `host-controller/src/main.py` | Host entry point (Bot + API + Watchdog) | 250 |
| `host-controller/src/db.py` | Database operations & queries | 350 |
| `host-controller/src/hypervisor_plugin.py` | Hyper-V PowerShell wrapper | 150 |
| `host-controller/src/bot/commands.py` | Telegram bot commands | 400 |
| `host-controller/src/bot/handlers.py` | Button callback handlers | 120 |
| `host-controller/src/api/endpoints.py` | FastAPI HTTP routes | 250 |
| `guest-detector/src/main.py` | Guest entry point (monitoring loop) | 200 |
| `guest-detector/src/idle_checker.py` | Windows API AFK detection | 80 |
| `guest-detector/src/parsec_reader.py` | Parsec log file watcher | 120 |
| `guest-detector/src/api_sender.py` | HTTP heartbeat client | 150 |
| `guest-detector/src/os_manager.py` | OS shutdown executor | 100 |

#### ⚙️ Configuration Files
| File | Required? | Purpose |
|------|-----------|---------|
| `host-controller/.env` | ✅ YES | Host: Bot token, LAN IP, ports |
| `guest-detector/.env` | ✅ YES | Guest: Host IP, credentials, intervals |
| `host-controller/requirements.txt` | ✅ Auto | Python packages to install |
| `guest-detector/requirements.txt` | ✅ Auto | Python packages to install |

#### 🚀 Utility Scripts
| Script | Platform | Purpose |
|--------|----------|---------|
| `host-controller/run.bat` | Windows | Quick test script for Host |
| `guest-detector/run.bat` | Windows | Quick test script for Guest |
| `guest-detector/build.bat` | Windows | Build .exe for service deployment |

---

## 🎯 Common Scenarios

### "I want to test this NOW" (30 minutes)
1. Read: [GETTING_STARTED.md](GETTING_STARTED.md) "Quick Start" section
2. Get: Telegram bot token from @BotFather
3. Edit: `host-controller/.env`
4. Run: `host-controller/run.bat`
5. Test: Send `/start` in Telegram

### "I want to deploy this properly" (2 hours)
1. Read: [SETUP.md](SETUP.md) entire document
2. Follow: 6 phases step-by-step
3. Deploy: Host Controller → Guest Detector
4. Verify: All components connected
5. Monitor: Check logs and Telegram

### "I need to fix a specific problem"
1. Search: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for your issue
2. Read: Troubleshooting section for that phase
3. Check: Example commands and solutions
4. Verify: Steps to confirm fix worked

### "I want to understand the code"
1. Start: [README.md](README.md) architecture sections
2. Read: `host-controller/src/main.py` (entry point)
3. Review: `src/db.py` (data layer)
4. Study: `bot/commands.py` (bot logic)
5. Check: Comments explain each function

### "I need to customize or extend it"
1. Review: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) database schema
2. Understand: Source code structure
3. Research: Specific component you need to modify
4. Change: Make your modifications
5. Test: Verify changes work

---

## 📊 Information By Role

### For System Administrators
- **Read first:** [README.md](README.md) (Architecture & Security)
- **Then read:** [SETUP.md](SETUP.md) (Deployment)
- **Reference:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) (99+ scenarios)
- **Keep handy:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (Commands & config)

### For End Users
- **Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (Commands cheat sheet)
- **Return to:** [README.md](README.md) (Features & usage)
- **For help:** [SETUP.md](SETUP.md) "Troubleshooting" section

### For Developers
- **Architecture:** [README.md](README.md) (Design philosophy)
- **Source:** `src/` directory (Read-through all files)
- **Reference:** [QUICK_REFERENCE.md](QUICK_REFERENCE.md) (Database schema)
- **Extend:** Customize any Python components

### For DevOps/Deployment
- **Guide:** [SETUP.md](SETUP.md) (Step-by-step phases)
- **Checklist:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Service setup:** [SETUP.md](SETUP.md) Phase 7
- **Monitoring:** [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) Monitoring section

---

## 🔍 Search Quick Links

### By Technology
- **Telegram Bot** → [README.md](README.md) Pillar 5 + `bot/commands.py`
- **FastAPI/HTTP API** → [README.md](README.md) Pillar 8 + `api/endpoints.py`
- **SQLite Database** → [README.md](README.md) Pillar 7 + `db.py`
- **Hyper-V PowerShell** → `hypervisor_plugin.py`
- **Windows Service (NSSM)** → [SETUP.md](SETUP.md) Phase 7
- **AFK Detection** → `idle_checker.py`
- **Parsec Integration** → `parsec_reader.py`

### By Feature
- **User Management** → `bot/commands.py` + `db.py`
- **VM Control** → `hypervisor_plugin.py` + `bot/commands.py`
- **Graceful Shutdown** → `os_manager.py` + `api/endpoints.py`
- **Heartbeat Monitoring** → `api/endpoints.py` + `main.py` (watchdog)
- **Security & Auth** → `api/endpoints.py` + `db.py`

### By Configuration
- **Bot Token** → `host-controller/.env`
- **Network Settings** → Both `.env` files (HOST_LAN_IP)
- **Timings** → Both `.env` files (intervals, thresholds)
- **Database** → `host-controller/.env` (DATABASE_PATH)

---

## ✅ Deployment Phases

Refer to [SETUP.md](SETUP.md) for complete phase documentation:

1. **Telegram Bot Setup** (5 min) - Get bot token
2. **Host Controller** (15 min) - Deploy main server
3. **Admin Registration** (5 min) - Login & verify
4. **Add VM** (10 min) - Register first VM
5. **Guest Detector** (20 min) - Deploy to VM
6. **Test Everything** (10 min) - Verify components
7. **Production Services** (15 min) - Install as Windows services

---

## 📞 Getting Help

| Question | Find Answer In |
|----------|----------------|
| "How do I start?" | [GETTING_STARTED.md](GETTING_STARTED.md) |
| "How does it work?" | [README.md](README.md) |
| "How do I deploy it?" | [SETUP.md](SETUP.md) |
| "What commands exist?" | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) |
| "Something is broken" | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |
| "How do I customize it?" | Source code + [README.md](README.md) architecture |
| "What's the status?" | [IMPLEMENTATION.md](IMPLEMENTATION.md) |
| "Where's file X?" | This INDEX.md |

---

## 🎓 Learning Path

### Path A: Quick Test (30 min)
```
1. GETTING_STARTED.md (5 min) → Quick Start section
2. Get Telegram token
3. host-controller/run.bat
4. Test in Telegram
```

### Path B: Full Deployment (2-3 hours)
```
1. GETTING_STARTED.md (5 min) → Overview
2. README.md (15 min) → Understand architecture
3. SETUP.md (Follow Phase 1-7)
4. DEPLOYMENT_CHECKLIST.md → Verify everything
```

### Path C: Deep Understanding (4-5 hours)
```
1. GETTING_STARTED.md (5 min)
2. README.md (15 min) → Read all sections
3. QUICK_REFERENCE.md (5 min) → Database schema
4. Source code tour (30 min) → All Python files
5. SETUP.md (Follow phases)
6. Customize & extend (30+ min)
```

---

## 🎉 You're All Set!

Everything is implemented and documented. Choose your path above and follow the corresponding guide.

**Fastest path:** [GETTING_STARTED.md](GETTING_STARTED.md) → Quick Start (5 min read)

**Most complete:** [SETUP.md](SETUP.md) → Full deployment (2 hours)

---

*Last updated: April 4, 2026*
*Total code: 1,900+ lines | Total documentation: 10,000+ words*
*Status: Ready for production ✅*
