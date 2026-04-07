"""Telegram bot commands handler."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatAction
import os
import uuid

from src import db
from src.hypervisor_plugin import get_hypervisor_plugin

logger = logging.getLogger(__name__)

# States for conversation handlers
AWAITING_VM_NAME, AWAITING_CONFIRMATION = range(2)


async def is_admin(telegram_id: str) -> bool:
    """Check if user is admin."""
    user = await db.get_user(telegram_id)
    return user and user["role"] == "admin"


async def is_banned(telegram_id: str) -> bool:
    """Check if user is banned."""
    user = await db.get_user(telegram_id)
    return user and user["is_banned"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show welcome message."""
    telegram_id = str(update.effective_user.id)
    
    if await is_banned(telegram_id):
        await update.message.reply_text("❌ You have been banned from using this bot.")
        return
    
    user = await db.get_user(telegram_id)
    
    if not user:
        # First time user - register them
        username = update.effective_user.username or "Unknown"
        await db.register_user(telegram_id, username)
        await update.message.reply_text(
            "👋 Welcome to VM Manager!\n\n"
            "You've been registered. Your access is pending admin approval.\n"
            "Use /register to request access."
        )
    elif user["role"] == "pending":
        await update.message.reply_text(
            "⏳ Your access is still pending admin approval.\n"
            "Please wait for an admin to grant you access."
        )
    else:
        await update.message.reply_text(
            "✅ Welcome to VM Manager!\n\n"
            "Use:\n"
            "/dashboard - View your VMs\n"
            "/help - Show all commands"
        )


async def register_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register command - request access."""
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username or "Unknown"
    
    user = await db.get_user(telegram_id)
    
    if user and user["role"] != "pending":
        await update.message.reply_text("✅ You already have access to the bot.")
        return
    
    if not user:
        await db.register_user(telegram_id, username)
    
    await update.message.reply_text(
        "📝 Registration request sent!\n\n"
        "An admin will review your request. Please wait for approval."
    )


async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show VMs - all VMs for admins, assigned VMs for regular users."""
    telegram_id = str(update.effective_user.id)
    
    if await is_banned(telegram_id):
        await update.message.reply_text("❌ You have been banned.")
        return
    
    user = await db.get_user(telegram_id)
    if not user or user["role"] == "pending":
        await update.message.reply_text("❌ You don't have access yet.")
        return
    
    # Admin sees all VMs, regular users see only assigned VMs
    if user["role"] == "admin":
        vms = await db.get_all_vms()
        dashboard_title = "📊 All VMs (Admin View):"
    else:
        vms = await db.get_vms_by_user(telegram_id)
        dashboard_title = "📊 Your Assigned VMs:"
    
    if not vms:
        await update.message.reply_text("📭 No VMs available.")
        return
    
    # Build inline keyboard with status
    buttons = []
    for vm in vms:
        status_icon = "🟢" if vm["status"] == "online" else "🔴"
        assigned = f" (→ {vm['assigned_user_id']})" if vm["assigned_user_id"] else " (unassigned)"
        button_text = f"{status_icon} {vm['hypervisor_name']}{assigned}"
        buttons.append([
            InlineKeyboardButton(
                button_text,
                callback_data=f"vm_info_{vm['detector_id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(
        dashboard_title,
        reply_markup=keyboard
    )


async def start_vm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start a VM: /start_vm <vm_id>"""
    telegram_id = str(update.effective_user.id)
    
    if await is_banned(telegram_id):
        await update.message.reply_text("❌ You have been banned.")
        return
    
    user = await db.get_user(telegram_id)
    if not user or user["role"] == "pending":
        await update.message.reply_text("❌ You don't have access yet. Wait for admin approval.")
        return
    
    if not context.args or len(context.args) == 0:
        await update.message.reply_text(
            "❌ Usage: /start_vm <detector_id>"
        )
        return
    
    detector_id = context.args[0]
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await update.message.reply_text("❌ VM not found.")
        return
    
    # Check permissions: assigned user or admin only
    is_user_admin = user["role"] == "admin"
    
    if vm["assigned_user_id"] and vm["assigned_user_id"] != telegram_id:
        await update.message.reply_text("❌ You don't have permission to control this VM.")
        return
    
    if not vm["assigned_user_id"] and not is_user_admin:
        await update.message.reply_text("❌ This VM is unassigned. Only admins can control it.")
        return
    
    # Start VM via hypervisor
    hypervisor = get_hypervisor_plugin()
    success, message = hypervisor.start_vm(vm["hypervisor_name"])
    
    if success:
        await db.update_vm_status(detector_id, "online")
        await update.message.reply_text(f"✅ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    user = await db.get_user(str(update.effective_user.id))
    
    text = "📖 **Available Commands**\n\n"
    text += "/dashboard - View your assigned VMs\n"
    text += "/start_vm <id> - Start a VM\n"
    text += "/register - Request access\n"
    text += "/help - Show this message\n"
    
    if user and user["role"] == "admin":
        text += "\n🔐 **Admin Commands (Shutdown & Management)**\n\n"
        text += "/add_vm - Add new VM\n"
        text += "/delete_vm <detector_id> - Delete a VM\n"
        text += "/assign <detector_id> <user_id> - Assign VM to user\n"
        text += "/stop_vm <id> - Graceful shutdown\n"
        text += "/force_stop <id> - Force shutdown\n"
        text += "/users - List all users\n"
        text += "/approve <user_id> - Approve pending user as regular user\n"
        text += "/promote <user_id> - Make user admin\n"
        text += "/ban <user_id> - Ban user\n"
        text += "/pardon <user_id> - Unban user\n"
        text += "/delete_user <user_id> - Delete user permanently\n"
        text += "/token <secret> - Become admin\n"
    else:
        text += "\n📝 **Regular Users**\n"
        text += "• Can only start VMs and view the dashboard\n"
        text += "• Cannot stop or force-stop VMs\n"
        text += "• Contact admin for shutdown requests\n"
    
    await update.message.reply_text(text)


# ============ ADMIN COMMANDS ============

async def add_vm_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add VM conversation."""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "📝 What is the VM name in your hypervisor?\n"
        "(Example: VM-01, Windows-Server, etc.)"
    )
    
    return AWAITING_VM_NAME


async def add_vm_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive VM name and confirm."""
    vm_name = update.message.text.strip()
    context.user_data["vm_name"] = vm_name
    
    # Generate credentials
    detector_id = str(uuid.uuid4())
    secret_key = str(uuid.uuid4())
    
    context.user_data["detector_id"] = detector_id
    context.user_data["secret_key"] = secret_key
    
    text = (
        f"✅ VM Details:\n\n"
        f"**VM Name:** `{vm_name}`\n"
        f"**Detector ID:** `{detector_id}`\n"
        f"**Secret Key:** `{secret_key}`\n\n"
        f"Is this correct?"
    )
    
    buttons = [
        [InlineKeyboardButton("✅ Yes", callback_data="confirm_add_vm")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_add_vm")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )
    
    return ConversationHandler.END


async def stop_vm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Queue a graceful shutdown: /stop_vm <detector_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /stop_vm <detector_id>")
        return
    
    detector_id = context.args[0]
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await update.message.reply_text("❌ VM not found.")
        return
    
    await db.set_vm_pending_shutdown(detector_id)
    await update.message.reply_text(
        f"⏸️ Graceful shutdown queued for {vm['hypervisor_name']}\n"
        "The detector will execute it on next heartbeat."
    )


async def force_stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force shutdown: /force_stop <detector_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /force_stop <detector_id>")
        return
    
    detector_id = context.args[0]
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await update.message.reply_text("❌ VM not found.")
        return
    
    hypervisor = get_hypervisor_plugin()
    success, message = hypervisor.stop_vm(vm["hypervisor_name"], force=True)
    
    if success:
        await db.update_vm_status(detector_id, "offline")
        await update.message.reply_text(f"⚡ {message}")
    else:
        await update.message.reply_text(f"❌ {message}")


async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all users."""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    users = await db.get_all_users()
    
    if not users:
        await update.message.reply_text("📭 No users registered.")
        return
    
    text = "👥 **Registered Users:**\n\n"
    for user in users:
        status = "🚫 Banned" if user["is_banned"] else f"{user['role']}"
        text += f"• {user['username']} ({user['telegram_id']}) - {status}\n"
    
    await update.message.reply_text(text, parse_mode="Markdown")


async def ban_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user: /ban <telegram_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /ban <telegram_id>")
        return
    
    target_id = context.args[0]
    user = await db.get_user(target_id)
    
    if not user:
        await update.message.reply_text("❌ User not found.")
        return
    
    await db.ban_user(target_id)
    await update.message.reply_text(f"🚫 Banned {user['username']}")


async def pardon_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user: /pardon <telegram_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /pardon <telegram_id>")
        return
    
    target_id = context.args[0]
    user = await db.get_user(target_id)
    
    if not user:
        await update.message.reply_text("❌ User not found.")
        return
    
    await db.unban_user(target_id)
    await update.message.reply_text(f"✅ Pardoned {user['username']}")


async def promote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote to admin: /promote <telegram_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /promote <telegram_id>")
        return
    
    target_id = context.args[0]
    user = await db.get_user(target_id)
    
    if not user:
        await update.message.reply_text("❌ User not found.")
        return
    
    await db.promote_to_admin(target_id)
    await update.message.reply_text(f"👤 Promoted {user['username']} to admin")


async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve pending user to regular user: /approve <telegram_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /approve <telegram_id>")
        return
    
    target_id = context.args[0]
    user = await db.get_user(target_id)
    
    if not user:
        await update.message.reply_text("❌ User not found.")
        return
    
    if user["role"] != "pending":
        await update.message.reply_text(f"⚠️ {user['username']} is already {user['role']}.")
        return
    
    success = await db.approve_to_user(target_id)
    if success:
        await update.message.reply_text(f"✅ Approved {user['username']} as regular user")
    else:
        await update.message.reply_text("❌ Failed to approve user.")


async def assign_vm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Assign a VM to a user: /assign <detector_id> <user_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /assign <detector_id> <user_id>")
        return
    
    detector_id = context.args[0]
    user_id = context.args[1]
    
    # Check if VM exists
    vm = await db.get_vm(detector_id)
    if not vm:
        await update.message.reply_text("❌ VM not found.")
        return
    
    # Check if user exists
    user = await db.get_user(user_id)
    if not user:
        await update.message.reply_text("❌ User not found.")
        return
    
    # Assign VM to user
    success = await db.assign_vm(detector_id, user_id)
    if success:
        await update.message.reply_text(
            f"✅ VM assigned successfully!\n\n"
            f"VM: {vm['hypervisor_name']}\n"
            f"Assigned to: {user['username']}\n"
            f"Detector ID: {detector_id}"
        )
    else:
        await update.message.reply_text("❌ Failed to assign VM.")


async def delete_user_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a user: /delete_user <telegram_id>"""
    admin_id = str(update.effective_user.id)
    if not await is_admin(admin_id):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /delete_user <telegram_id>")
        return
    
    target_id = context.args[0]
    user = await db.get_user(target_id)
    
    if not user:
        await update.message.reply_text("❌ User not found.")
        return
    
    # Prevent self-deletion
    if target_id == admin_id:
        await update.message.reply_text("❌ You cannot delete yourself!")
        return
    
    await db.delete_user(target_id)
    await update.message.reply_text(f"🗑️ Deleted user {user['username']} and unassigned their VMs")


async def token_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Become admin with token: /token <secret>"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /token <secret_token>")
        return
    
    telegram_id = str(update.effective_user.id)
    provided_token = context.args[0]
    admin_token = os.getenv("ADMIN_SECRET_TOKEN")
    
    # Rate limiting: track failed attempts
    failed_key = f"token_attempts_{telegram_id}"
    current_attempts = context.user_data.get(failed_key, 0)
    
    if current_attempts >= 3:
        logger.warning(f"Token rate limit exceeded for user {telegram_id}")
        await update.message.reply_text("❌ Too many failed attempts. Wait and try again.")
        return
    
    if provided_token != admin_token:
        current_attempts += 1
        context.user_data[failed_key] = current_attempts
        logger.warning(f"Invalid admin token attempt from {telegram_id} ({current_attempts}/3)")
        await update.message.reply_text(f"❌ Invalid token. ({current_attempts}/3 attempts)")
        return
    
    # Successful token - promote to admin
    await db.promote_to_admin(telegram_id)
    context.user_data.pop(failed_key, None)  # Clear attempt counter
    await update.message.reply_text("✅ You are now an admin!")
    logger.info(f"User {telegram_id} promoted to admin via token")


async def delete_vm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a VM: /delete_vm <detector_id>"""
    if not await is_admin(str(update.effective_user.id)):
        await update.message.reply_text("❌ Admin only.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /delete_vm <detector_id>")
        return
    
    detector_id = context.args[0]
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await update.message.reply_text("❌ VM not found.")
        return
    
    success = await db.delete_vm(detector_id)
    
    if success:
        await update.message.reply_text(
            f"✅ VM deleted successfully!\n\n"
            f"VM Name: {vm['hypervisor_name']}\n"
            f"Detector ID: {detector_id}\n\n"
            f"This VM has been removed from the database."
        )
    else:
        await update.message.reply_text("❌ Failed to delete VM.")
