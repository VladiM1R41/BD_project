import streamlit as st
import asyncio
from datetime import datetime
import secrets
from repositories.user import authenticate_user
from settings import get_redis, REDIS_KEY_PREFIX,TOKEN_TTL, SESSION_TTL

async def login_page(pool):
    st.title("Вход в систему")
    login = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")

    if st.button("Войти"):
        user = await authenticate_user(pool, login, password)
        if user:

            token = secrets.token_hex(16)
            redis_client = get_redis()

            redis_key = f"{REDIS_KEY_PREFIX}auth_token:{token}"
            redis_client.setex(
                name=redis_key,
                time=TOKEN_TTL,
                value=user['user_id']
            )
            session_data = {
                "user_id": str(user['user_id']),
                "role": user['role'],
                "login": user['login'],
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
            session_key = f"{REDIS_KEY_PREFIX}session:{token}"
            redis_client.hset(
                name=session_key,
                mapping=session_data
            )
            redis_client.expire(session_key, SESSION_TTL)

            st.session_state.update({
                "auth_token": token,
                "user": {
                    "id": user['user_id'],
                    "role": user['role'],
                    "username": user['username']
                }
            })
            st.success("Успешная авторизация!")
            st.rerun() 
        else:
            st.error("Неверный логин или пароль.")

    if st.button("Зарегистрироваться"):
        st.session_state['page'] = 'register'
        st.rerun()