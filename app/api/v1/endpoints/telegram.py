"""
Telegram webhook endpoint for handling bot updates
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timezone
import logging
from app.database import get_db
from app.services.telegram_service import TelegramService
from app.services.nlp_service import NLPService
from app.models.kid import Kid
from app.models.event import Event as EventModel
from app.schemas.event import EventCreate

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for pending events (callback_query_id -> event_data)
# In production, consider using Redis or database
pending_events: Dict[str, Dict[str, Any]] = {}


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle incoming Telegram webhook updates
    
    This endpoint receives updates from Telegram when:
    - Users send messages to the bot
    - Users click inline buttons (callback queries)
    """
    try:
        # Parse the update
        update_data = await request.json()
        logger.info(f"Received Telegram update: {update_data.get('update_id')}")
        
        # Initialize services
        telegram_service = TelegramService()
        
        # Handle message (new event request)
        if "message" in update_data:
            return await handle_message(update_data["message"], telegram_service, db)
        
        # Handle callback query (button click)
        elif "callback_query" in update_data:
            return await handle_callback_query(update_data["callback_query"], telegram_service, db)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return {"status": "error", "message": str(e)}


async def handle_message(
    message: Dict[str, Any],
    telegram_service: TelegramService,
    db: Session
):
    """
    Handle incoming text messages from users
    
    Args:
        message: Message data from Telegram
        telegram_service: TelegramService instance
        db: Database session
    """
    try:
        # Extract user and chat info
        user = message.get("from", {})
        user_id = user.get("id")
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        
        if not user_id or not chat_id:
            logger.warning("Missing user_id or chat_id in message")
            return {"status": "error", "message": "Missing user info"}
        
        # Verify user authorization
        if not telegram_service.verify_user(user_id):
            await telegram_service.send_unauthorized_message(chat_id, user_id)
            return {"status": "unauthorized"}
        
        # Handle commands
        if text.startswith('/'):
            return await handle_command(text, chat_id, telegram_service, db)
        
        # Parse the message as an event request
        try:
            # Get available kids
            kids = db.query(Kid).all()
            kids_list = [{"id": kid.id, "name": kid.name} for kid in kids]
            
            # Parse event using NLP service
            nlp_service = NLPService()
            event_data = nlp_service.parse_event_from_text(
                message=text,
                kids_list=kids_list,
                timezone_str="America/Los_Angeles"  # Pacific Time (PST/PDT)
            )
            
            # Check for parsing errors
            if "error" in event_data:
                error_msg = f"I couldn't understand that message.\n\nError: {event_data['error']}"
                await telegram_service.send_error_message(chat_id, error_msg)
                return {"status": "parse_error"}
            
            # Map kid names to IDs (case-insensitive matching)
            kid_ids = []
            for kid_name in event_data.get("kid_names", []):
                # Try exact match first, then case-insensitive
                kid = next((k for k in kids if k.name == kid_name), None)
                if not kid:
                    kid = next((k for k in kids if k.name.lower() == kid_name.lower()), None)
                if kid:
                    kid_ids.append(kid.id)
                    logger.info(f"Matched kid name '{kid_name}' to kid ID {kid.id} ({kid.name})")
                else:
                    logger.warning(f"Could not match kid name '{kid_name}' to any kid in database")
            
            # Store kid IDs in event data
            event_data["kid_ids"] = kid_ids
            
            # Generate a unique callback ID for this pending event
            callback_id = f"{chat_id}_{message.get('message_id')}"
            
            # Store pending event
            pending_events[callback_id] = {
                "event_data": event_data,
                "chat_id": chat_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Send confirmation message with buttons
            response = await telegram_service.send_confirmation(
                chat_id=chat_id,
                event_data=event_data,
                callback_data_prefix=callback_id
            )
            
            if response.get("success"):
                # Store message_id for later editing
                pending_events[callback_id]["confirmation_message_id"] = response["message_id"]
            
            return {"status": "confirmation_sent"}
            
        except Exception as e:
            logger.error(f"Error parsing event: {e}")
            error_msg = f"Sorry, I had trouble parsing that message.\n\nPlease try rephrasing or use /help for examples."
            await telegram_service.send_error_message(chat_id, error_msg)
            return {"status": "parse_error", "error": str(e)}
    
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        return {"status": "error", "message": str(e)}


async def handle_callback_query(
    callback_query: Dict[str, Any],
    telegram_service: TelegramService,
    db: Session
):
    """
    Handle callback queries (button clicks) from users
    
    Args:
        callback_query: Callback query data from Telegram
        telegram_service: TelegramService instance
        db: Database session
    """
    try:
        callback_id = callback_query.get("id")
        user_id = callback_query.get("from", {}).get("id")
        message = callback_query.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        message_id = message.get("message_id")
        data = callback_query.get("data", "")
        
        # Parse callback data (format: "callback_id:action")
        parts = data.split(":", 1)
        if len(parts) != 2:
            logger.warning(f"Invalid callback data format: {data}")
            await telegram_service.answer_callback_query(callback_id, "Invalid action")
            return {"status": "error", "message": "Invalid callback data"}
        
        event_callback_id, action = parts
        
        # Get pending event
        pending_event = pending_events.get(event_callback_id)
        if not pending_event:
            logger.warning(f"Pending event not found: {event_callback_id}")
            await telegram_service.answer_callback_query(
                callback_id, 
                "This event request has expired. Please send a new message.",
                show_alert=True
            )
            return {"status": "expired"}
        
        # Verify user is the same one who initiated the request
        if pending_event.get("user_id") != user_id:
            await telegram_service.answer_callback_query(
                callback_id,
                "You cannot confirm someone else's event.",
                show_alert=True
            )
            return {"status": "unauthorized"}
        
        # Handle the action
        if action == "confirm":
            return await confirm_event(
                pending_event,
                callback_id,
                chat_id,
                message_id,
                event_callback_id,
                telegram_service,
                db
            )
        elif action == "cancel":
            return await cancel_event(
                callback_id,
                chat_id,
                message_id,
                event_callback_id,
                telegram_service
            )
        else:
            await telegram_service.answer_callback_query(callback_id, "Unknown action")
            return {"status": "unknown_action"}
    
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        return {"status": "error", "message": str(e)}


async def confirm_event(
    pending_event: Dict[str, Any],
    callback_id: str,
    chat_id: int,
    message_id: int,
    event_callback_id: str,
    telegram_service: TelegramService,
    db: Session
):
    """
    Confirm and create the event
    
    Args:
        pending_event: Pending event data
        callback_id: Telegram callback query ID
        chat_id: Chat ID
        message_id: Message ID to edit
        event_callback_id: Our event callback ID
        telegram_service: TelegramService instance
        db: Database session
    """
    try:
        event_data = pending_event["event_data"]
        
        # Convert parsed data to EventCreate schema
        # Parse times as Pacific time, then convert to UTC for storage
        from zoneinfo import ZoneInfo
        pacific_tz = ZoneInfo("America/Los_Angeles")
        
        # Parse as local time first
        start_datetime_local = datetime.fromisoformat(
            f"{event_data['date']}T{event_data['start_time']}:00"
        ).replace(tzinfo=pacific_tz)
        
        end_datetime_local = datetime.fromisoformat(
            f"{event_data['date']}T{event_data['end_time']}:00"
        ).replace(tzinfo=pacific_tz)
        
        # Convert to UTC
        start_datetime = start_datetime_local.astimezone(timezone.utc)
        end_datetime = end_datetime_local.astimezone(timezone.utc)
        
        # Adjust RRULE if weekday changed due to timezone conversion
        rrule_str = event_data.get("rrule")
        if rrule_str and "BYDAY=" in rrule_str:
            # If the UTC day is different from local day, adjust RRULE
            local_weekday = start_datetime_local.weekday()
            utc_weekday = start_datetime.weekday()
            
            if local_weekday != utc_weekday:
                # Map weekday to RRULE day code
                day_codes = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']
                utc_day_code = day_codes[utc_weekday]
                
                # Replace the BYDAY value with UTC weekday
                import re
                rrule_str = re.sub(r'BYDAY=\w+', f'BYDAY={utc_day_code}', rrule_str)
                logger.info(f"Adjusted RRULE for timezone conversion: {event_data.get('rrule')} → {rrule_str}")
        
        event_create = EventCreate(
            title=event_data["title"],
            location=event_data.get("location"),
            start_utc=start_datetime,
            end_utc=end_datetime,
            rrule=rrule_str,
            exdates=None,
            kid_ids=event_data.get("kid_ids", []),
            category=event_data["category"],
            source="telegram",
            created_by=f"telegram_user_{pending_event['user_id']}"
        )
        
        # Create event in database
        db_event = EventModel(**event_create.model_dump())
        db_event.updated_at = datetime.now(timezone.utc)
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Created event {db_event.id}: {db_event.title}")
        
        # Answer callback query
        await telegram_service.answer_callback_query(
            callback_id,
            "✅ Event created!"
        )
        
        # Edit the message to show success
        success_text = f"✅ *Event Created!*\n\n*{event_data['title']}*\n📆 {event_data['date']} {event_data['start_time']}"
        if event_data.get('is_recurring'):
            from app.services.nlp_service import NLPService
            human_readable = NLPService.rrule_to_human_readable(event_data.get('rrule', ''))
            success_text += f"\n🔁 {human_readable}"
        success_text += f"\n\n_Event ID: {db_event.id}_"
        
        await telegram_service.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=success_text
        )
        
        # Remove from pending events
        del pending_events[event_callback_id]
        
        return {"status": "created", "event_id": db_event.id}
        
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        await telegram_service.answer_callback_query(
            callback_id,
            f"Error creating event: {str(e)}",
            show_alert=True
        )
        return {"status": "error", "message": str(e)}


async def cancel_event(
    callback_id: str,
    chat_id: int,
    message_id: int,
    event_callback_id: str,
    telegram_service: TelegramService
):
    """
    Cancel the event creation
    
    Args:
        callback_id: Telegram callback query ID
        chat_id: Chat ID
        message_id: Message ID to edit
        event_callback_id: Our event callback ID
        telegram_service: TelegramService instance
    """
    try:
        # Answer callback query
        await telegram_service.answer_callback_query(
            callback_id,
            "Event creation cancelled"
        )
        
        # Edit the message
        await telegram_service.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text="❌ Event creation cancelled.\n\nSend a new message to create an event."
        )
        
        # Remove from pending events
        if event_callback_id in pending_events:
            del pending_events[event_callback_id]
        
        return {"status": "cancelled"}
        
    except Exception as e:
        logger.error(f"Error cancelling event: {e}")
        return {"status": "error", "message": str(e)}


async def handle_command(
    command: str,
    chat_id: int,
    telegram_service: TelegramService,
    db: Session
):
    """
    Handle bot commands
    
    Args:
        command: Command text (e.g., "/start", "/help")
        chat_id: Chat ID
        telegram_service: TelegramService instance
        db: Database session
    """
    command = command.lower().split()[0]  # Get just the command, ignore parameters
    
    if command == "/start":
        # Get available kids for help message
        kids = db.query(Kid).all()
        kid_names = [kid.name for kid in kids]
        await telegram_service.send_help_message(chat_id, kid_names)
        return {"status": "help_sent"}
    
    elif command == "/help":
        # Get available kids for help message
        kids = db.query(Kid).all()
        kid_names = [kid.name for kid in kids]
        await telegram_service.send_help_message(chat_id, kid_names)
        return {"status": "help_sent"}
    
    else:
        await telegram_service.send_message(
            chat_id,
            f"Unknown command: {command}\n\nUse /help to see available commands."
        )
        return {"status": "unknown_command"}


@router.get("/setup")
async def setup_webhook(webhook_url: str):
    """
    Setup Telegram webhook URL (development helper)
    
    Args:
        webhook_url: Your webhook URL (e.g., https://your-domain.com/v1/telegram/webhook)
    
    Example:
        GET /v1/telegram/setup?webhook_url=https://example.com/v1/telegram/webhook
    """
    try:
        telegram_service = TelegramService()
        app = await telegram_service.get_application()
        
        # Set webhook
        await app.bot.set_webhook(url=webhook_url)
        
        # Get webhook info
        webhook_info = await app.bot.get_webhook_info()
        
        return {
            "status": "success",
            "webhook_url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count
        }
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook-info")
async def get_webhook_info():
    """
    Get current webhook information (development helper)
    """
    try:
        telegram_service = TelegramService()
        app = await telegram_service.get_application()
        
        webhook_info = await app.bot.get_webhook_info()
        
        return {
            "webhook_url": webhook_info.url,
            "has_custom_certificate": webhook_info.has_custom_certificate,
            "pending_update_count": webhook_info.pending_update_count,
            "last_error_date": webhook_info.last_error_date,
            "last_error_message": webhook_info.last_error_message,
            "max_connections": webhook_info.max_connections
        }
    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/webhook")
async def delete_webhook():
    """
    Delete the webhook (development helper)
    """
    try:
        telegram_service = TelegramService()
        app = await telegram_service.get_application()
        
        await app.bot.delete_webhook()
        
        return {"status": "success", "message": "Webhook deleted"}
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))
