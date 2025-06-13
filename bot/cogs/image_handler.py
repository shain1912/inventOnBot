import discord
from discord.ext import commands
from typing import Optional

class ImageHandler(commands.Cog):
    """Handle image uploads and attachments"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle messages with image attachments"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if message has attachments
        if not message.attachments:
            return
        
        # Check if this is in a question thread
        if not isinstance(message.channel, discord.Thread):
            return
        
        # Check if thread is a private thread (question thread)
        if message.channel.type != discord.ChannelType.private_thread:
            return
        
        try:
            # Get question info from database
            db_manager = self.bot.db_manager
            question = await db_manager.get_question_by_thread(message.channel.id)
            
            if not question:
                return  # Not a question thread
            
            # Check for image attachments
            image_attachments = []
            for attachment in message.attachments:
                # Check if attachment is an image
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
                    image_attachments.append(attachment)
            
            if not image_attachments:
                return  # No image attachments
            
            # Create acknowledgment embed
            embed = discord.Embed(
                title="📷 이미지가 업로드되었습니다",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            # Add image info
            image_list = "\n".join([f"• {att.filename} ({self._format_file_size(att.size)})" for att in image_attachments])
            embed.add_field(
                name=f"업로드된 이미지 ({len(image_attachments)}개)",
                value=image_list,
                inline=False
            )
            
            # Check if user is admin or question author
            from config.config import Config
            is_admin = False
            is_author = message.author.id == question['user_id']
            
            guild = message.guild
            if guild:
                admin_role = guild.get_role(Config.ADMIN_ROLE_ID)
                if admin_role and admin_role in message.author.roles:
                    is_admin = True
            
            if is_admin:
                embed.add_field(
                    name="👨‍💼 관리자 이미지",
                    value="관리자가 답변과 함께 이미지를 제공했습니다.",
                    inline=False
                )
                embed.color = discord.Color.blue()
            elif is_author:
                embed.add_field(
                    name="👤 질문자 이미지",
                    value="질문자가 추가 정보로 이미지를 제공했습니다.",
                    inline=False
                )
            
            # Add usage tip
            embed.add_field(
                name="💡 팁",
                value="이미지에 대한 설명을 메시지로 추가해주시면 더 도움이 됩니다!",
                inline=False
            )
            
            # React to the message with checkmark
            await message.add_reaction("✅")
            
            # Send acknowledgment (but not immediately after to avoid spam)
            await message.channel.send(embed=embed, delete_after=30)
            
        except Exception as e:
            self.bot.logger.error(f"Error handling image upload: {e}")
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes/(1024**2):.1f} MB"
        else:
            return f"{size_bytes/(1024**3):.1f} GB"
    
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Handle edited messages with new image attachments"""
        # Check if new attachments were added
        if len(after.attachments) > len(before.attachments):
            await self.on_message(after)

async def setup(bot):
    await bot.add_cog(ImageHandler(bot))