import streamlit as st
import threading
from datetime import datetime
import asyncio
import json
import pandas as pd
import repositories.flights
import repositories.user
from settings import get_redis, REDIS_KEY_PREFIX

async def fetch_users(pool):
    return await repositories.user.get_all_users(pool)

async def fetch_flights(pool):
    return await repositories.flights.get_all_flights(pool)

async def fetch_bookings(pool):
    return await repositories.flights.get_all_bookings(pool)

async def fetch_payments(pool):
    return await repositories.flights.get_all_payments(pool)

async def fetch_reviews(pool):
    return await repositories.flights.get_all_reviews(pool)


def listen_bookings():
    redis_client = get_redis()
    pubsub = redis_client.pubsub()
    pubsub.subscribe(f"{REDIS_KEY_PREFIX}bookings")  # Подписываемся на канал
    
    while True:
        message = pubsub.get_message()  # Получаем сообщение
        if message and message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                # Сохраняем событие в session_state
                st.session_state.last_booking_event = data
                st.experimental_rerun()  # Триггерим обновление страницы
            except Exception as e:
                print(f"Ошибка обработки сообщения: {e}")

# Запускаем поток при первом открытии админки
if "pubsub_thread" not in st.session_state:
    thread = threading.Thread(target=listen_bookings, daemon=True)
    thread.start()
    st.session_state.pubsub_thread = thread

async def admin_page_users(pool):
    st.title("Административная панель")

    if 'users' not in st.session_state:
        st.session_state.users = await fetch_users(pool)

    st.subheader("Управление пользователями")
    
    with st.expander("Показать пользователей"):
        if st.session_state.users:
            users_df = pd.DataFrame(st.session_state.users)
            users_df.columns = ["ID", "Имя", "Логин", "Роль"]
            st.dataframe(users_df) 
        else:
            st.write("Нет пользователей для отображения.")

        with st.form(key='change_role_form'):
            user_id = st.text_input("Введите ID пользователя для изменения роли", "")
            new_role = st.selectbox("Выберите новую роль", options=["admin", "user"])
            
            submit_role_button = st.form_submit_button("Изменить роль")

            if submit_role_button:
                if user_id.isdigit():
                    success = await repositories.user.change_user_role(pool, int(user_id), new_role)
                    if success:
                        st.success("Роль пользователя изменена успешно!")
                        st.session_state.users = await fetch_users(pool)
                    else:
                        st.error("Ошибка при изменении роли пользователя.")
                else:
                    st.error("Ошибка: ID пользователя должен быть целым числом.")

        with st.form(key='delete_user_form'):
            user_id_to_delete = st.text_input("Введите ID пользователя для удаления", "")
            
            submit_delete_button = st.form_submit_button("Удалить пользователя")

            if submit_delete_button:
                if user_id_to_delete.isdigit():
                    success = await repositories.user.delete_user(pool, int(user_id_to_delete))
                    if success:
                        st.success("Пользователь удалён успешно!")
                        st.session_state.users = await fetch_users(pool)
                    else:
                        st.error("Ошибка при удалении пользователя.")
                else:
                    st.error("Ошибка: ID пользователя должен быть целым числом.")


    if st.button("Выход"):
        st.session_state['user'] = None
        st.session_state['page'] = 'login'
        st.rerun()

async def admin_page_flights(pool):

    if 'flights' not in st.session_state:
        st.session_state.flights = await fetch_flights(pool)

    st.title("Административная панель")
    st.subheader("Управление рейсами")
    
    with st.expander("Показать рейсы"):
        if st.session_state.flights:
            flights_df = pd.DataFrame(st.session_state.flights)
            flights_df.columns = ["ID", "id авиакомпании", "id аэропорта вылета", "id аэропорта прилета", "Время вылета", "Время прилета ", "Количество мест", "Цена"]
            st.dataframe(flights_df, width=1500, height=400) 
        else:
            st.write("Нет рейсов для отображения.")

        with st.form(key='add_flight_form'):
            airline_id = st.text_input("ID авиакомпании")
            departure_airport_id = st.text_input("ID аэропорта вылета")
            arrival_airport_id = st.text_input("ID аэропорта прилета")
            departure_time = st.text_input("Время вылета (YYYY-MM-DD HH:MM:SS)")
            arrival_time = st.text_input("Время прилета (YYYY-MM-DD HH:MM:SS)")
            number_seats = st.number_input("Количество мест", min_value=1)
            price = st.number_input("Цена", min_value=0.0)

            submit_flight_button = st.form_submit_button("Сохранить рейс")

            if submit_flight_button:
                try:
                    airline_id = int(airline_id)
                    departure_airport_id = int(departure_airport_id)
                    arrival_airport_id = int(arrival_airport_id)
                    departure_time = datetime.strptime(departure_time, '%Y-%m-%d %H:%M:%S')
                    arrival_time = datetime.strptime(arrival_time, '%Y-%m-%d %H:%M:%S')

                    success = await repositories.flights.add_flight(pool,
                        airline_id, departure_airport_id, arrival_airport_id,
                        departure_time, arrival_time, number_seats, price
                    )

                    if success:
                        st.success("Рейс добавлен успешно!")
                        st.session_state.flights = await fetch_flights(pool)
                    else:
                        st.error("Ошибка при добавлении рейса.")
                except ValueError:
                    st.error("Ошибка: убедитесь, что все ID введены корректно и являются целыми числами.")


    if st.button("Выход"):
        st.session_state['user'] = None
        st.session_state['page'] = 'login'
        st.rerun()
async def admin_page_bookings(pool):
    st.title("Административная панель")

    if 'last_booking_event' in st.session_state:
        event = st.session_state.last_booking_event
        st.toast(f"Новое бронирование! Рейс #{event['flight_id']}", icon="✈️")
        del st.session_state.last_booking_event

    if 'bookings' not in st.session_state:
        st.session_state.bookings = await fetch_bookings(pool)

    st.subheader("Брони")

    with st.expander("Показать бронирования"):
        if st.session_state.bookings:
            bookings_df = pd.DataFrame(st.session_state.bookings)
            bookings_df.columns = ["ID", "id пользователя", "Номер рейса", "Время бронирования","Статус"]
            st.dataframe(bookings_df)
        else:
            st.write("Нет бронирований для отображения.")
    
    st.subheader("Платежи")

    if 'payments' not in st.session_state:
        st.session_state.payments = await fetch_payments(pool)

    with st.expander("Показать платежи"):
        if st.session_state.payments:
            bookings_df = pd.DataFrame(st.session_state.payments)
            bookings_df.columns = ["ID", "id брони", "Сумма", "Время бронирования","Способ оплаты"]
            st.dataframe(bookings_df)
        else:
            st.write("Нет платежей для отображения.")
    if st.button("Выход"):
        st.session_state['user'] = None
        st.session_state['page'] = 'login'
        st.rerun()

async def admin_page_reviews(pool):
    st.title("Административная панель")

    if 'reviews' not in st.session_state:
        st.session_state.reviews = await fetch_reviews(pool)

    st.subheader("Отзывы")

    with st.expander("Показать отзывы"):
        if st.session_state.reviews:
            reviews_df = pd.DataFrame(st.session_state.reviews)
            reviews_df.columns = ["ID", "id пользователя", "id авиакомпании", "Рейтинг","Комментарий"]
            st.dataframe(reviews_df)
        else:
            st.write("Нет отзывов для отображения.")

        with st.form(key='delete_review_form'):
            review_id_to_delete = st.text_input("Введите ID отзыва для удаления", "")
            
            submit_delete_button = st.form_submit_button("Удалить отзыв")

            if submit_delete_button:
                if review_id_to_delete.isdigit():
                    success = await repositories.user.delete_review(pool, int(review_id_to_delete))
                    if success:
                        st.success("Отзыв удалён успешно!")
                        st.session_state.users = await fetch_reviews(pool)
                    else:
                        st.error("Ошибка при удалении отзыва.")
                else:
                    st.error("Ошибка: ID отзыва должен быть целым числом.")
    if st.button("Выход"):
        auth_token = st.session_state.get("auth_token")
        if auth_token:
            redis_client = get_redis()
        
            redis_client.delete(
                f"{REDIS_KEY_PREFIX}auth_token:{auth_token}",
                f"{REDIS_KEY_PREFIX}session:{auth_token}"
            )
    
        st.session_state.clear()
        st.session_state['user'] = None
        st.session_state['page'] = 'login'
        st.rerun()
