# pages/register.py
import streamlit as st
import asyncio
import asyncpg
from repositories.user import register_user


async def register_page(pool):
    st.title("Регистрация")
    name = st.text_input("Имя")
    new_login = st.text_input("Новый логин")
    new_password = st.text_input("Новый пароль", type="password")


    if st.button("Зарегистрироваться"):
        if await register_user(pool, name, new_login, new_password):
            st.success("Регистрация успешна!")
            st.session_state['page'] = 'login'
            st.rerun()
        else:
            st.error("Ошибка регистрации. Возможно, логин уже занят.")
