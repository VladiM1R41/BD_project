import streamlit as st
import asyncio
import asyncpg
from pages.flight_search_and_booking import show_flight_search_and_booking_page
from pages.my_profile import show_my_bookings_page
from pages.login import login_page
from pages.register import register_page
from pages.admin import admin_page_bookings,admin_page_flights,admin_page_users, admin_page_reviews
from pages.airline_reviews import show_airline_reviews_page
from settings import DB_CONFIG, POOL_MAX_CONN, POOL_MIN_CONN


async def create_connection_pool():
    connection_pool: asyncpg.Pool = await asyncpg.create_pool(
        **DB_CONFIG,
        min_size=POOL_MIN_CONN,
        max_size=POOL_MAX_CONN,
    )
    return connection_pool

async def close_connection_pool(connection_pool: asyncpg.Pool):
    await connection_pool.close()
    print("Connection pool closed.")


async def main():

    pool: asyncpg.Pool = await create_connection_pool()

    st.sidebar.title("Навигация")

    # Проверяем, существует ли пользователь в сессии
    if 'user' not in st.session_state or st.session_state['user'] is None:
        if 'page' not in st.session_state:
            st.session_state['page'] = 'login'
        if st.session_state['page'] == 'login':
            await login_page(pool)  # Если пользователь не авторизован, показываем страницу входа
        elif st.session_state['page'] == 'register':
            await register_page(pool)  # Если пользователь хочет зарегистрироваться
        return

    # Получаем роль пользователя, если он существует
    user = st.session_state['user']
    user_role = user.get('role', 'user') if user else 'user'
    user_id = user.get('id')  # Предполагается, что user_id хранится в сессиисв

    if user_role == 'admin':
        # Если пользователь администратор, показываем страницу администратора
        page = st.sidebar.radio(
            "Перейти к странице",
            ["Управление пользователями", "Управление рейсами", "Все брони", "Отзывы"],
        )
        if page == "Управление пользователями":
            await admin_page_users(pool)
        if page == "Управление рейсами":
            await admin_page_flights(pool)
        if page == "Все брони":
            await admin_page_bookings(pool)
        if page == "Отзывы":
            await admin_page_reviews(pool)
    else:
        # Для обычных пользователей
        page = st.sidebar.radio(
            "Перейти к странице",
            ["Поиск и бронирование рейсов", "Отзывы об авиакомпаниях", "Мой профиль"],
        )

        if page == "Поиск и бронирование рейсов":
            await show_flight_search_and_booking_page(pool, user_id)
        if page == "Мой профиль":
            await show_my_bookings_page(pool, user_id)
        if page == "Отзывы об авиакомпаниях":
            await show_airline_reviews_page(pool, user_id)

    await close_connection_pool(pool)

if __name__ == "__main__":
    asyncio.run(main())