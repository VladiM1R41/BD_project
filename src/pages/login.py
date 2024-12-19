import streamlit as st
import asyncio
from repositories.user import authenticate_user

async def login_page(pool):
    st.title("Вход в систему")
    login = st.text_input("Логин")
    password = st.text_input("Пароль", type="password")

    if st.button("Войти"):
        user = await authenticate_user(pool, login, password)
        if user:
            st.session_state['user'] = {
                'id': user['user_id'],  
                'role': user['role'],
            }
            st.success("Успешная авторизация!")
            st.rerun() 
        else:
            st.error("Неверный логин или пароль.")

    if st.button("Зарегистрироваться"):
        st.session_state['page'] = 'register'
        st.rerun()