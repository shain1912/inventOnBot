import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional, Dict, List, Tuple
import aiosqlite
import asyncio
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import io
import base64

class StatisticsSystem(commands.Cog):
    """상세 통계 시스템"""
    
    def __init__(self, bot):
        self.bot = bot
        # 한글 폰트 설정 (시스템에 따라 조정 필요)
        plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
    
    def is_admin(self, user: discord.Member) -> bool:
        """Check if user is admin"""
        from config.config import Config
        admin_role = user.guild.get_role(Config.ADMIN_ROLE_ID)
        return admin_role in user.roles if admin_role else False
    
    @app_commands.command(name="통계", description="종합 통계를 확인합니다 (관리자 전용)")
    async def comprehensive_stats(self, interaction: discord.Interaction):
        """Show comprehensive statistics"""
        if not self.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            db_manager = self.bot.db_manager
            
            # 기본 통계 수집
            basic_stats = await self._get_basic_statistics(db_manager)
            
            # 임베드 생성
            embed = discord.Embed(
                title="📊 InventOnBot 종합 통계",
                description="봇 사용 현황과 상세 분석 정보입니다.",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            # 기본 통계
            embed.add_field(
                name="📝 질문 통계",
                value=(
                    f"총 질문 수: **{basic_stats['total_questions']}**\n"
                    f"✅ 해결됨: **{basic_stats['solved_questions']}** "
                    f"({basic_stats['solve_rate']:.1f}%)\n"
                    f"🟡 진행중: **{basic_stats['in_progress_questions']}**\n"
                    f"🔵 대기중: **{basic_stats['open_questions']}**"
                ),
                inline=True
            )
            
            # 사용자 통계
            embed.add_field(
                name="👥 사용자 통계",
                value=(
                    f"총 사용자: **{basic_stats['total_users']}**\n"
                    f"활성 사용자: **{basic_stats['active_users']}**\n"
                    f"신규 사용자: **{basic_stats['new_users_week']}**\n"
                    f"(최근 7일)"
                ),
                inline=True
            )
            
            # 응답 시간 통계
            embed.add_field(
                name="⏱️ 응답 시간",
                value=(
                    f"평균 응답 시간: **{basic_stats['avg_response_time']}**\n"
                    f"최고 응답 시간: **{basic_stats['fastest_response']}**\n"
                    f"총 답변 수: **{basic_stats['total_answers']}**"
                ),
                inline=True
            )
            
            # 인기 언어
            if basic_stats['popular_languages']:
                lang_text = "\n".join([
                    f"{i+1}. {lang}: {count}개" 
                    for i, (lang, count) in enumerate(basic_stats['popular_languages'][:5])
                ])
                embed.add_field(
                    name="💻 인기 프로그래밍 언어",
                    value=lang_text,
                    inline=True
                )
            
            # 최근 활동
            embed.add_field(
                name="📈 최근 활동 (7일)",
                value=(
                    f"새 질문: **{basic_stats['recent_questions']}**\n"
                    f"새 답변: **{basic_stats['recent_answers']}**\n"
                    f"해결된 문제: **{basic_stats['recent_solved']}**"
                ),
                inline=True
            )
            
            # FAQ 통계
            embed.add_field(
                name="❓ FAQ 통계",
                value=(
                    f"총 FAQ: **{basic_stats['total_faq']}**\n"
                    f"이번주 검색: **{basic_stats['faq_searches_week']}**"
                ),
                inline=True
            )
            
            embed.set_footer(text="💡 자세한 분석은 /상세통계 명령어를 사용하세요")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error generating comprehensive stats: {e}")
            await interaction.followup.send(
                "❌ 통계 생성 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="상세통계", description="상세 통계와 그래프를 생성합니다 (관리자 전용)")
    @app_commands.describe(
        period="분석 기간 (week/month/quarter/all)",
        chart_type="차트 타입 (daily/weekly/language/status)"
    )
    async def detailed_stats(
        self,
        interaction: discord.Interaction,
        period: str = "month",
        chart_type: str = "daily"
    ):
        """Generate detailed statistics with charts"""
        if not self.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
                ephemeral=True
            )
            return
        
        valid_periods = ['week', 'month', 'quarter', 'all']
        valid_charts = ['daily', 'weekly', 'language', 'status']
        
        if period not in valid_periods:
            await interaction.response.send_message(
                f"❌ 유효하지 않은 기간입니다. 사용 가능: {', '.join(valid_periods)}",
                ephemeral=True
            )
            return
        
        if chart_type not in valid_charts:
            await interaction.response.send_message(
                f"❌ 유효하지 않은 차트 타입입니다. 사용 가능: {', '.join(valid_charts)}",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            db_manager = self.bot.db_manager
            
            # 차트 생성
            chart_buffer = await self._generate_chart(db_manager, period, chart_type)
            
            # 상세 통계 데이터 수집
            detailed_stats = await self._get_detailed_statistics(db_manager, period)
            
            # 임베드 생성
            embed = discord.Embed(
                title=f"📈 상세 통계 분석 ({period.upper()})",
                description=f"차트 타입: {chart_type.upper()}",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            # 기간별 상세 정보
            embed.add_field(
                name="📊 분석 결과",
                value=(
                    f"분석 기간: **{detailed_stats['period_name']}**\n"
                    f"총 질문: **{detailed_stats['total_questions']}**\n"
                    f"해결률: **{detailed_stats['solve_rate']:.1f}%**\n"
                    f"평균 일일 질문: **{detailed_stats['avg_daily_questions']:.1f}**"
                ),
                inline=False
            )
            
            if detailed_stats['trends']:
                embed.add_field(
                    name="📈 트렌드 분석",
                    value=detailed_stats['trends'],
                    inline=False
                )
            
            # 차트 첨부
            if chart_buffer:
                file = discord.File(chart_buffer, filename=f"stats_{chart_type}_{period}.png")
                embed.set_image(url=f"attachment://stats_{chart_type}_{period}.png")
                
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error generating detailed stats: {e}")
            await interaction.followup.send(
                "❌ 상세 통계 생성 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    @app_commands.command(name="사용자통계", description="개별 사용자 통계를 확인합니다")
    @app_commands.describe(user="통계를 확인할 사용자 (미입력시 자신의 통계)")
    async def user_stats(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Show individual user statistics"""
        target_user = user or interaction.user
        
        # 관리자가 아니면 자신의 통계만 볼 수 있음
        if not self.is_admin(interaction.user) and target_user != interaction.user:
            await interaction.response.send_message(
                "❌ 다른 사용자의 통계는 관리자만 확인할 수 있습니다.",
                ephemeral=True
            )
            return
        
        try:
            db_manager = self.bot.db_manager
            user_data = await self._get_user_statistics(db_manager, target_user.id)
            
            embed = discord.Embed(
                title=f"👤 {target_user.display_name}님의 통계",
                color=discord.Color.purple(),
                timestamp=discord.utils.utcnow()
            )
            
            embed.set_thumbnail(url=target_user.avatar.url if target_user.avatar else target_user.default_avatar.url)
            
            embed.add_field(
                name="📝 질문 활동",
                value=(
                    f"총 질문 수: **{user_data['total_questions']}**\n"
                    f"해결된 질문: **{user_data['solved_questions']}**\n"
                    f"진행 중인 질문: **{user_data['active_questions']}**\n"
                    f"해결률: **{user_data['solve_rate']:.1f}%**"
                ),
                inline=True
            )
            
            if user_data['favorite_languages']:
                lang_text = ", ".join(user_data['favorite_languages'][:3])
                embed.add_field(
                    name="💻 주요 언어",
                    value=lang_text,
                    inline=True
                )
            
            embed.add_field(
                name="📊 활동 정보",
                value=(
                    f"첫 질문: **{user_data['first_question_date']}**\n"
                    f"최근 질문: **{user_data['last_question_date']}**\n"
                    f"평균 응답 시간: **{user_data['avg_response_time']}**"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            self.bot.logger.error(f"Error generating user stats: {e}")
            await interaction.response.send_message(
                "❌ 사용자 통계 생성 중 오류가 발생했습니다.",
                ephemeral=True
            )
    
    async def _get_basic_statistics(self, db_manager) -> Dict:
        """기본 통계 데이터 수집"""
        try:
            async with aiosqlite.connect(db_manager.db_path) as db:
                stats = {}
                
                # 질문 통계
                async with db.execute('SELECT COUNT(*) FROM questions') as cursor:
                    stats['total_questions'] = (await cursor.fetchone())[0]
                
                async with db.execute("SELECT COUNT(*) FROM questions WHERE status = 'solved'") as cursor:
                    stats['solved_questions'] = (await cursor.fetchone())[0]
                
                async with db.execute("SELECT COUNT(*) FROM questions WHERE status = 'in_progress'") as cursor:
                    stats['in_progress_questions'] = (await cursor.fetchone())[0]
                
                async with db.execute("SELECT COUNT(*) FROM questions WHERE status = 'open'") as cursor:
                    stats['open_questions'] = (await cursor.fetchone())[0]
                
                # 해결률 계산
                if stats['total_questions'] > 0:
                    stats['solve_rate'] = (stats['solved_questions'] / stats['total_questions']) * 100
                else:
                    stats['solve_rate'] = 0
                
                # 사용자 통계
                async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                    stats['total_users'] = (await cursor.fetchone())[0]
                
                # 활성 사용자 (최근 30일 내 질문한 사용자)
                async with db.execute('''
                    SELECT COUNT(DISTINCT user_id) FROM questions 
                    WHERE created_at >= date('now', '-30 days')
                ''') as cursor:
                    stats['active_users'] = (await cursor.fetchone())[0]
                
                # 신규 사용자 (최근 7일)
                async with db.execute('''
                    SELECT COUNT(*) FROM users 
                    WHERE created_at >= date('now', '-7 days')
                ''') as cursor:
                    stats['new_users_week'] = (await cursor.fetchone())[0]
                
                # 답변 통계
                async with db.execute('SELECT COUNT(*) FROM answers') as cursor:
                    stats['total_answers'] = (await cursor.fetchone())[0]
                
                # 평균 응답 시간 계산 (간단화)
                stats['avg_response_time'] = "계산 중..."
                stats['fastest_response'] = "계산 중..."
                
                # 인기 프로그래밍 언어
                async with db.execute('''
                    SELECT programming_language, COUNT(*) as count 
                    FROM questions 
                    GROUP BY programming_language 
                    ORDER BY count DESC 
                    LIMIT 5
                ''') as cursor:
                    stats['popular_languages'] = await cursor.fetchall()
                
                # 최근 활동 (7일)
                async with db.execute('''
                    SELECT COUNT(*) FROM questions 
                    WHERE created_at >= date('now', '-7 days')
                ''') as cursor:
                    stats['recent_questions'] = (await cursor.fetchone())[0]
                
                async with db.execute('''
                    SELECT COUNT(*) FROM answers 
                    WHERE created_at >= date('now', '-7 days')
                ''') as cursor:
                    stats['recent_answers'] = (await cursor.fetchone())[0]
                
                async with db.execute('''
                    SELECT COUNT(*) FROM questions 
                    WHERE status = 'solved' AND updated_at >= date('now', '-7 days')
                ''') as cursor:
                    stats['recent_solved'] = (await cursor.fetchone())[0]
                
                # FAQ 통계
                async with db.execute('SELECT COUNT(*) FROM faq') as cursor:
                    stats['total_faq'] = (await cursor.fetchone())[0]
                
                # FAQ 검색 수는 별도 테이블이 없으므로 기본값
                stats['faq_searches_week'] = 0
                
                return stats
                
        except Exception as e:
            self.bot.logger.error(f"Error collecting basic statistics: {e}")
            return {}
    
    async def _get_detailed_statistics(self, db_manager, period: str) -> Dict:
        """상세 통계 데이터 수집"""
        # 기간 설정
        if period == 'week':
            date_filter = "date('now', '-7 days')"
            period_name = "최근 7일"
        elif period == 'month':
            date_filter = "date('now', '-30 days')"
            period_name = "최근 30일"
        elif period == 'quarter':
            date_filter = "date('now', '-90 days')"
            period_name = "최근 90일"
        else:  # all
            date_filter = "'1970-01-01'"
            period_name = "전체 기간"
        
        try:
            async with aiosqlite.connect(db_manager.db_path) as db:
                stats = {'period_name': period_name}
                
                # 기간 내 총 질문 수
                async with db.execute(f'''
                    SELECT COUNT(*) FROM questions 
                    WHERE created_at >= {date_filter}
                ''') as cursor:
                    stats['total_questions'] = (await cursor.fetchone())[0]
                
                # 기간 내 해결된 질문 수
                async with db.execute(f'''
                    SELECT COUNT(*) FROM questions 
                    WHERE status = 'solved' AND created_at >= {date_filter}
                ''') as cursor:
                    solved = (await cursor.fetchone())[0]
                
                # 해결률
                if stats['total_questions'] > 0:
                    stats['solve_rate'] = (solved / stats['total_questions']) * 100
                else:
                    stats['solve_rate'] = 0
                
                # 평균 일일 질문 수
                days = 7 if period == 'week' else 30 if period == 'month' else 90 if period == 'quarter' else 365
                stats['avg_daily_questions'] = stats['total_questions'] / days
                
                # 간단한 트렌드 분석
                if stats['total_questions'] > 0:
                    if stats['solve_rate'] >= 80:
                        trend = "🟢 높은 해결률을 유지하고 있습니다!"
                    elif stats['solve_rate'] >= 60:
                        trend = "🟡 양호한 해결률입니다."
                    else:
                        trend = "🔴 해결률 개선이 필요합니다."
                    
                    if stats['avg_daily_questions'] >= 5:
                        trend += "\n📈 활발한 질문 활동을 보이고 있습니다."
                    elif stats['avg_daily_questions'] >= 1:
                        trend += "\n📊 적당한 질문 활동을 보이고 있습니다."
                    else:
                        trend += "\n📉 질문 활동이 저조합니다."
                    
                    stats['trends'] = trend
                else:
                    stats['trends'] = "📭 분석할 데이터가 부족합니다."
                
                return stats
                
        except Exception as e:
            self.bot.logger.error(f"Error collecting detailed statistics: {e}")
            return {'period_name': period_name, 'total_questions': 0, 'solve_rate': 0, 'avg_daily_questions': 0, 'trends': '오류 발생'}
    
    async def _get_user_statistics(self, db_manager, user_id: int) -> Dict:
        """사용자별 통계 데이터 수집"""
        try:
            async with aiosqlite.connect(db_manager.db_path) as db:
                stats = {}
                
                # 총 질문 수
                async with db.execute('SELECT COUNT(*) FROM questions WHERE user_id = ?', (user_id,)) as cursor:
                    stats['total_questions'] = (await cursor.fetchone())[0]
                
                # 해결된 질문 수
                async with db.execute("SELECT COUNT(*) FROM questions WHERE user_id = ? AND status = 'solved'", (user_id,)) as cursor:
                    stats['solved_questions'] = (await cursor.fetchone())[0]
                
                # 진행 중인 질문 수
                async with db.execute("SELECT COUNT(*) FROM questions WHERE user_id = ? AND status IN ('open', 'in_progress')", (user_id,)) as cursor:
                    stats['active_questions'] = (await cursor.fetchone())[0]
                
                # 해결률
                if stats['total_questions'] > 0:
                    stats['solve_rate'] = (stats['solved_questions'] / stats['total_questions']) * 100
                else:
                    stats['solve_rate'] = 0
                
                # 자주 사용하는 언어
                async with db.execute('''
                    SELECT programming_language, COUNT(*) as count 
                    FROM questions WHERE user_id = ? 
                    GROUP BY programming_language 
                    ORDER BY count DESC 
                    LIMIT 3
                ''', (user_id,)) as cursor:
                    languages = await cursor.fetchall()
                    stats['favorite_languages'] = [lang[0] for lang in languages]
                
                # 첫 질문과 최근 질문 날짜
                async with db.execute('''
                    SELECT MIN(created_at), MAX(created_at) 
                    FROM questions WHERE user_id = ?
                ''', (user_id,)) as cursor:
                    dates = await cursor.fetchone()
                    if dates[0]:
                        stats['first_question_date'] = dates[0][:10]
                        stats['last_question_date'] = dates[1][:10]
                    else:
                        stats['first_question_date'] = "없음"
                        stats['last_question_date'] = "없음"
                
                # 평균 응답 시간 (간단화)
                stats['avg_response_time'] = "계산 중..."
                
                return stats
                
        except Exception as e:
            self.bot.logger.error(f"Error collecting user statistics: {e}")
            return {}
    
    @app_commands.command(name="대시보드", description="실시간 대시보드를 표시합니다 (관리자 전용)")
    async def dashboard(self, interaction: discord.Interaction):
        """실시간 대시보드 표시"""
        if not self.is_admin(interaction.user):
            await interaction.response.send_message(
                "❌ 이 명령어는 관리자만 사용할 수 있습니다.",
                ephemeral=True
            )
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            db_manager = self.bot.db_manager
            dashboard_data = await self._get_dashboard_data(db_manager)
            
            embed = discord.Embed(
                title="📊 InventOnBot 대시보드",
                description="실시간 사용 현황",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            
            # 오늘의 활동
            embed.add_field(
                name="🔥 오늘의 활동",
                value=(
                    f"새 질문: **{dashboard_data['today_questions']}**\n"
                    f"답변 수: **{dashboard_data['today_answers']}**\n"
                    f"해결된 문제: **{dashboard_data['today_solved']}**\n"
                    f"신규 사용자: **{dashboard_data['today_new_users']}**"
                ),
                inline=True
            )
            
            # 이번 주 요약
            embed.add_field(
                name="📈 이번 주 (7일)",
                value=(
                    f"질문 수: **{dashboard_data['week_questions']}**\n"
                    f"해결률: **{dashboard_data['week_solve_rate']:.1f}%**\n"
                    f"평균 일일 질문: **{dashboard_data['avg_daily']:.1f}**\n"
                    f"평균 응답시간: **{dashboard_data['avg_response_time']}**"
                ),
                inline=True
            )
            
            # 현재 상태
            embed.add_field(
                name="🔄 현재 상태",
                value=(
                    f"대기중 질문: **{dashboard_data['pending_questions']}**\n"
                    f"진행중 질문: **{dashboard_data['active_questions']}**\n"
                    f"총 사용자: **{dashboard_data['total_users']}**\n"
                    f"총 FAQ: **{dashboard_data['total_faq']}**"
                ),
                inline=True
            )
            
            # 인기 언어 (이번 주)
            if dashboard_data['popular_languages_week']:
                lang_text = "\n".join([
                    f"{i+1}. {lang}: {count}개" 
                    for i, (lang, count) in enumerate(dashboard_data['popular_languages_week'][:3])
                ])
                embed.add_field(
                    name="💻 인기 언어 (이번주)",
                    value=lang_text,
                    inline=True
                )
            
            # 성과 지표
            embed.add_field(
                name="🏆 성과 지표",
                value=(
                    f"전체 해결률: **{dashboard_data['total_solve_rate']:.1f}%**\n"
                    f"이번주 효율: **{dashboard_data['week_efficiency']}**\n"
                    f"사용자 만족도: **{dashboard_data['satisfaction']}**"
                ),
                inline=True
            )
            
            # 알림 및 경고
            alerts = []
            if dashboard_data['pending_questions'] > 5:
                alerts.append("🔴 대기중인 질문이 많습니다!")
            if dashboard_data['week_solve_rate'] < 70:
                alerts.append("🟡 이번주 해결률이 낮습니다.")
            if dashboard_data['avg_response_time_minutes'] > 1440:  # 24시간 이상
                alerts.append("🟠 평균 응답시간이 깁니다.")
            
            if alerts:
                embed.add_field(
                    name="⚠️ 알림",
                    value="\n".join(alerts),
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ 상태",
                    value="**모든 지표가 양호합니다!**",
                    inline=False
                )
            
            embed.set_footer(text="🔄 자동 업데이트되는 대시보드입니다")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            self.bot.logger.error(f"Error generating dashboard: {e}")
            await interaction.followup.send(
                "❌ 대시보드 생성 중 오류가 발생했습니다.",
                ephemeral=True
            )
        """차트 생성"""
        try:
            # 차트 생성은 복잡하므로 기본 구조만 구현
            # 실제 환경에서는 matplotlib 설치 필요
            
            plt.figure(figsize=(10, 6))
            
            if chart_type == "daily":
                # 일별 질문 수 차트
                plt.title("일별 질문 수")
                plt.xlabel("날짜")
                plt.ylabel("질문 수")
                # 실제 데이터 조회 및 그래프 생성 코드 필요
                
            elif chart_type == "language":
                # 언어별 질문 수 파이 차트
                plt.title("프로그래밍 언어별 질문 분포")
                # 실제 데이터 조회 및 파이차트 생성 코드 필요
            
            # 차트를 바이트 버퍼로 저장
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            plt.close()
            
            return buffer
            
        except Exception as e:
            self.bot.logger.error(f"Error generating chart: {e}")
            return None

async def setup(bot):
    await bot.add_cog(StatisticsSystem(bot))