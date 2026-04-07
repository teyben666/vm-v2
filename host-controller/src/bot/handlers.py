"""Callback handlers for inline buttons."""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from src import db
from src.hypervisor_plugin import get_hypervisor_plugin


async def is_admin(telegram_id: str) -> bool:
    """Check if user is admin."""
    user = await db.get_user(telegram_id)
    return user and user["role"] == "admin"

logger = logging.getLogger(__name__)


async def vm_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle VM info button click."""
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(query.from_user.id)
    detector_id = query.data.replace("vm_info_", "")
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await query.edit_message_text("❌ VM not found.")
        return
    
    status_icon = "🟢" if vm["status"] == "online" else "🔴"
    
    text = (
        f"{status_icon} **{vm['hypervisor_name']}**\n\n"
        f"**Status:** {vm['status']}\n"
        f"**Last Heartbeat:** {vm['last_heartbeat'] or 'Never'}\n"
        f"**Assigned User:** {vm['assigned_user_id'] or 'Unassigned'}\n\n"
        f"**Detector ID:** `{vm['detector_id']}`"
    )
    
    buttons = []
    user_is_admin = await is_admin(telegram_id)
    
    if vm["status"] == "online":
        # Only admins can stop VMs
        if user_is_admin:
            buttons.append(("⏸️ Stop", f"stop_vm_{detector_id}"))
            buttons.append(("⚡ Force Stop", f"force_vm_{detector_id}"))
        # Regular users see no action buttons when VM is online
    else:
        # Everyone can start VMs
        buttons.append(("▶️ Start", f"start_vm_{detector_id}"))
    
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = None
    if buttons:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text, callback_data=cb)] for text, cb in buttons]
        )
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


async def start_vm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start VM via callback."""
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(query.from_user.id)
    
    # Permission check: must not be pending or banned
    user = await db.get_user(telegram_id)
    if not user or user["role"] == "pending":
        await query.edit_message_text("❌ Admin only approved users can start VMs.")
        return
    
    if user["is_banned"]:
        await query.edit_message_text("❌ You have been banned.")
        return
    
    detector_id = query.data.replace("start_vm_", "")
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await query.edit_message_text("❌ VM not found.")
        return
    
    # Verify user is assigned to VM or is admin
    is_user_admin = user["role"] == "admin"
    if vm["assigned_user_id"] and vm["assigned_user_id"] != telegram_id and not is_user_admin:
        await query.edit_message_text("❌ You don't have permission to start this VM.")
        return
    
    hypervisor = get_hypervisor_plugin()
    success, message = hypervisor.start_vm(vm["hypervisor_name"])
    
    if success:
        await db.update_vm_status(detector_id, "online")
        await query.edit_message_text(f"✅ {message}")
    else:
        await query.edit_message_text(f"❌ {message}")


async def stop_vm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stop VM via callback - graceful shutdown (admin only)."""
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(query.from_user.id)
    if not await is_admin(telegram_id):
        await query.edit_message_text("❌ Admin only.")
        return
    
    detector_id = query.data.replace("stop_vm_", "")
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await query.edit_message_text("❌ VM not found.")
        return
    
    await db.set_vm_pending_shutdown(detector_id)
    await query.edit_message_text(
        f"⏸️ Graceful shutdown queued.\n"
        f"Will execute on next heartbeat."
    )


async def force_vm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force stop VM via callback (admin only)."""
    query = update.callback_query
    await query.answer()
    
    telegram_id = str(query.from_user.id)
    if not await is_admin(telegram_id):
        await query.edit_message_text("❌ Admin only.")
        return
    
    detector_id = query.data.replace("force_vm_", "")
    vm = await db.get_vm(detector_id)
    
    if not vm:
        await query.edit_message_text("❌ VM not found.")
        return
    
    hypervisor = get_hypervisor_plugin()
    success, message = hypervisor.stop_vm(vm["hypervisor_name"], force=True)
    
    if success:
        await db.update_vm_status(detector_id, "offline")
        await query.edit_message_text(f"⚡ {message}")
    else:
        await query.edit_message_text(f"❌ {message}")


async def confirm_add_vm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm adding VM."""
    query = update.callback_query
    await query.answer()
    
    detector_id = context.user_data.get("detector_id")
    secret_key = context.user_data.get("secret_key")
    vm_name = context.user_data.get("vm_name")
    
    success = await db.add_vm(detector_id, vm_name, secret_key)
    
    if success:
        text = (
            f"✅ VM added successfully!\n\n"
            f"VM Name: {vm_name}\n"
            f"Detector ID: {detector_id}\n"
            f"Secret Key: {secret_key}\n\n"
            f"📋 Install on Guest:\n"
            f"1. Copy the Detector ID and Secret Key to the guest's .env file\n"
            f"2. Run the guest detector\n\n"
            f"Use: /assign {detector_id} USER_ID to assign to a user"
        )
    else:
        text = "❌ Failed to add VM (duplicate name or ID)"
    
    await query.edit_message_text(text)
    context.user_data.clear()


async def cancel_add_vm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel adding VM."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ Cancelled.")
    context.user_data.clear()
