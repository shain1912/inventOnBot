import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import re

class QuestionModal(discord.ui.Modal, title='프로그래밍 질문하기'):
    """Modal form for submitting programming questions"""
    
    def __init__(self):
        super().__init__()
        
    # Required fields
    os = discord.ui.TextInput(
        label='운영체제 (필수)',
        placeholder='예: Windows 11, macOS Ventura, Ubuntu 22.04',
        required=True,
        max_length=100
    )
    
    programming_language = discord.ui.TextInput(
        label='프로그래밍 언어 (필수)',
        placeholder='예: Python 3.9, JavaScript, Java 17, C++',
        required=True,
        max_length=100
    )
    
    error_message = discord.ui.TextInput(
        label='에러 메시지 (필수)',
        placeholder='발생한 오류 메시지를 정확히 입력해주세요',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    purpose = discord.ui.TextInput(
        label='원래 하려던 목적 (필수)',
        placeholder='무엇을 구현하려고 했는지, 어떤 기능을 만들려고 했는지 설명해주세요',
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    code_snippet = discord.ui.TextInput(
        label='코드 (선택)',
        placeholder='문제가 발생한 코드를 입력해주세요',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=2000
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission"""
        try:
            # Get the bot and database manager
            bot = interaction.client
            db_manager = bot.db_manager
            
            # Ensure user exists in database
            user = interaction.user
            await db_manager.add_user(
                user_id=user.id,
                username=user.name,
                display_name=user.display_name
            )
            
            # Create a title for the question thread
            title = f"[{self.programming_language.value}] {self.purpose.value[:50]}..."
            if len(self.purpose.value) <= 50:
                title = f"[{self.programming_language.value}] {self.purpose.value}"
            
            # Create private thread
            channel = interaction.channel
            
            # Check if we're already in a thread, if so get the parent channel
            if isinstance(channel, discord.Thread):
                parent_channel = channel.parent
            else:
                parent_channel = channel
            
            # Ensure parent_channel is a text channel that supports threads
            if not hasattr(parent_channel, 'create_thread'):
                await interaction.response.send_message(
                    "❌ 이 채널에서는 스레드를 생성할 수 없습니다. 텍스트 채널에서 다시 시도해주세요.",
                    ephemeral=True
                )
                return
            
            thread = await parent_channel.create_thread(
                name=title,
                type=discord.ChannelType.private_thread,
                reason=f"질문 스레드 - {user.display_name}"
            )
            
            # Add the user to the thread
            await thread.add_user(user)
            
            # Add admin role members to the thread
            from config.config import Config
            guild = interaction.guild
            admin_role = guild.get_role(Config.ADMIN_ROLE_ID)
            
            if admin_role:
                for member in admin_role.members:
                    try:
                        await thread.add_user(member)
                    except discord.HTTPException:
                        pass  # Member might already be in thread or unavailable
            
            # Save question to database
            question_id = await db_manager.create_question(
                user_id=user.id,
                thread_id=thread.id,
                title=title,
                os=self.os.value,
                programming_language=self.programming_language.value,
                error_message=self.error_message.value,
                purpose=self.purpose.value,
                code_snippet=self.code_snippet.value if self.code_snippet.value else None
            )
            
            # Update daily statistics
            await db_manager.update_daily_stats('questions_created')
            
            # Create detailed question embed
            embed = discord.Embed(
                title="새로운 프로그래밍 질문",
                description=f"질문 ID: {question_id}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="🖥️ 운영체제", value=self.os.value, inline=True)
            embed.add_field(name="💻 프로그래밍 언어", value=self.programming_language.value, inline=True)
            embed.add_field(name="🎯 목적", value=self.purpose.value, inline=False)
            embed.add_field(name="❌ 에러 메시지", value=f"```\n{self.error_message.value}\n```", inline=False)
            
            if self.code_snippet.value:
                # Try to detect language for syntax highlighting
                lang = self._detect_language(self.programming_language.value)
                embed.add_field(
                    name="📝 코드",
                    value=f"```{lang}\n{self.code_snippet.value[:1000]}\n```",
                    inline=False
                )
                if len(self.code_snippet.value) > 1000:
                    embed.add_field(
                        name="📝 코드 (계속)",
                        value=f"```{lang}\n{self.code_snippet.value[1000:]}\n```",
                        inline=False
                    )
            
            embed.set_footer(text=f"질문자: {user.display_name}", icon_url=user.avatar.url if user.avatar else None)
            
            # Send question to the thread
            message = await thread.send(embed=embed)
            
            # Add image upload reminder
            image_reminder = discord.Embed(
                title="📷 이미지 첨부 안내",
                description="스크린샷이나 에러 화면 이미지가 있다면 이 메시지에 답장하여 직접 업로드해주세요.",
                color=discord.Color.orange()
            )
            image_reminder.add_field(
                name="이미지 첨부 방법",
                value="1. 이 메시지에 답장하기\n2. 파일 선택 또는 드래그&드롭\n3. 이미지에 대한 설명 메시지 추가",
                inline=False
            )
            await thread.send(embed=image_reminder)
            
            # Create follow-up modal view for optional fields
            follow_up_view = OptionalFieldsView(question_id, db_manager)
            
            # Respond to user
            await interaction.response.send_message(
                f"✅ 질문이 성공적으로 등록되었습니다!\n"
                f"스레드: {thread.mention}\n"
                f"질문 ID: `{question_id}`\n\n"
                f"📷 **이미지 첨부**: 스크린샷이나 에러 화면이 있다면 스레드에 직접 업로드해주세요!\n"
                f"📝 **추가 정보**: 아래 버튼을 눌러 로그, 시도한 조치 등을 추가할 수 있습니다.",
                view=follow_up_view,
                ephemeral=True
            )
            
        except Exception as e:
            bot.logger.error(f"Error submitting question: {e}")
            await interaction.response.send_message(
                "❌ 질문 등록 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                ephemeral=True
            )
    
    def _detect_language(self, prog_lang: str) -> str:
        """Detect language for code syntax highlighting"""
        lang_lower = prog_lang.lower()
        
        if 'python' in lang_lower:
            return 'python'
        elif 'javascript' in lang_lower or 'js' in lang_lower:
            return 'javascript'
        elif 'java' in lang_lower and 'script' not in lang_lower:
            return 'java'
        elif 'c++' in lang_lower or 'cpp' in lang_lower:
            return 'cpp'
        elif 'c#' in lang_lower or 'csharp' in lang_lower:
            return 'csharp'
        elif 'html' in lang_lower:
            return 'html'
        elif 'css' in lang_lower:
            return 'css'
        elif 'sql' in lang_lower:
            return 'sql'
        else:
            return ''

class OptionalFieldsView(discord.ui.View):
    """View for adding optional fields to a question"""
    
    def __init__(self, question_id: int, db_manager):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.question_id = question_id
        self.db_manager = db_manager
    
    @discord.ui.button(label='추가 정보 입력', style=discord.ButtonStyle.secondary, emoji='📝')
    async def add_optional_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show modal for optional information"""
        modal = OptionalInfoModal(self.question_id, self.db_manager)
        await interaction.response.send_modal(modal)

class OptionalInfoModal(discord.ui.Modal, title='추가 정보 입력'):
    """Modal for optional question information"""
    
    def __init__(self, question_id: int, db_manager):
        super().__init__()
        self.question_id = question_id
        self.db_manager = db_manager
    
    log_files = discord.ui.TextInput(
        label='로그 파일 내용 (선택)',
        placeholder='관련 로그 파일의 내용을 붙여넣어주세요',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=2000
    )
    
    attempted_solutions = discord.ui.TextInput(
        label='이미 시도해본 조치들 (선택)',
        placeholder='문제 해결을 위해 시도해본 방법들을 적어주세요',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=1000
    )
    
    screenshot_info = discord.ui.TextInput(
        label='스크린샷 설명 (선택)',
        placeholder='스크린샷이 있다면 스레드에 첨부하고 여기에 설명을 적어주세요',
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=500
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle optional info submission"""
        try:
            # Get question and post additional info to thread
            question = await self.db_manager.get_question(self.question_id)
            if question:
                channel = interaction.guild.get_channel_or_thread(question['thread_id'])
                if channel:
                    embed = discord.Embed(
                        title="추가 정보",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    
                    if self.log_files.value:
                        embed.add_field(
                            name="📄 로그 파일",
                            value=f"```\n{self.log_files.value}\n```",
                            inline=False
                        )
                    
                    if self.attempted_solutions.value:
                        embed.add_field(
                            name="🔧 시도한 조치들",
                            value=self.attempted_solutions.value,
                            inline=False
                        )
                    
                    if self.screenshot_info.value:
                        embed.add_field(
                            name="📸 스크린샷 설명",
                            value=self.screenshot_info.value,
                            inline=False
                        )
                    
                    await channel.send(embed=embed)
            
            await interaction.response.send_message(
                "✅ 추가 정보가 질문 스레드에 추가되었습니다!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                "❌ 추가 정보 등록 중 오류가 발생했습니다.",
                ephemeral=True
            )

class QuestionHandler(commands.Cog):
    """Cog for handling question submissions"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="질문", description="프로그래밍 관련 질문을 등록합니다")
    async def submit_question(self, interaction: discord.Interaction):
        """Submit a programming question"""
        modal = QuestionModal()
        await interaction.response.send_modal(modal)
    
    @app_commands.command(name="내질문", description="내가 등록한 질문들을 확인합니다")
    async def my_questions(self, interaction: discord.Interaction):
        """View user's questions"""
        try:
            db_manager = self.bot.db_manager
            questions = await db_manager.get_user_questions(interaction.user.id)
            
            if not questions:
                await interaction.response.send_message(
                    "등록된 질문이 없습니다.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"{interaction.user.display_name}님의 질문 목록",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            for i, question in enumerate(questions[:10]):  # Show only first 10
                status_emoji = {
                    'open': '🔵',
                    'in_progress': '🟡',
                    'solved': '🟢',
                    'closed': '⚫'
                }.get(question['status'], '❓')
                
                thread_mention = f"<#{question['thread_id']}>"
                embed.add_field(
                    name=f"{status_emoji} 질문 #{question['id']}",
                    value=f"**언어:** {question['programming_language']}\n**상태:** {question['status']}\n**스레드:** {thread_mention}\n**등록일:** {question['created_at'][:10]}",
                    inline=True
                )
            
            if len(questions) > 10:
                embed.set_footer(text=f"총 {len(questions)}개 질문 중 최근 10개만 표시")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error fetching user questions: {e}")
            await interaction.response.send_message(
                "질문 목록을 가져오는 중 오류가 발생했습니다.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(QuestionHandler(bot))