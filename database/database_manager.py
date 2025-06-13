import aiosqlite
import os
from datetime import datetime
from typing import Optional, Dict, List
from utils.logger import setup_logger

class DatabaseManager:
    """Database manager for InventOnBot"""
    
    def __init__(self, db_path: str = None):
        from config.config import Config
        self.db_path = db_path or Config.DATABASE_PATH
        self.logger = setup_logger()
        
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            # Ensure database directory exists
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Create tables
            await self._create_tables()
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    display_name TEXT,
                    is_admin BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Questions table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    thread_id INTEGER UNIQUE,
                    title TEXT NOT NULL,
                    os TEXT NOT NULL,
                    programming_language TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    code_snippet TEXT,
                    log_files TEXT,
                    screenshot_url TEXT,
                    attempted_solutions TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Answers table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    admin_id INTEGER NOT NULL,
                    answer_text TEXT NOT NULL,
                    is_solution BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions (id),
                    FOREIGN KEY (admin_id) REFERENCES users (user_id)
                )
            ''')
            
            # FAQ table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS faq (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    keywords TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users (user_id)
                )
            ''')
            
            # Statistics tracking table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    questions_created INTEGER DEFAULT 0,
                    questions_solved INTEGER DEFAULT 0,
                    answers_given INTEGER DEFAULT 0,
                    new_users INTEGER DEFAULT 0,
                    faq_searches INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Response time tracking
            await db.execute('''
                CREATE TABLE IF NOT EXISTS response_times (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER,
                    response_time_minutes INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (question_id) REFERENCES questions (id)
                )
            ''')
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: str, display_name: str = None, is_admin: bool = False):
        """Add or update user"""
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user already exists
            async with db.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,)) as cursor:
                existing_user = await cursor.fetchone()
            
            await db.execute('''
                INSERT OR REPLACE INTO users (user_id, username, display_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, display_name, is_admin))
            await db.commit()
            
            # If this is a new user, update daily stats
            if not existing_user:
                await self.update_daily_stats('new_users')
    
    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM users WHERE user_id = ?', (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'user_id': row[0],
                        'username': row[1],
                        'display_name': row[2],
                        'is_admin': bool(row[3]),
                        'created_at': row[4]
                    }
                return None
    
    async def create_question(self, user_id: int, thread_id: int, title: str, 
                            os: str, programming_language: str, error_message: str, 
                            purpose: str, code_snippet: str = None, log_files: str = None,
                            screenshot_url: str = None, attempted_solutions: str = None) -> int:
        """Create a new question"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO questions (user_id, thread_id, title, os, programming_language, 
                                     error_message, purpose, code_snippet, log_files, 
                                     screenshot_url, attempted_solutions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, thread_id, title, os, programming_language, error_message, 
                  purpose, code_snippet, log_files, screenshot_url, attempted_solutions))
            await db.commit()
            return cursor.lastrowid
    
    async def get_question(self, question_id: int) -> Optional[Dict]:
        """Get question by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM questions WHERE id = ?', (question_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'thread_id': row[2],
                        'title': row[3],
                        'os': row[4],
                        'programming_language': row[5],
                        'error_message': row[6],
                        'purpose': row[7],
                        'code_snippet': row[8],
                        'log_files': row[9],
                        'screenshot_url': row[10],
                        'attempted_solutions': row[11],
                        'status': row[12],
                        'created_at': row[13],
                        'updated_at': row[14]
                    }
                return None
    
    async def get_question_by_thread(self, thread_id: int) -> Optional[Dict]:
        """Get question by thread ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM questions WHERE thread_id = ?', (thread_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'user_id': row[1],
                        'thread_id': row[2],
                        'title': row[3],
                        'os': row[4],
                        'programming_language': row[5],
                        'error_message': row[6],
                        'purpose': row[7],
                        'code_snippet': row[8],
                        'log_files': row[9],
                        'screenshot_url': row[10],
                        'attempted_solutions': row[11],
                        'status': row[12],
                        'created_at': row[13],
                        'updated_at': row[14]
                    }
                return None
    
    async def update_question_status(self, question_id: int, status: str):
        """Update question status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE questions 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (status, question_id))
            await db.commit()
    
    async def add_answer(self, question_id: int, admin_id: int, answer_text: str, is_solution: bool = False) -> int:
        """Add an answer to a question"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO answers (question_id, admin_id, answer_text, is_solution)
                VALUES (?, ?, ?, ?)
            ''', (question_id, admin_id, answer_text, is_solution))
            await db.commit()
            return cursor.lastrowid
    
    async def get_user_questions(self, user_id: int) -> List[Dict]:
        """Get all questions for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM questions WHERE user_id = ? ORDER BY created_at DESC', 
                (user_id,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{
                    'id': row[0],
                    'user_id': row[1],
                    'thread_id': row[2],
                    'title': row[3],
                    'os': row[4],
                    'programming_language': row[5],
                    'error_message': row[6],
                    'purpose': row[7],
                    'code_snippet': row[8],
                    'log_files': row[9],
                    'screenshot_url': row[10],
                    'attempted_solutions': row[11],
                    'status': row[12],
                    'created_at': row[13],
                    'updated_at': row[14]
                } for row in rows]
    
    async def close(self):
        """Close database connection"""
        # For aiosqlite, connections are automatically managed
        pass
    
    # FAQ related methods
    async def add_faq(self, question: str, answer: str, keywords: str = None, created_by: int = None) -> int:
        """Add a new FAQ"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO faq (question, answer, keywords, created_by)
                VALUES (?, ?, ?, ?)
            ''', (question, answer, keywords, created_by))
            await db.commit()
            return cursor.lastrowid
    
    async def search_faq(self, keyword: str) -> List[Dict]:
        """Search FAQ by keyword"""
        async with aiosqlite.connect(self.db_path) as db:
            # Search in question, answer, and keywords
            search_term = f'%{keyword}%'
            async with db.execute('''
                SELECT * FROM faq 
                WHERE question LIKE ? OR answer LIKE ? OR keywords LIKE ?
                ORDER BY created_at DESC
            ''', (search_term, search_term, search_term)) as cursor:
                rows = await cursor.fetchall()
                return [{
                    'id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'keywords': row[3],
                    'created_by': row[4],
                    'created_at': row[5]
                } for row in rows]
    
    async def get_all_faq(self) -> List[Dict]:
        """Get all FAQs"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM faq ORDER BY created_at DESC'
            ) as cursor:
                rows = await cursor.fetchall()
                return [{
                    'id': row[0],
                    'question': row[1],
                    'answer': row[2],
                    'keywords': row[3],
                    'created_by': row[4],
                    'created_at': row[5]
                } for row in rows]
    
    async def get_faq_by_id(self, faq_id: int) -> Optional[Dict]:
        """Get FAQ by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                'SELECT * FROM faq WHERE id = ?', (faq_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        'id': row[0],
                        'question': row[1],
                        'answer': row[2],
                        'keywords': row[3],
                        'created_by': row[4],
                        'created_at': row[5]
                    }
                return None
    
    async def delete_faq(self, faq_id: int):
        """Delete FAQ by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM faq WHERE id = ?', (faq_id,))
            await db.commit()
    
    async def update_faq(self, faq_id: int, question: str = None, answer: str = None, keywords: str = None):
        """Update FAQ"""
        fields = []
        values = []
        
        if question:
            fields.append('question = ?')
            values.append(question)
        if answer:
            fields.append('answer = ?')
            values.append(answer)
        if keywords:
            fields.append('keywords = ?')
            values.append(keywords)
        
        if fields:
            values.append(faq_id)
            query = f'UPDATE faq SET {", ".join(fields)} WHERE id = ?'
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(query, values)
                await db.commit()
    
    # Statistics tracking methods
    async def update_daily_stats(self, stat_type: str, increment: int = 1):
        """Update daily statistics"""
        today = datetime.now().date().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Insert or update today's stats
            await db.execute(f'''
                INSERT INTO daily_stats (date, {stat_type}) 
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET 
                {stat_type} = {stat_type} + ?
            ''', (today, increment, increment))
            await db.commit()
    
    async def record_response_time(self, question_id: int, minutes: int):
        """Record response time for a question"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO response_times (question_id, response_time_minutes)
                VALUES (?, ?)
            ''', (question_id, minutes))
            await db.commit()
    
    async def get_statistics_data(self, days: int = 30) -> Dict:
        """Get comprehensive statistics data"""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}
            
            # Daily stats for the period
            async with db.execute(f'''
                SELECT date, questions_created, questions_solved, answers_given, new_users
                FROM daily_stats 
                WHERE date >= date('now', '-{days} days')
                ORDER BY date
            ''') as cursor:
                daily_data = await cursor.fetchall()
                stats['daily_data'] = daily_data
            
            # Average response time
            async with db.execute('''
                SELECT AVG(response_time_minutes) 
                FROM response_times 
                WHERE created_at >= date('now', '-30 days')
            ''') as cursor:
                avg_time = await cursor.fetchone()
                stats['avg_response_time'] = avg_time[0] if avg_time[0] else 0
            
            # Top languages
            async with db.execute('''
                SELECT programming_language, COUNT(*) as count
                FROM questions 
                WHERE created_at >= date('now', '-30 days')
                GROUP BY programming_language 
                ORDER BY count DESC 
                LIMIT 10
            ''') as cursor:
                stats['top_languages'] = await cursor.fetchall()
            
            # Status distribution
            async with db.execute('''
                SELECT status, COUNT(*) as count
                FROM questions 
                WHERE created_at >= date('now', '-30 days')
                GROUP BY status
            ''') as cursor:
                stats['status_distribution'] = await cursor.fetchall()
            
            return stats