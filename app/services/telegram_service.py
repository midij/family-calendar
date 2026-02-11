"""
Telegram Service for handling bot interactions and webhook management
"""

from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """Service for Telegram bot interactions"""
    
    def __init__(self):
        """Initialize Telegram bot"""
        if not settings.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not configured")
        
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.allowed_user_ids = self._parse_allowed_users()
        self.application = None
    
    def _parse_allowed_users(self) -> List[int]:
        """Parse comma-separated user IDs from config"""
        if not settings.TELEGRAM_ALLOWED_USER_IDS:
            logger.warning("No TELEGRAM_ALLOWED_USER_IDS configured")
            return []
        
        try:
            user_ids = [
                int(uid.strip()) 
                for uid in settings.TELEGRAM_ALLOWED_USER_IDS.split(',') 
                if uid.strip()
            ]
            return user_ids
        except ValueError as e:
            logger.error(f"Error parsing TELEGRAM_ALLOWED_USER_IDS: {e}")
            return []
    
    async def get_application(self) -> Application:
        """Get or create the Telegram Application instance"""
        if self.application is None:
            self.application = Application.builder().token(self.bot_token).build()
        return self.application
    
    def verify_user(self, user_id: int) -> bool:
        """
        Check if user is authorized to use the bot
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            True if authorized, False otherwise
        """
        if not self.allowed_user_ids:
            logger.warning("No allowed users configured - denying access")
            return False
        
        is_allowed = user_id in self.allowed_user_ids
        if not is_allowed:
            logger.warning(f"Unauthorized access attempt from user {user_id}")
        
        return is_allowed
    
    async def send_message(
        self, 
        chat_id: int, 
        text: str, 
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a chat
        
        Args:
            chat_id: Chat ID to send to
            text: Message text
            reply_markup: Optional inline keyboard markup
            
        Returns:
            Message info dict
        """
        try:
            app = await self.get_application()
            message = await app.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return {
                "message_id": message.message_id,
                "chat_id": message.chat_id,
                "success": True
            }
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_confirmation(
        self, 
        chat_id: int, 
        event_data: Dict[str, Any],
        callback_data_prefix: str = "event"
    ) -> Dict[str, Any]:
        """
        Send event confirmation message with inline buttons
        
        Args:
            chat_id: Chat ID to send to
            event_data: Parsed event data
            callback_data_prefix: Prefix for callback data (default: "event")
            
        Returns:
            Message info dict
        """
        # Build confirmation message
        message_lines = ["📅 *Create this event?*\n"]
        
        # Title
        title = event_data.get('title', 'Untitled Event')
        message_lines.append(f"*{title}*")
        
        # Date and time
        date = event_data.get('date', '')
        start_time = event_data.get('start_time', '')
        end_time = event_data.get('end_time', '')
        if date:
            message_lines.append(f"📆 {date}")
        if start_time:
            time_str = f"⏰ {start_time}"
            if end_time:
                time_str += f" - {end_time}"
            message_lines.append(time_str)
        
        # Location
        location = event_data.get('location')
        if location:
            message_lines.append(f"📍 {location}")
        
        # Kids
        kid_names = event_data.get('kid_names', [])
        if kid_names:
            message_lines.append(f"👥 {', '.join(kid_names)}")
        
        # Category
        category = event_data.get('category', '')
        if category:
            category_emoji = {
                'school': '🏫',
                'after-school': '🎯',
                'family': '👨‍👩‍👧‍👦',
                'sports': '⚽',
                'education': '📚',
                'health': '🏥'
            }
            emoji = category_emoji.get(category, '📋')
            message_lines.append(f"{emoji} {category.title()}")
        
        # Recurring info
        if event_data.get('is_recurring'):
            rrule = event_data.get('rrule', '')
            if rrule:
                from app.services.nlp_service import NLPService
                human_readable = NLPService.rrule_to_human_readable(rrule)
                message_lines.append(f"🔁 {human_readable}")
        
        # Missing fields warning
        missing_fields = event_data.get('missing_fields', [])
        if missing_fields and missing_fields != ['kid_names']:
            message_lines.append(f"\n⚠️ Missing: {', '.join(missing_fields)}")
        
        # Confidence warning
        confidence = event_data.get('confidence', 'medium')
        if confidence == 'low':
            message_lines.append("\n⚠️ Low confidence - please verify details")
        
        message_text = "\n".join(message_lines)
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=f"{callback_data_prefix}:confirm"),
                InlineKeyboardButton("❌ Cancel", callback_data=f"{callback_data_prefix}:cancel")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        return await self.send_message(chat_id, message_text, reply_markup)
    
    async def answer_callback_query(
        self, 
        callback_query_id: str, 
        text: str = "",
        show_alert: bool = False
    ) -> bool:
        """
        Answer a callback query (button click)
        
        Args:
            callback_query_id: Callback query ID
            text: Text to show (optional)
            show_alert: Whether to show as alert (default: False)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            app = await self.get_application()
            await app.bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text,
                show_alert=show_alert
            )
            return True
        except Exception as e:
            logger.error(f"Error answering callback query: {e}")
            return False
    
    async def edit_message_text(
        self, 
        chat_id: int, 
        message_id: int, 
        text: str,
        reply_markup: Optional[InlineKeyboardMarkup] = None
    ) -> bool:
        """
        Edit an existing message
        
        Args:
            chat_id: Chat ID
            message_id: Message ID to edit
            text: New text
            reply_markup: Optional new inline keyboard
            
        Returns:
            True if successful, False otherwise
        """
        try:
            app = await self.get_application()
            await app.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return True
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return False
    
    async def send_error_message(
        self, 
        chat_id: int, 
        error_message: str
    ) -> Dict[str, Any]:
        """
        Send an error message to the user
        
        Args:
            chat_id: Chat ID to send to
            error_message: Error message text
            
        Returns:
            Message info dict
        """
        text = f"❌ *Error*\n\n{error_message}\n\nPlease try again or use /help for guidance."
        return await self.send_message(chat_id, text)
    
    async def send_help_message(
        self, 
        chat_id: int,
        kid_names: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send help message with examples
        
        Args:
            chat_id: Chat ID to send to
            kid_names: List of available kid names
            
        Returns:
            Message info dict
        """
        kids_str = ", ".join(kid_names) if kid_names else "No kids configured"
        
        help_text = f"""📅 *Family Calendar Bot*

Send me a message describing an event, and I'll create it for you!

*Available kids:* {kids_str}

*Examples:*

📌 *One-time events:*
• "Soccer practice for Emma tomorrow at 4pm"
• "Dentist appointment next Tuesday 2pm"
• "Family dinner this Friday 6pm at Luigi's"

📌 *Recurring events:*
• "Piano lessons every Tuesday at 4pm"
• "Swimming practice every Monday and Wednesday 5pm"
• "Study time every weekday at 6pm"
• "Dentist checkup first Friday of each month"

*Categories:* school, after-school, family, sports, education, health

*Commands:*
/help - Show this message
/start - Start the bot"""
        
        return await self.send_message(chat_id, help_text)
    
    async def send_unauthorized_message(
        self, 
        chat_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Send unauthorized access message
        
        Args:
            chat_id: Chat ID to send to
            user_id: User's Telegram ID
            
        Returns:
            Message info dict
        """
        text = f"""🚫 *Unauthorized Access*

Your user ID: `{user_id}`

You are not authorized to use this bot. Please contact the bot administrator to request access.

Your user ID must be added to the bot's configuration."""
        
        return await self.send_message(chat_id, text)
