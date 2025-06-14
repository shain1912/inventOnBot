import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import asyncio

class AdminCommands(commands.Cog):
    """Admin commands for managing questions and answers"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin(self, user: discord.Member) -> bool:
        """Check if user is admin"""
        from config.config import Config
        
        # Check if user has the admin role
        admin_role = user.guild.get_role(Config.ADMIN_ROLE_ID)
        has_admin_role = admin_role in user.roles if admin_role else False
        
        # Check if user has administrator permission
        has_admin_perm = user.guild_permissions.administrator
        
        # Check if user is server owner
        is_owner = user.id == user.guild.owner_id
        
        return has_admin_role or has_admin_perm or is_owner
    
    async def send_no_permission_message(self, interaction: discord.Interaction):
        """Send a detailed no permission message"""
        from config.config import Config
        admin_role = interaction.guild.get_role(Config.ADMIN_ROLE_ID)
        embed = discord.Embed(
            title="❌ 권한 부족",
            description="이 명령어는 관리자만 사용할 수 있습니다.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="필요한 권한 (다음 중 하나)",
            value=f"• 관리자 역할: {admin_role.mention if admin_role else f'<@&{Config.ADMIN_ROLE_ID}> (역할 없음)'}\n• 서버 관리자 권한\n• 서버 소유자",
            inline=False
        )
        embed.add_field(
            name="💡 도움말",
            value="권한 확인이 필요하면 `/권한확인` 명령어를 사용해보세요.",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="권한확인", description="현재 사용자의 관리자 권한을 확인합니다")
    async def check_permissions(self, interaction: discord.Interaction):
        """Check user's admin permissions"""
        from config.config import Config
        
        user = interaction.user
        embed = discord.Embed(
            title="권한 확인 결과",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        
        # Check various permission types
        admin_role = user.guild.get_role(Config.ADMIN_ROLE_ID)
        has_admin_role = admin_role in user.roles if admin_role else False
        has_admin_perm = user.guild_permissions.administrator
        is_owner = user.id == user.guild.owner_id
        is_admin_overall = self.is_admin(user)
        
        embed.add_field(
            name="🎭 역할 정보",
            value=f"관리자 역할 ID: `{Config.ADMIN_ROLE_ID}`\n"
                  f"관리자 역할 존재: {'✅' if admin_role else '❌'}\n"
                  f"관리자 역할 보유: {'✅' if has_admin_role else '❌'}",
            inline=False
        )
        
        embed.add_field(
            name="🔐 권한 정보",
            value=f"관리자 권한: {'✅' if has_admin_perm else '❌'}\n"
                  f"서버 소유자: {'✅' if is_owner else '❌'}\n"
                  f"**최종 관리자 판정: {'✅' if is_admin_overall else '❌'}**",
            inline=False
        )
        
        if admin_role:
            embed.add_field(
                name="📋 관리자 역할 멤버",
                value=f"총 {len(admin_role.members)}명: {', '.join([m.display_name for m in admin_role.members[:5]])}{'...' if len(admin_role.members) > 5 else ''}",
                inline=False
            )
        
        user_roles = [role.name for role in user.roles if role.name != '@everyone']
        embed.add_field(
            name="👤 내 역할 목록",
            value=", ".join(user_roles) if user_roles else "역할 없음",
            inline=False
        )
        
        embed.set_footer(text=f"사용자: {user.display_name}", icon_url=user.avatar.url if user.avatar else None)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="질문상태", description="질문의 상태를 변경합니다 (관리자 전용)")
    @app_commands.describe(
        question_id="질문 ID",
        status="새로운 상태 (open, in_progress, solved, closed)"
    )
    async def change_question_status(
        self, 
        interaction: discord.Interaction, 
        question_id: int,
        status: str
    ):
        """Change question status (Admin only)"""
        if not self.is_admin(interaction.user):
            await self.send_no_permission_message(interaction)
            return
        
        valid_statuses = ['open', 'in_progress', 'solved', 'closed']
        if status not in valid_statuses:
            await interaction.response.send_message(
                f"❌ 유효하지 않은 상태입니다. 사용 가능한 상태: {', '.join(valid_statuses)}",
                ephemeral=True
            )
            return
        
        try:
            db_manager = self.bot.db_manager
            question = await db_manager.get_question(question_id)
            
            if not question:
                await interaction.response.send_message(
                    f"❌ 질문 ID {question_id}를 찾을 수 없습니다.",
                    ephemeral=True
                )
                return
            
            # Update status in database
            await db_manager.update_question_status(question_id, status)
            
            # Update thread if exists
            thread = interaction.guild.get_channel_or_thread(question['thread_id'])
            if thread:
                status_emoji = {
                    'open': '🔵',
                    'in_progress': '🟡',
                    'solved': '✅',
                    'closed': '⚫'
                }.get(status, '❓')
                
                embed = discord.Embed(
                    title="질문 상태 변경",
                    description=f"질문 #{question_id}의 상태가 **{status}**로 변경되었습니다.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.add_field(name="변경자", value=interaction.user.mention, inline=True)
                embed.add_field(name="새 상태", value=f"{status_emoji} {status}", inline=True)
                
                await thread.send(embed=embed)
            
            await interaction.response.send_message(
                f"✅ 질문 #{question_id}의 상태를 **{status}**로 변경했습니다.",
                ephemeral=True
            )
            
        except Exception as e:
            self.bot.logger.error(f"Error changing question status: {e}")
            await interaction.response.send_message(
                "❌ 상태 변경 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="답변", description="질문에 답변을 등록합니다 (관리자 전용)")
    @app_commands.describe(
        question_id="질문 ID",
        answer="답변 내용",
        is_solution="이 답변이 최종 해결책인지 여부"
    )
    async def add_answer(
        self,
        interaction: discord.Interaction,
        question_id: int,
        answer: str,
        is_solution: bool = False
    ):
        """Add an answer to a question (Admin only)"""
        if not self.is_admin(interaction.user):
            await self.send_no_permission_message(interaction)
            return
        
        try:
            # 즉시 응답하여 3초 제한 해결
            await interaction.response.defer(ephemeral=True)
            
            db_manager = self.bot.db_manager
            question = await db_manager.get_question(question_id)
            
            if not question:
                await interaction.followup.send(
                    f"❌ 질문 ID {question_id}를 찾을 수 없습니다.",
                    ephemeral=True
                )
                return
            
            # Add answer to database
            answer_id = await db_manager.add_answer(
                question_id=question_id,
                admin_id=interaction.user.id,
                answer_text=answer,
                is_solution=is_solution
            )
            
            # Update daily statistics
            await db_manager.update_daily_stats('answers_given')
            if is_solution:
                await db_manager.update_daily_stats('questions_solved')
                
                # Calculate and record response time
                question = await db_manager.get_question(question_id)
                if question and question['created_at']:
                    from datetime import datetime
                    try:
                        created_time = datetime.fromisoformat(question['created_at'].replace('Z', '+00:00'))
                        response_time = datetime.now() - created_time
                        minutes = int(response_time.total_seconds() / 60)
                        await db_manager.record_response_time(question_id, minutes)
                    except Exception:
                        pass  # 시간 계산 실패시 무시
            
            # Post answer in thread
            thread = interaction.guild.get_channel_or_thread(question['thread_id'])
            if thread:
                embed = discord.Embed(
                    title="관리자 답변" if not is_solution else "✅ 해결책",
                    description=answer,
                    color=discord.Color.green() if is_solution else discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(
                    text=f"답변자: {interaction.user.display_name}",
                    icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                )
                
                if is_solution:
                    embed.add_field(
                        name="🎉 해결됨",
                        value="이 답변으로 문제가 해결되었습니다!",
                        inline=False
                    )
                    # Automatically change status to solved
                    await db_manager.update_question_status(question_id, 'solved')
                
                answer_message = await thread.send(embed=embed)
                
                # Add image upload option for admin
                image_option_embed = discord.Embed(
                    title="📷 이미지 첨부 옵션",
                    description="설명에 도움이 될 이미지가 있다면 이 메시지에 답장하여 업로드해주세요.",
                    color=discord.Color.blue()
                )
                await thread.send(embed=image_option_embed)
                
                # Notify the question author
                question_author = interaction.guild.get_member(question['user_id'])
                if question_author:
                    try:
                        notification_embed = discord.Embed(
                            title="새로운 답변이 등록되었습니다!",
                            description=f"질문 #{question_id}에 새로운 답변이 등록되었습니다.",
                            color=discord.Color.green(),
                            timestamp=discord.utils.utcnow()
                        )
                        notification_embed.add_field(
                            name="질문 스레드",
                            value=thread.mention,
                            inline=False
                        )
                        
                        await question_author.send(embed=notification_embed)
                    except discord.HTTPException:
                        pass  # User might have DMs disabled
            
            await interaction.followup.send(
                f"✅ 질문 #{question_id}에 답변을 등록했습니다. (답변 ID: {answer_id})",
                ephemeral=True
            )
            
        except Exception as e:
            self.bot.logger.error(f"Error adding answer: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ 답변 등록 중 오류가 발생했습니다.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ 답변 등록 중 오류가 발생했습니다.",
                        ephemeral=True
                    )
            except:
                pass
    
    @app_commands.command(name="질문목록", description="모든 질문 목록을 확인합니다 (관리자 전용)")
    @app_commands.describe(
        status="필터링할 상태 (선택사항)",
        limit="표시할 질문 수 (기본: 20, 최대: 50)"
    )
    async def list_questions(
        self,
        interaction: discord.Interaction,
        status: Optional[str] = None,
        limit: int = 20
    ):
        """List all questions (Admin only)"""
        if not self.is_admin(interaction.user):
            await self.send_no_permission_message(interaction)
            return
        
        if limit > 50:
            limit = 50
        
        try:
            # This would require adding a method to database manager
            # For now, we'll show a placeholder response
            await interaction.response.send_message(
                f"📋 질문 목록 기능은 구현 중입니다.\n"
                f"필터: {status or '전체'}\n"
                f"제한: {limit}개",
                ephemeral=True
            )
            
        except Exception as e:
            self.bot.logger.error(f"Error listing questions: {e}")
            await interaction.response.send_message(
                "❌ 질문 목록을 가져오는 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="질문검색", description="질문을 검색합니다 (관리자 전용)")
    @app_commands.describe(
        keyword="검색할 키워드",
        search_type="검색 범위 (title, error, code, all)"
    )
    async def search_questions(
        self,
        interaction: discord.Interaction,
        keyword: str,
        search_type: str = "all"
    ):
        """Search questions (Admin only)"""
        if not self.is_admin(interaction.user):
            await self.send_no_permission_message(interaction)
            return
        
        valid_search_types = ['title', 'error', 'code', 'all']
        if search_type not in valid_search_types:
            await interaction.response.send_message(
                f"❌ 유효하지 않은 검색 타입입니다. 사용 가능: {', '.join(valid_search_types)}",
                ephemeral=True
            )
            return
        
        try:
            # Placeholder for search functionality
            await interaction.response.send_message(
                f"🔍 질문 검색 기능은 구현 중입니다.\n"
                f"키워드: '{keyword}'\n"
                f"검색 범위: {search_type}",
                ephemeral=True
            )
            
        except Exception as e:
            self.bot.logger.error(f"Error searching questions: {e}")
            await interaction.response.send_message(
                "❌ 검색 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="이미지답변", description="이미지와 함께 답변을 등록합니다 (관리자 전용)")
    @app_commands.describe(
        question_id="질문 ID",
        answer="답변 내용",
        is_solution="이 답변이 최종 해결책인지 여부"
    )
    async def add_answer_with_image(
        self,
        interaction: discord.Interaction,
        question_id: int,
        answer: str,
        is_solution: bool = False
    ):
        """Add an answer with image option (Admin only)"""
        if not self.is_admin(interaction.user):
            await self.send_no_permission_message(interaction)
            return
        
        try:
            # 즉시 응답하여 3초 제한 해결
            await interaction.response.defer(ephemeral=True)
            
            db_manager = self.bot.db_manager
            question = await db_manager.get_question(question_id)
            
            if not question:
                await interaction.followup.send(
                    f"❌ 질문 ID {question_id}를 찾을 수 없습니다.",
                    ephemeral=True
                )
                return
            
            # Add answer to database
            answer_id = await db_manager.add_answer(
                question_id=question_id,
                admin_id=interaction.user.id,
                answer_text=answer,
                is_solution=is_solution
            )
            
            # Post answer in thread
            thread = interaction.guild.get_channel_or_thread(question['thread_id'])
            if thread:
                embed = discord.Embed(
                    title="관리자 답변" if not is_solution else "✅ 해결책",
                    description=answer,
                    color=discord.Color.green() if is_solution else discord.Color.blue(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(
                    text=f"답변자: {interaction.user.display_name}",
                    icon_url=interaction.user.avatar.url if interaction.user.avatar else None
                )
                
                if is_solution:
                    embed.add_field(
                        name="🎉 해결됨",
                        value="이 답변으로 문제가 해결되었습니다!",
                        inline=False
                    )
                    # Automatically change status to solved
                    await db_manager.update_question_status(question_id, 'solved')
                
                await thread.send(embed=embed)
                
                # Send image upload instructions
                image_instructions = discord.Embed(
                    title="📎 이미지 업로드 안내",
                    description="답변과 함께 제공할 이미지를 지금 업로드해주세요.",
                    color=discord.Color.orange()
                )
                image_instructions.add_field(
                    name="업로드 방법",
                    value="1. 이 스레드에 직접 이미지 파일을 드래그&드롭하거나\n2. 파일 첨부 버튼을 사용하여 업로드\n3. 이미지 설명을 함께 작성해주세요",
                    inline=False
                )
                await thread.send(embed=image_instructions)
            
            await interaction.followup.send(
                f"✅ 질문 #{question_id}에 답변을 등록했습니다. 이제 스레드에 이미지를 업로드해주세요. (답변 ID: {answer_id})",
                ephemeral=True
            )
            
        except Exception as e:
            self.bot.logger.error(f"Error adding answer with image: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ 답변 등록 중 오류가 발생했습니다.",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        "❌ 답변 등록 중 오류가 발생했습니다.",
                        ephemeral=True
                    )
            except:
                pass
    
    @app_commands.command(name="통계", description="질문 및 답변 통계를 확인합니다 (관리자 전용)")
    async def show_stats(self, interaction: discord.Interaction):
        """Show question and answer statistics (Admin only)"""
        if not self.is_admin(interaction.user):
            await self.send_no_permission_message(interaction)
            return
        
        try:
            # Placeholder for statistics
            embed = discord.Embed(
                title="📊 InventOnBot 통계",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="📝 총 질문 수", value="구현 중", inline=True)
            embed.add_field(name="✅ 해결된 질문", value="구현 중", inline=True)
            embed.add_field(name="🟡 진행 중인 질문", value="구현 중", inline=True)
            embed.add_field(name="👥 활성 사용자", value="구현 중", inline=True)
            embed.add_field(name="💬 총 답변 수", value="구현 중", inline=True)
            embed.add_field(name="⏱️ 평균 응답 시간", value="구현 중", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error showing stats: {e}")
            await interaction.response.send_message(
                "❌ 통계를 가져오는 중 오류가 발생했습니다.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AdminCommands(bot))