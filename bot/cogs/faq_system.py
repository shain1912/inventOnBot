import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List
import re

class FAQSystem(commands.Cog):
    """FAQ (자주 묻는 질문) 관리 시스템"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin(self, user: discord.Member) -> bool:
        """Check if user is admin"""
        from config.config import Config
        admin_role = user.guild.get_role(Config.ADMIN_ROLE_ID)
        return admin_role in user.roles if admin_role else False
    
    @app_commands.command(name="faq추가", description="FAQ를 추가합니다 (관리자 전용)")
    @app_commands.describe(
        question="질문 내용",
        answer="답변 내용", 
        keywords="검색 키워드 (쉼표로 구분)"
    )
    async def add_faq(
        self,
        interaction: discord.Interaction,
        question: str,
        answer: str,
        keywords: Optional[str] = None
    ):
        """Add a new FAQ (Admin only)"""
        if not self.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
                ephemeral=True
            )
            return
        
        try:
            db_manager = self.bot.db_manager
            
            # Add FAQ to database
            await db_manager.add_faq(
                question=question,
                answer=answer,
                keywords=keywords,
                created_by=interaction.user.id
            )
            
            embed = discord.Embed(
                title="✅ FAQ가 추가되었습니다",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="질문", value=question, inline=False)
            embed.add_field(name="답변", value=answer[:500] + "..." if len(answer) > 500 else answer, inline=False)
            if keywords:
                embed.add_field(name="키워드", value=keywords, inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error adding FAQ: {e}")
            await interaction.response.send_message(
                "❌ FAQ 추가 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="faq검색", description="FAQ를 검색합니다")
    @app_commands.describe(keyword="검색할 키워드")
    async def search_faq(self, interaction: discord.Interaction, keyword: str):
        """Search FAQ by keyword"""
        try:
            db_manager = self.bot.db_manager
            faqs = await db_manager.search_faq(keyword)
            
            if not faqs:
                embed = discord.Embed(
                    title="🔍 검색 결과",
                    description=f"'{keyword}'와 관련된 FAQ를 찾을 수 없습니다.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Create paginated embed for multiple results
            embed = discord.Embed(
                title=f"🔍 FAQ 검색 결과: '{keyword}'",
                description=f"총 {len(faqs)}개의 FAQ를 찾았습니다.",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            # Show first 3 results
            for i, faq in enumerate(faqs[:3]):
                embed.add_field(
                    name=f"❓ {faq['question']}",
                    value=f"{faq['answer'][:200]}{'...' if len(faq['answer']) > 200 else ''}",
                    inline=False
                )
            
            if len(faqs) > 3:
                embed.set_footer(text=f"더 많은 결과가 있습니다. '/faq목록'으로 전체 목록을 확인하세요.")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error searching FAQ: {e}")
            await interaction.response.send_message(
                "❌ FAQ 검색 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="faq목록", description="모든 FAQ 목록을 확인합니다")
    async def list_faq(self, interaction: discord.Interaction):
        """List all FAQs"""
        try:
            db_manager = self.bot.db_manager
            faqs = await db_manager.get_all_faq()
            
            if not faqs:
                embed = discord.Embed(
                    title="📋 FAQ 목록",
                    description="등록된 FAQ가 없습니다.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📋 FAQ 목록",
                description=f"총 {len(faqs)}개의 FAQ가 등록되어 있습니다.",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            # Show first 10 FAQs
            for i, faq in enumerate(faqs[:10]):
                embed.add_field(
                    name=f"{i+1}. {faq['question']}",
                    value=f"{faq['answer'][:150]}{'...' if len(faq['answer']) > 150 else ''}",
                    inline=False
                )
            
            if len(faqs) > 10:
                embed.set_footer(text=f"총 {len(faqs)}개 중 10개만 표시됩니다.")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error listing FAQ: {e}")
            await interaction.response.send_message(
                "❌ FAQ 목록 조회 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="faq삭제", description="FAQ를 삭제합니다 (관리자 전용)")
    @app_commands.describe(faq_id="삭제할 FAQ ID")
    async def delete_faq(self, interaction: discord.Interaction, faq_id: int):
        """Delete FAQ (Admin only)"""
        if not self.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
                ephemeral=True
            )
            return
        
        try:
            db_manager = self.bot.db_manager
            
            # Get FAQ details before deletion
            faq = await db_manager.get_faq_by_id(faq_id)
            if not faq:
                await interaction.response.send_message(
                    f"❌ FAQ ID {faq_id}를 찾을 수 없습니다.",
                    ephemeral=True
                )
                return
            
            # Delete FAQ
            await db_manager.delete_faq(faq_id)
            
            embed = discord.Embed(
                title="🗑️ FAQ가 삭제되었습니다",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="삭제된 질문", value=faq['question'], inline=False)
            embed.add_field(name="FAQ ID", value=str(faq_id), inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error deleting FAQ: {e}")
            await interaction.response.send_message(
                "❌ FAQ 삭제 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="faq수정", description="FAQ를 수정합니다 (관리자 전용)")
    @app_commands.describe(
        faq_id="수정할 FAQ ID",
        question="새로운 질문 (선택)",
        answer="새로운 답변 (선택)",
        keywords="새로운 키워드 (선택)"
    )
    async def update_faq(
        self,
        interaction: discord.Interaction,
        faq_id: int,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        keywords: Optional[str] = None
    ):
        """Update FAQ (Admin only)"""
        if not self.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
                ephemeral=True
            )
            return
        
        if not any([question, answer, keywords]):
            await interaction.response.send_message(
                "❌ 수정할 내용(질문, 답변, 키워드 중 하나)을 입력해주세요.",
                ephemeral=True
            )
            return
        
        try:
            db_manager = self.bot.db_manager
            
            # Check if FAQ exists
            existing_faq = await db_manager.get_faq_by_id(faq_id)
            if not existing_faq:
                await interaction.response.send_message(
                    f"❌ FAQ ID {faq_id}를 찾을 수 없습니다.",
                    ephemeral=True
                )
                return
            
            # Update FAQ
            await db_manager.update_faq(
                faq_id=faq_id,
                question=question,
                answer=answer,
                keywords=keywords
            )
            
            embed = discord.Embed(
                title="✏️ FAQ가 수정되었습니다",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="FAQ ID", value=str(faq_id), inline=True)
            
            if question:
                embed.add_field(name="🔄 질문 (수정됨)", value=question, inline=False)
            else:
                embed.add_field(name="질문 (기존)", value=existing_faq['question'], inline=False)
            
            if answer:
                embed.add_field(name="🔄 답변 (수정됨)", value=answer[:500] + "..." if len(answer) > 500 else answer, inline=False)
            else:
                embed.add_field(name="답변 (기존)", value=existing_faq['answer'][:500] + "..." if len(existing_faq['answer']) > 500 else existing_faq['answer'], inline=False)
            
            if keywords:
                embed.add_field(name="🔄 키워드 (수정됨)", value=keywords, inline=False)
            elif existing_faq['keywords']:
                embed.add_field(name="키워드 (기존)", value=existing_faq['keywords'], inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error updating FAQ: {e}")
            await interaction.response.send_message(
                "❌ FAQ 수정 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Auto-suggest FAQ when someone asks a question in channel"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Only respond in non-thread channels
        if isinstance(message.channel, discord.Thread):
            return
        
        # Check if message contains question indicators
        question_indicators = ['?', '어떻게', '왜', '뭐', '언제', '어디서', '도움', '문제', '오류', '에러']
        message_lower = message.content.lower()
        
        if not any(indicator in message_lower for indicator in question_indicators):
            return
        
        try:
            db_manager = self.bot.db_manager
            
            # Extract keywords from message
            words = re.findall(r'\b\w+\b', message_lower)
            potential_keywords = [word for word in words if len(word) > 2]
            
            if not potential_keywords:
                return
            
            # Search for relevant FAQs
            relevant_faqs = []
            for keyword in potential_keywords[:3]:  # Check first 3 keywords
                faqs = await db_manager.search_faq(keyword)
                relevant_faqs.extend(faqs)
            
            # Remove duplicates
            seen_ids = set()
            unique_faqs = []
            for faq in relevant_faqs:
                if faq['id'] not in seen_ids:
                    unique_faqs.append(faq)
                    seen_ids.add(faq['id'])
            
            if unique_faqs:
                embed = discord.Embed(
                    title="💡 관련 FAQ 추천",
                    description="질문과 관련된 FAQ를 찾았습니다!",
                    color=discord.Color.gold()
                )
                
                for faq in unique_faqs[:2]:  # Show top 2 recommendations
                    embed.add_field(
                        name=f"❓ {faq['question']}",
                        value=f"{faq['answer'][:200]}{'...' if len(faq['answer']) > 200 else ''}",
                        inline=False
                    )
                
                embed.set_footer(text="더 많은 FAQ는 '/faq검색 키워드' 또는 '/faq목록'을 사용하세요.")
                
                # Send suggestion with auto-delete
                await message.reply(embed=embed, delete_after=60)
                
        except Exception as e:
            self.bot.logger.error(f"Error in FAQ auto-suggestion: {e}")

async def setup(bot):
    await bot.add_cog(FAQSystem(bot))