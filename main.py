import discord
from discord.ext import commands
import logging
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config
from utils.logger import setup_logger
from database.database_manager import DatabaseManager

class InventOnBot(commands.Bot):
    """Main bot class for InventOnBot"""
    
    def __init__(self):
        # Configure bot intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=Config.BOT_PREFIX,
            intents=intents,
            help_command=None
        )
        
        # Initialize components
        self.logger = setup_logger()
        self.db_manager = None
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        try:
            # Initialize database based on configuration
            from config.config import Config
            
            if Config.DATABASE_TYPE == 'supabase':
                from database.supabase_manager import SupabaseManager
                self.db_manager = SupabaseManager()
            else:
                from database.database_manager import DatabaseManager
                self.db_manager = DatabaseManager()
                
            await self.db_manager.initialize()
            
            # Load cogs/extensions
            await self.load_extension('bot.cogs.question_handler')
            await self.load_extension('bot.cogs.admin_commands')
            await self.load_extension('bot.cogs.image_handler')
            await self.load_extension('bot.cogs.faq_system')
            await self.load_extension('bot.cogs.welcome_system')
            #await self.load_extension('bot.cogs.statistics_system')
            
            self.logger.info(f"Bot setup completed successfully with {Config.DATABASE_TYPE} database")
            
        except Exception as e:
            self.logger.error(f"Error during bot setup: {e}")
            raise
    
    async def on_ready(self):
        """Called when bot is ready"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            self.logger.error(f"Failed to sync commands: {e}")
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        self.logger.error(f"Command error: {error}")
        
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        await ctx.send(f"오류가 발생했습니다: {error}")

async def main():
    """Main function to run the bot"""
    try:
        # Validate configuration
        Config.validate()
        
        # Create and start bot
        bot = InventOnBot()
        await bot.start(Config.DISCORD_TOKEN)
        
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())