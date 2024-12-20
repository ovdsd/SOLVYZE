# neon_connect.py
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def get_db_connection():
    connection_string = os.getenv('DATABASE_URL')
    pool = await asyncpg.create_pool(connection_string)
    return pool

async def store_account(username, encrypted_password):
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (username, password) VALUES ($1, $2)",
            username, encrypted_password
        )

async def store_conversation(username, user_msg, ai_response):
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO conversations (username, user_message, ai_response) VALUES ($1, $2, $3)",
            username, user_msg, ai_response
        )
