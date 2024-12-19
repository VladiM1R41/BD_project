import asyncpg
import bcrypt

async def authenticate_user(pool, login: str, password: str):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM Users WHERE login = $1", login)

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return user 
    return None 

async def register_user(pool, name: str, login: str, password: str, role: str = 'user'):

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8') 
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                "INSERT INTO Users (username, login, password_hash, role) VALUES ($1, $2, $3, $4)",
                name, login, hashed_password, role
            )
            return True 
        except asyncpg.UniqueViolationError:
            return False
        except Exception as e:
            print(f"Ошибка: {e}")
            return False


async def get_all_users(pool):
    async with pool.acquire() as connection:
        try:
            users = await connection.fetch("SELECT user_id, username, login, role FROM Users")
            return users
        except Exception as e:
            print(f"Ошибка: {e}")
            return []

async def delete_user(pool, user_id: int):

    async with pool.acquire() as connection:
        try:

            result = await connection.fetchrow("SELECT * FROM Users WHERE user_id = $1", user_id)
            if result is None:
                return False
            user = await connection.fetchrow("SELECT role FROM Users WHERE user_id = $1", user_id)
            if user and user['role'] == 'admin':
                print("Нет прав удалить этого пользователя")
                return False
            
            await connection.execute("""
                DELETE FROM Payments 
                WHERE booking_id IN (
                    SELECT booking_id FROM Bookings WHERE user_id = $1
                )
            """, user_id)
            
            await connection.execute("DELETE FROM Bookings WHERE user_id = $1", user_id)
            await connection.execute("DELETE FROM Reviews WHERE user_id = $1", user_id)
            await connection.execute("DELETE FROM Users WHERE user_id = $1", user_id)
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False

async def get_user(pool, user_id: int):
    async with pool.acquire() as conn:
        try:
            users = await conn.fetch("SELECT user_id, username, login, role FROM Users WHERE user_id = $1", user_id)
            return users
        except Exception as e:
            print(f"Ошибка при получении пользователя: {e}")
            return []
        
async def change_user_role(pool, user_id: int, new_role: str):
    async with pool.acquire() as connection:
        try:
            
            result = await connection.fetchrow("SELECT * FROM Users WHERE user_id = $1", user_id)
            if result is None:
                return False

            await connection.execute("UPDATE Users SET role = $1 WHERE user_id = $2", new_role, user_id)
            return True 
        except Exception as e:
            print(f"Ошибка: {e}")
            return False 

async def change_user_username(pool, user_id: int, new_username: str):
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchrow("SELECT * FROM Users WHERE user_id = $1", user_id)
            if result is None:
                return False

            await conn.execute("UPDATE Users SET username = $1 WHERE user_id = $2", new_username, user_id)
            return True
        except asyncpg.UniqueViolationError:
            return False
        except Exception as e:
            print(f"Ошибка: {e}")
            return False

async def change_user_login(pool, user_id: int, new_login: str):
    async with pool.acquire() as conn:
        try:
            result = await conn.fetchrow("SELECT * FROM Users WHERE user_id = $1", user_id)
            if result is None:
                return False
            
            await conn.execute("UPDATE Users SET login = $1 WHERE user_id = $2", new_login, user_id)
            return True
        except asyncpg.UniqueViolationError:
            return False
        except Exception as e:
            print(f"Ошибка: {e}")
            return False

async def delete_review(pool, review_id: int):
    async with pool.acquire() as connection:
        try:
            result = await connection.fetchrow("SELECT * FROM Reviews WHERE review_id = $1", review_id)
            if result is None:
                return False

            await connection.execute("DELETE FROM Reviews WHERE review_id = $1", review_id)
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False