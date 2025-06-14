import os
from datetime import datetime
from typing import Optional, Dict, List
from utils.logger import setup_logger
from supabase import create_client, Client

class SupabaseManager:
    """Supabase client manager for InventOnBot"""
    
    def __init__(self):
        from config.config import Config
        self.supabase_url = Config.SUPABASE_URL
        self.supabase_key = Config.SUPABASE_ANON_KEY
        self.logger = setup_logger()
        self.client: Client = None
        
    async def initialize(self):
        """Initialize Supabase client"""
        try:
            # Create Supabase client
            self.client = create_client(self.supabase_url, self.supabase_key)
            
            # Test connection and create tables if needed
            await self._create_tables()
            self.logger.info("Supabase client initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Supabase client initialization failed: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables using Supabase client"""
        try:
            # Note: In Supabase, tables are usually created via SQL editor or migrations
            # This is a simplified approach for the bot
            
            # Check if tables exist by trying to select from them
            # If they don't exist, we'll get an error and can create them
            try:
                # Test if users table exists
                self.client.table('users').select('*').limit(1).execute()
            except Exception:
                # Table doesn't exist, create it via RPC or direct SQL
                self.logger.info("Tables need to be created. Please create them manually in Supabase Dashboard.")
                self.logger.info("Or use the SQL editor with the provided SQL schema.")
                
        except Exception as e:
            self.logger.error(f"Error checking/creating tables: {e}")
    
    async def add_user(self, user_id: int, username: str, display_name: str = None, is_admin: bool = False):
        """Add or update user"""
        try:
            # Check if user exists
            existing_user = self.client.table('users').select('*').eq('user_id', user_id).execute()
            
            user_data = {
                'user_id': user_id,
                'username': username,
                'display_name': display_name,
                'is_admin': is_admin
            }
            
            if existing_user.data:
                # Update existing user
                result = self.client.table('users').update(user_data).eq('user_id', user_id).execute()
            else:
                # Insert new user
                result = self.client.table('users').insert(user_data).execute()
                # Update daily stats for new user
                await self.update_daily_stats('new_users')
                
        except Exception as e:
            self.logger.error(f"Error adding user {user_id}: {e}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            result = self.client.table('users').select('*').eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def create_question(self, user_id: int, thread_id: int, title: str, 
                            os: str, programming_language: str, error_message: str, 
                            purpose: str, code_snippet: str = None, log_files: str = None,
                            screenshot_url: str = None, attempted_solutions: str = None) -> int:
        """Create a new question"""
        try:
            question_data = {
                'user_id': user_id,
                'thread_id': thread_id,
                'title': title,
                'os': os,
                'programming_language': programming_language,
                'error_message': error_message,
                'purpose': purpose,
                'code_snippet': code_snippet,
                'log_files': log_files,
                'screenshot_url': screenshot_url,
                'attempted_solutions': attempted_solutions,
                'status': 'open'
            }
            
            result = self.client.table('questions').insert(question_data).execute()
            if result.data:
                return result.data[0]['id']
            raise Exception("Failed to create question")
            
        except Exception as e:
            self.logger.error(f"Error creating question: {e}")
            raise
    
    async def get_question(self, question_id: int) -> Optional[Dict]:
        """Get question by ID"""
        try:
            result = self.client.table('questions').select('*').eq('id', question_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting question {question_id}: {e}")
            return None
    
    async def get_question_by_thread(self, thread_id: int) -> Optional[Dict]:
        """Get question by thread ID"""
        try:
            result = self.client.table('questions').select('*').eq('thread_id', thread_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting question by thread {thread_id}: {e}")
            return None
    
    async def update_question_status(self, question_id: int, status: str):
        """Update question status"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            result = self.client.table('questions').update(update_data).eq('id', question_id).execute()
            if not result.data:
                raise Exception(f"Question {question_id} not found")
                
        except Exception as e:
            self.logger.error(f"Error updating question status: {e}")
            raise
    
    async def add_answer(self, question_id: int, admin_id: int, answer_text: str, is_solution: bool = False) -> int:
        """Add an answer to a question"""
        try:
            answer_data = {
                'question_id': question_id,
                'admin_id': admin_id,
                'answer_text': answer_text,
                'is_solution': is_solution
            }
            
            result = self.client.table('answers').insert(answer_data).execute()
            if result.data:
                return result.data[0]['id']
            raise Exception("Failed to add answer")
            
        except Exception as e:
            self.logger.error(f"Error adding answer: {e}")
            raise
    
    async def get_user_questions(self, user_id: int) -> List[Dict]:
        """Get all questions for a user"""
        try:
            result = self.client.table('questions').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Error getting user questions: {e}")
            return []
    
    # FAQ related methods
    async def add_faq(self, question: str, answer: str, keywords: str = None, created_by: int = None) -> int:
        """Add a new FAQ"""
        try:
            faq_data = {
                'question': question,
                'answer': answer,
                'keywords': keywords,
                'created_by': created_by
            }
            
            result = self.client.table('faq').insert(faq_data).execute()
            if result.data:
                return result.data[0]['id']
            raise Exception("Failed to add FAQ")
            
        except Exception as e:
            self.logger.error(f"Error adding FAQ: {e}")
            raise
    
    async def search_faq(self, keyword: str) -> List[Dict]:
        """Search FAQ by keyword"""
        try:
            # Supabase supports text search
            result = self.client.table('faq').select('*').or_(
                f'question.ilike.%{keyword}%,answer.ilike.%{keyword}%,keywords.ilike.%{keyword}%'
            ).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Error searching FAQ: {e}")
            return []
    
    async def get_all_faq(self) -> List[Dict]:
        """Get all FAQs"""
        try:
            result = self.client.table('faq').select('*').order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Error getting all FAQ: {e}")
            return []
    
    async def get_faq_by_id(self, faq_id: int) -> Optional[Dict]:
        """Get FAQ by ID"""
        try:
            result = self.client.table('faq').select('*').eq('id', faq_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            self.logger.error(f"Error getting FAQ {faq_id}: {e}")
            return None
    
    async def delete_faq(self, faq_id: int):
        """Delete FAQ by ID"""
        try:
            result = self.client.table('faq').delete().eq('id', faq_id).execute()
            if not result.data:
                raise Exception(f"FAQ {faq_id} not found")
        except Exception as e:
            self.logger.error(f"Error deleting FAQ: {e}")
            raise
    
    async def update_faq(self, faq_id: int, question: str = None, answer: str = None, keywords: str = None):
        """Update FAQ"""
        try:
            update_data = {}
            if question:
                update_data['question'] = question
            if answer:
                update_data['answer'] = answer
            if keywords:
                update_data['keywords'] = keywords
            
            if update_data:
                result = self.client.table('faq').update(update_data).eq('id', faq_id).execute()
                if not result.data:
                    raise Exception(f"FAQ {faq_id} not found")
        except Exception as e:
            self.logger.error(f"Error updating FAQ: {e}")
            raise
    
    # Statistics tracking methods
    async def update_daily_stats(self, stat_type: str, increment: int = 1):
        """Update daily statistics"""
        try:
            today = datetime.now().date().isoformat()
            
            # Check if today's stats exist
            existing = self.client.table('daily_stats').select('*').eq('date', today).execute()
            
            if existing.data:
                # Update existing record
                current_value = existing.data[0].get(stat_type, 0)
                update_data = {stat_type: current_value + increment}
                self.client.table('daily_stats').update(update_data).eq('date', today).execute()
            else:
                # Create new record
                new_data = {
                    'date': today,
                    'questions_created': 1 if stat_type == 'questions_created' else 0,
                    'questions_solved': 1 if stat_type == 'questions_solved' else 0,
                    'answers_given': 1 if stat_type == 'answers_given' else 0,
                    'new_users': 1 if stat_type == 'new_users' else 0,
                    'faq_searches': 1 if stat_type == 'faq_searches' else 0
                }
                self.client.table('daily_stats').insert(new_data).execute()
                
        except Exception as e:
            self.logger.error(f"Error updating daily stats: {e}")
    
    async def record_response_time(self, question_id: int, minutes: int):
        """Record response time for a question"""
        try:
            response_data = {
                'question_id': question_id,
                'response_time_minutes': minutes
            }
            
            self.client.table('response_times').insert(response_data).execute()
        except Exception as e:
            self.logger.error(f"Error recording response time: {e}")
    
    async def get_statistics_data(self, days: int = 30) -> Dict:
        """Get comprehensive statistics data"""
        try:
            stats = {}
            
            # Calculate date range
            from datetime import date, timedelta
            start_date = (date.today() - timedelta(days=days)).isoformat()
            
            # Daily stats for the period
            daily_result = self.client.table('daily_stats').select('*').gte('date', start_date).order('date').execute()
            stats['daily_data'] = daily_result.data or []
            
            # Average response time
            response_result = self.client.table('response_times').select('response_time_minutes').gte('created_at', start_date).execute()
            if response_result.data:
                total_time = sum(item['response_time_minutes'] for item in response_result.data)
                stats['avg_response_time'] = total_time / len(response_result.data)
            else:
                stats['avg_response_time'] = 0
            
            # Top languages
            lang_result = self.client.table('questions').select('programming_language').gte('created_at', start_date).execute()
            if lang_result.data:
                from collections import Counter
                lang_counts = Counter(item['programming_language'] for item in lang_result.data)
                stats['top_languages'] = [{'programming_language': lang, 'count': count} 
                                        for lang, count in lang_counts.most_common(10)]
            else:
                stats['top_languages'] = []
            
            # Status distribution
            status_result = self.client.table('questions').select('status').gte('created_at', start_date).execute()
            if status_result.data:
                from collections import Counter
                status_counts = Counter(item['status'] for item in status_result.data)
                stats['status_distribution'] = [{'status': status, 'count': count} 
                                              for status, count in status_counts.items()]
            else:
                stats['status_distribution'] = []
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
    
    async def close(self):
        """Close Supabase client (no-op as it's stateless)"""
        self.logger.info("Supabase client closed")
