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
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: str, display_name: str = None, is_admin: bool = False):
        """Add or update user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO users (user_id, username, display_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, display_name, is_admin))
            await db.commit()
    
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