import discord
from discord.ext import commands
from typing import Optional

class WelcomeSystem(commands.Cog):
    """환영 메시지 및 튜토리얼 시스템"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def create_tutorial_embed(self):
        """튜토리얼 임베드 생성"""
        embed = discord.Embed(
            title="📢 InventOnBot 사용법 안내",
            description="안녕하세요! 프로그래밍 질의응답 봇 **InventOnBot**에 오신 것을 환영합니다! 🎉",
            color=discord.Color.blue()
        )
        
        # Discord 슬래시 명령어 설명
        embed.add_field(
            name="🤔 Discord 슬래시 명령어란?",
            value=(
                "Discord에서 `/`로 시작하는 명령어를 **슬래시 명령어**라고 합니다.\n\n"
                "**📝 사용법:**\n"
                "1. 채팅창에 `/` 입력\n"
                "2. 자동으로 명령어 목록 표시\n"
                "3. 원하는 명령어 클릭 또는 타이핑\n"
                "4. 필요한 정보 입력 후 Enter\n\n"
                "**예시:** `/질문` 입력 → 질문 등록 모달창 열림"
            ),
            inline=False
        )
        
        # 스레드 설명
        embed.add_field(
            name="🧵 스레드(Thread)란?",
            value=(
                "메인 채널에서 분리된 별도의 대화 공간입니다.\n\n"
                "**🔒 InventOnBot의 프라이빗 스레드:**\n"
                "• 개별 질문마다 전용 스레드 생성\n"
                "• 질문자와 관리자만 접근 가능\n"
                "• 다른 사람들은 여러분의 질문을 볼 수 없음\n"
                "• 개인정보 보호 및 집중적인 지원 제공\n\n"
                "✅ 개인 맞춤형 지원\n"
                "✅ 체계적인 문제 해결 과정 관리"
            ),
            inline=False
        )
        
        return embed
    
    def create_question_tutorial_embed(self):
        """질문 튜토리얼 임베드 생성"""
        embed = discord.Embed(
            title="🚀 `/질문` 명령어 튜토리얼",
            description="효과적인 질문 등록 방법을 안내해드립니다!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="**1단계: 질문 등록하기**",
            value="`/질문` 명령어 입력 → 질문 등록 모달창 열림",
            inline=False
        )
        
        embed.add_field(
            name="**2단계: 필수 정보 입력 📋**",
            value=(
                "🖥️ **운영체제**: `Windows 11`, `macOS Ventura`, `Ubuntu 22.04` 등\n"
                "💻 **프로그래밍 언어**: `Python 3.9`, `JavaScript`, `Java 17` 등\n"
                "❌ **에러 메시지**: 발생한 오류 메시지를 정확히 복사&붙여넣기\n"
                "🎯 **원래 하려던 목적**: 구현하려던 기능이나 목표 설명"
            ),
            inline=False
        )
        
        embed.add_field(
            name="**3단계: 이미지 첨부 (선택사항) 📷**",
            value=(
                "스크린샷이나 에러 화면이 있다면:\n"
                "1. 생성된 스레드로 이동\n"
                "2. 이미지를 **드래그&드롭** 또는 **파일 첨부**\n"
                "3. 이미지 설명을 함께 작성\n"
                "4. 봇이 자동으로 ✅ 체크 표시 추가"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 효과적인 질문하는 방법",
            value=(
                "• **구체적인 에러 메시지** 포함\n"
                "• **최소한의 재현 가능한 코드** 제공\n"
                "• **예상 결과 vs 실제 결과** 명시\n"
                "• **이미 시도한 해결 방법** 공유\n"
                "• **관련 스크린샷** 첨부"
            ),
            inline=False
        )
        
        return embed
    
    def create_commands_embed(self):
        """명령어 목록 임베드 생성"""
        embed = discord.Embed(
            title="🔍 사용 가능한 명령어",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="👤 사용자 명령어",
            value=(
                "`/질문` - 새로운 프로그래밍 질문 등록\n"
                "`/내질문` - 내가 등록한 질문 목록 확인\n"
                "`/faq검색 키워드` - 자주 묻는 질문 검색\n"
                "`/faq목록` - 전체 FAQ 목록 보기"
            ),
            inline=False
        )
        
        embed.add_field(
            name="❓ 자주 묻는 질문",
            value=(
                "**Q: 다른 사람이 내 질문을 볼 수 있나요?**\n"
                "A: 아니요! 프라이빗 스레드로 질문자와 관리자만 볼 수 있습니다.\n\n"
                "**Q: 이미지는 어떻게 올리나요?**\n"
                "A: 스레드에서 드래그&드롭하거나 파일 첨부 버튼을 사용하세요.\n\n"
                "**Q: 답변은 언제 받을 수 있나요?**\n"
                "A: 관리자 확인 후 답변드립니다. 자세한 정보 제공시 더 빠른 답변 가능!"
            ),
            inline=False
        )
        
        embed.set_footer(text="🤖 InventOnBot과 함께 프로그래밍 문제를 해결해보세요! 💪")
        
        return embed
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """새 멤버 참여 시 환영 메시지 및 튜토리얼 전송"""
        if member.bot:
            return  # 봇은 무시
        
        try:
            # 개인 DM으로 환영 메시지 전송
            welcome_embed = discord.Embed(
                title="🎉 InventOnBot 서버에 오신 것을 환영합니다!",
                description=f"안녕하세요 {member.mention}님! 프로그래밍 질의응답 전용 서버입니다.",
                color=discord.Color.gold()
            )
            
            welcome_embed.add_field(
                name="🚀 시작하기",
                value=(
                    f"서버에서 `/질문` 명령어를 사용하여 프로그래밍 관련 질문을 등록할 수 있습니다.\n"
                    f"질문을 등록하면 개인 전용 스레드가 생성되어 관리자와 1:1로 소통할 수 있습니다!"
                ),
                inline=False
            )
            
            welcome_embed.add_field(
                name="📖 사용법 안내",
                value="서버의 📢안내 채널에서 자세한 사용법을 확인하실 수 있습니다.",
                inline=False
            )
            
            welcome_embed.set_footer(text="질문이 있으시면 언제든지 /질문 명령어를 사용해주세요!")
            
            await member.send(embed=welcome_embed)
            
            # 서버 로그 채널에 입장 알림 (선택사항)
            guild = member.guild
            if guild:
                # 로그 채널 찾기 (채널명으로 찾기, 없으면 무시)
                log_channel = discord.utils.get(guild.channels, name="입장로그")
                if log_channel:
                    log_embed = discord.Embed(
                        title="새 멤버 입장",
                        description=f"{member.mention}님이 서버에 참여했습니다.",
                        color=discord.Color.green(),
                        timestamp=discord.utils.utcnow()
                    )
                    log_embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                    await log_channel.send(embed=log_embed)
            
        except discord.HTTPException:
            # DM 전송 실패 시 (DM 차단 등) 무시
            pass
    
    @commands.command(name="튜토리얼")
    @commands.has_permissions(manage_messages=True)
    async def send_tutorial(self, ctx, channel: Optional[discord.TextChannel] = None):
        """관리자가 튜토리얼 메시지를 특정 채널에 전송"""
        if channel is None:
            channel = ctx.channel
        
        # 봇이 해당 채널에 메시지를 보낼 권한이 있는지 확인
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send("❌ 해당 채널에 메시지를 보낼 권한이 없습니다.", delete_after=10)
            return
        
        try:
            # 1. 기본 사용법
            tutorial_embed = self.create_tutorial_embed()
            await channel.send(embed=tutorial_embed)
            
            # 2. 질문 튜토리얼
            question_embed = self.create_question_tutorial_embed()
            await channel.send(embed=question_embed)
            
            # 3. 명령어 및 FAQ
            commands_embed = self.create_commands_embed()
            await channel.send(embed=commands_embed)
            
            # 확인 메시지
            confirm_msg = await ctx.send("✅ 튜토리얼이 성공적으로 게시되었습니다!")
            await confirm_msg.delete(delay=5)
            
        except discord.Forbidden:
            await ctx.send("❌ 메시지 전송 권한이 없습니다. 봇 권한을 확인해주세요.", delete_after=10)
        except Exception as e:
            self.bot.logger.error(f"Tutorial send error: {e}")
            await ctx.send("❌ 튜토리얼 전송 중 오류가 발생했습니다.", delete_after=10)
    
    @commands.command(name="고정튜토리얼")
    @commands.has_permissions(manage_messages=True)
    async def pin_tutorial(self, ctx, channel: Optional[discord.TextChannel] = None):
        """관리자가 튜토리얼 메시지를 고정"""
        if channel is None:
            channel = ctx.channel
        
        # 모든 튜토리얼 임베드를 하나로 합치기
        main_embed = discord.Embed(
            title="📢 InventOnBot 완전 사용 가이드",
            description="프로그래밍 질의응답 봇 사용법을 안내해드립니다! 🎉",
            color=discord.Color.blurple()
        )
        
        # 슬래시 명령어 설명
        main_embed.add_field(
            name="🤔 슬래시 명령어 사용법",
            value=(
                "1. 채팅창에 `/` 입력\n"
                "2. 명령어 목록에서 선택\n"
                "3. 정보 입력 후 Enter\n"
                "**예:** `/질문` → 질문 등록"
            ),
            inline=True
        )
        
        # 스레드 설명
        main_embed.add_field(
            name="🧵 프라이빗 스레드",
            value=(
                "• 개인 전용 대화방\n"
                "• 질문자 + 관리자만 접근\n"
                "• 다른 사람은 볼 수 없음\n"
                "• 개인정보 보호 보장"
            ),
            inline=True
        )
        
        # 사용 가능 명령어
        main_embed.add_field(
            name="🔍 주요 명령어",
            value=(
                "`/질문` - 질문 등록\n"
                "`/내질문` - 내 질문 목록\n"
                "`/faq검색` - FAQ 검색\n"
                "`/faq목록` - FAQ 전체 목록"
            ),
            inline=True
        )
        
        # 질문하기 단계
        main_embed.add_field(
            name="📝 효과적인 질문 등록법",
            value=(
                "**1단계:** `/질문` 입력\n"
                "**2단계:** 필수 정보 입력\n"
                "　　• 운영체제 (Windows, Mac 등)\n"
                "　　• 프로그래밍 언어\n"
                "　　• 에러 메시지 (정확히 복사)\n"
                "　　• 하려던 목적\n"
                "**3단계:** 생성된 스레드에서 이미지 첨부 (선택)"
            ),
            inline=False
        )
        
        # 팁
        main_embed.add_field(
            name="💡 빠른 답변 받는 꿀팁",
            value=(
                "✅ 구체적인 에러 메시지 포함\n"
                "✅ 재현 가능한 최소 코드 제공\n"
                "✅ 예상 결과 vs 실제 결과 명시\n"
                "✅ 스크린샷 첨부\n"
                "✅ 이미 시도한 방법 공유"
            ),
            inline=True
        )
        
        # FAQ
        main_embed.add_field(
            name="❓ 자주 묻는 질문",
            value=(
                "**Q: 다른 사람이 내 질문을 보나요?**\n"
                "A: 아니요! 프라이빗 스레드로 보호됩니다.\n\n"
                "**Q: 언제 답변을 받을 수 있나요?**\n"
                "A: 관리자 확인 후 최대한 빠르게!"
            ),
            inline=True
        )
        
        main_embed.set_footer(text="🤖 InventOnBot | 언제든지 /질문 명령어로 도움을 요청하세요!")
        main_embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
        
        # 메시지 전송 및 고정
        tutorial_msg = await channel.send(embed=main_embed)
        await tutorial_msg.pin()
        
        # 확인 메시지
        confirm_msg = await ctx.send("📌 튜토리얼이 고정되었습니다!")
        await confirm_msg.delete(delay=5)
    
    @commands.command(name="권한확인")
    @commands.has_permissions(manage_messages=True)
    async def check_permissions(self, ctx, channel: Optional[discord.TextChannel] = None):
        """봇의 권한을 확인합니다"""
        if channel is None:
            channel = ctx.channel
        
        bot_permissions = channel.permissions_for(ctx.guild.me)
        
        embed = discord.Embed(
            title=f"🔍 봇 권한 확인 - #{channel.name}",
            color=discord.Color.blue()
        )
        
        # 현재 봇이 가진 권한 정수값 계산
        current_permissions_value = bot_permissions.value
        from config.config import Config
        
        embed.add_field(
            name="📊 권한 정보",
            value=f"현재 권한값: `{current_permissions_value}`\n필요 권한값: `{Config.BOT_PERMISSIONS}`",
            inline=False
        )
        
        # 필수 권한들 체크
        permissions_check = {
            "메시지 전송": bot_permissions.send_messages,
            "임베드 링크": bot_permissions.embed_links,
            "파일 첨부": bot_permissions.attach_files,
            "메시지 관리": bot_permissions.manage_messages,
            "메시지 기록 읽기": bot_permissions.read_message_history,
            "리액션 추가": bot_permissions.add_reactions,
            "스레드 생성": bot_permissions.create_private_threads,
            "스레드 관리": bot_permissions.manage_threads,
        }
        
        success_perms = []
        missing_perms = []
        
        for perm_name, has_perm in permissions_check.items():
            if has_perm:
                success_perms.append(f"✅ {perm_name}")
            else:
                missing_perms.append(f"❌ {perm_name}")
        
        if success_perms:
            embed.add_field(
                name="✅ 보유 권한",
                value="\n".join(success_perms),
                inline=True
            )
        
        if missing_perms:
            embed.add_field(
                name="❌ 부족한 권한",
                value="\n".join(missing_perms),
                inline=True
            )
            embed.color = discord.Color.red()
        else:
            embed.add_field(
                name="🎉 상태",
                value="모든 필수 권한을 보유하고 있습니다!",
                inline=False
            )
            embed.color = discord.Color.green()
        
        await ctx.send(embed=embed, delete_after=30)
    
    @commands.command(name="초대링크")
    @commands.has_permissions(manage_messages=True)
    async def invite_link(self, ctx):
        """봇 초대 링크를 생성합니다 (관리자 전용)"""
        from config.config import Config
        
        # 봇 초대 URL 생성
        invite_url = discord.utils.oauth_url(
            client_id=self.bot.user.id,
            permissions=discord.Permissions(Config.BOT_PERMISSIONS),
            scopes=['bot', 'applications.commands']
        )
        
        embed = discord.Embed(
            title="🔗 InventOnBot 초대 링크",
            description="아래 링크를 사용하여 다른 서버에 봇을 초대할 수 있습니다.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="초대 링크",
            value=f"[**여기를 클릭하여 초대**]({invite_url})",
            inline=False
        )
        
        embed.add_field(
            name="포함된 권한",
            value=(
                "• 메시지 전송 및 관리\n"
                "• 슬래시 명령어 사용\n"
                "• 스레드 생성 및 관리\n"
                "• 파일 첨부 및 임베드\n"
                "• 리액션 추가\n"
                "• 메시지 기록 읽기"
            ),
            inline=False
        )
        
        embed.add_field(
            name="권한 번호",
            value=f"`{Config.BOT_PERMISSIONS}`",
            inline=True
        )
        
        embed.set_footer(text="이 링크는 자동으로 필수 권한을 설정합니다.")
        
        try:
            # 개인 DM으로 전송
            await ctx.author.send(embed=embed)
            await ctx.send("📨 초대 링크를 DM으로 전송했습니다!", delete_after=10)
        except discord.HTTPException:
            # DM 전송 실패 시 채널에 전송
            await ctx.send(embed=embed, delete_after=60)
    
    @invite_link.error
    async def invite_link_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ 이 명령어를 사용하려면 메시지 관리 권한이 필요합니다.", delete_after=10)

async def setup(bot):
    await bot.add_cog(WelcomeSystem(bot))