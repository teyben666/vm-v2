"""Host Controller - Main Entry Point.

Runs:
1. Telegram Bot (command listener + inline callbacks)
2. FastAPI HTTP Server (for VM heartbeats)
3. Watchdog Thread (monitor heartbeat timeouts)
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
)
from fastapi import FastAPI
from uvicorn import Server, Config
import aiosqlite

# Load environment variables from .env file
load_dotenv()

from src import db
from src.api.endpoints import app as api_app
from src.bot import commands, handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HOST_LAN_IP = os.getenv("HOST_LAN_IP", "192.168.1.100")
API_PORT = int(os.getenv("API_PORT", 8000))
HEARTBEAT_TIMEOUT_MINUTES = int(os.getenv("HEARTBEAT_TIMEOUT_MINUTES", 3))

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in .env file")


class VMWatchdog:
    """Monitor VM heartbeats and trigger force-kill if needed."""

    def __init__(self, bot_app: Application):
        self.bot_app = bot_app
        self.running = False

    async def run(self):
        """Main watchdog loop."""
        self.running = True
        logger.info("Watchdog started")

        while self.running:
            try:
                await self._check_heartbeats()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Watchdog error: {e}", exc_info=True)
                await asyncio.sleep(30)

    async def _check_heartbeats(self):
        """Check all online VMs for missed heartbeats."""
        vms = await db.get_all_vms()
        timeout = timedelta(minutes=HEARTBEAT_TIMEOUT_MINUTES)
        now = datetime.utcnow()

        for vm in vms:
            if vm["status"] != "online":
                continue

            if not vm["last_heartbeat"]:
                continue

            last_heartbeat = datetime.fromisoformat(vm["last_heartbeat"])
            time_since = now - last_heartbeat

            if time_since > timeout:
                logger.warning(
                    f"VM {vm['detector_id']} missed heartbeat "
                    f"({time_since.total_seconds():.0f}s)"
                )
                
                # Alert admin via Telegram
                await self._alert_admins(
                    f"🚨 **Heartbeat Timeout**\n\n"
                    f"VM: {vm['hypervisor_name']}\n"
                    f"Detector ID: {vm['detector_id']}\n"
                    f"Last heartbeat: {time_since.total_seconds():.0f}s ago\n\n"
                    f"This may indicate detector process crash or tampering."
                )
                
                # Mark as offline
                await db.update_vm_status(vm["detector_id"], "offline")

    async def _alert_admins(self, message: str):
        """Send alert to all admins."""
        users = await db.get_all_users()
        admins = [u for u in users if u["role"] == "admin" and not u["is_banned"]]

        for admin in admins:
            try:
                # Validate telegram_id is numeric
                try:
                    chat_id = int(admin["telegram_id"])
                except (ValueError, TypeError):
                    logger.error(f"Invalid telegram_id format for admin: {admin['telegram_id']}")
                    continue
                
                await self.bot_app.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Failed to alert admin {admin['telegram_id']}: {e}")

    def stop(self):
        """Stop the watchdog."""
        self.running = False
        logger.info("Watchdog stopped")


class ControllerApp:
    """Main application that runs Bot + API + Watchdog."""

    def __init__(self):
        self.bot_app: Application = None
        self.api_server: Server = None
        self.watchdog: VMWatchdog = None

    async def setup_bot(self):
        """Configure and return Telegram bot application."""
        self.bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # User Commands
        self.bot_app.add_handler(CommandHandler("start", commands.start))
        self.bot_app.add_handler(CommandHandler("register", commands.register_user_cmd))
        self.bot_app.add_handler(CommandHandler("dashboard", commands.dashboard))
        self.bot_app.add_handler(CommandHandler("start_vm", commands.start_vm_cmd))
        self.bot_app.add_handler(CommandHandler("help", commands.help_cmd))

        # Admin Commands
        self.bot_app.add_handler(
            ConversationHandler(
                entry_points=[CommandHandler("add_vm", commands.add_vm_start)],
                states={
                    commands.AWAITING_VM_NAME: [
                        MessageHandler(filters.TEXT, commands.add_vm_name)
                    ]
                },
                fallbacks=[]
            )
        )
        self.bot_app.add_handler(CommandHandler("stop_vm", commands.stop_vm_cmd))
        self.bot_app.add_handler(CommandHandler("force_stop", commands.force_stop_cmd))
        self.bot_app.add_handler(CommandHandler("users", commands.users_cmd))
        self.bot_app.add_handler(CommandHandler("ban", commands.ban_user_cmd))
        self.bot_app.add_handler(CommandHandler("pardon", commands.pardon_user_cmd))
        self.bot_app.add_handler(CommandHandler("approve", commands.approve_cmd))
        self.bot_app.add_handler(CommandHandler("promote", commands.promote_cmd))
        self.bot_app.add_handler(CommandHandler("assign", commands.assign_vm_cmd))
        self.bot_app.add_handler(CommandHandler("delete_user", commands.delete_user_cmd))
        self.bot_app.add_handler(CommandHandler("token", commands.token_cmd))
        self.bot_app.add_handler(CommandHandler("delete_vm", commands.delete_vm_cmd))

        # Callback Handlers
        self.bot_app.add_handler(
            CallbackQueryHandler(handlers.vm_info_callback, pattern=r"^vm_info_")
        )
        self.bot_app.add_handler(
            CallbackQueryHandler(handlers.start_vm_callback, pattern=r"^start_vm_")
        )
        self.bot_app.add_handler(
            CallbackQueryHandler(handlers.stop_vm_callback, pattern=r"^stop_vm_")
        )
        self.bot_app.add_handler(
            CallbackQueryHandler(handlers.force_vm_callback, pattern=r"^force_vm_")
        )
        self.bot_app.add_handler(
            CallbackQueryHandler(handlers.confirm_add_vm_callback, pattern=r"^confirm_add_vm")
        )
        self.bot_app.add_handler(
            CallbackQueryHandler(handlers.cancel_add_vm_callback, pattern=r"^cancel_add_vm")
        )

        logger.info("Bot configured")

    async def start(self):
        """Start all components."""
        # Initialize database
        await db.init_database()
        logger.info("Database initialized")

        # Setup bot
        await self.setup_bot()
        
        # Initialize and start bot
        await self.bot_app.initialize()
        await self.bot_app.start()

        # Setup watchdog
        self.watchdog = VMWatchdog(self.bot_app)

        # Setup and start API server
        config = Config(
            app=api_app,
            host=HOST_LAN_IP,
            port=API_PORT,
            log_level="info"
        )
        self.api_server = Server(config)

        # Run all components concurrently
        try:
            await asyncio.gather(
                self._bot_polling(),
                self.api_server.serve(),
                self.watchdog.run(),
                return_exceptions=True
            )
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            await self.stop()

    async def _bot_polling(self):
        """Async polling loop for the bot using get_updates."""
        try:
            offset = None
            while True:
                try:
                    # Get updates from Telegram
                    updates = await self.bot_app.bot.get_updates(timeout=30, offset=offset)
                    
                    for update in updates:
                        # Process the update through the bot's handlers
                        await self.bot_app.process_update(update)
                        offset = update.update_id + 1
                    
                    # Small delay to prevent tight loop
                    if not updates:
                        await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error in bot polling: {e}")
                    await asyncio.sleep(1)
        finally:
            await self.bot_app.stop()

    async def stop(self):
        """Stop all components gracefully."""
        logger.info("Stopping all components...")

        if self.watchdog:
            self.watchdog.stop()

        if self.bot_app:
            await self.bot_app.stop()

        if self.api_server:
            self.api_server.should_exit = True

        logger.info("All components stopped")


async def main():
    """Entry point."""
    logger.info(f"Starting VM Manager Host Controller")
    logger.info(f"  API: http://{HOST_LAN_IP}:{API_PORT}")
    logger.info(f"  Heartbeat timeout: {HEARTBEAT_TIMEOUT_MINUTES} minutes")

    app = ControllerApp()
    await app.start()


if __name__ == "__main__":
    asyncio.run(main())
