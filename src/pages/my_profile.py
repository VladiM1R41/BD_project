import streamlit as st
import pandas as pd
from datetime import datetime
import repositories.flights
import repositories.user
import asyncio
from settings import get_redis, REDIS_KEY_PREFIX

async def confirm_booking(pool, booking_id, booking_price):
    print(f"Подтверждение бронирования {booking_id}")
    success = await repositories.flights.confirm_booking(pool, booking_id)
    if success:
        payment_method = "Кредитная карта"  
        payment_date = datetime.now()
        payment_success = await repositories.flights.add_payment(pool, booking_id, booking_price,payment_date, payment_method)
        if payment_success:
            print(f"Платеж для бронирования {booking_id} успешно добавлен.")
        else:
            print(f"Не удалось добавить платеж для бронирования {booking_id}.")
    return success

async def get_user_data(pool, user_id):
    user_data = await repositories.user.get_user(pool, user_id)
    return user_data

async def update_username(pool, user_id, new_username):
    success = await repositories.user.change_user_username(pool, user_id, new_username)
    return success

async def update_login(pool, user_id, new_login):
    success = await repositories.user.change_user_login(pool, user_id, new_login)
    return success


async def show_my_bookings_page(pool, user_id):
    st.title("Мои забронированные билеты")
    
    bookings = await repositories.flights.get_user_bookings(pool, user_id)
    
    if bookings:
        df = pd.DataFrame(bookings)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="Скачать мои забронированные билеты в формате CSV",
            data=csv,
            file_name='my_bookings.csv',
            mime='text/csv',
        )
        
        for booking in bookings:
            st.markdown("---") 
            st.header(f"Рейс: {booking['flight_id']} - {booking['airline_name']}")
            
            st.write(f"**Уникальный номер брони:** {booking['booking_id']}")
            st.write(f"**Дата вылета:** {booking['departure_time']}     |     **Дата прибытия:** {booking['arrival_time']}")
            st.write(f"**Аэропорт отправления:** {booking['departure_airport_name']} | **Аэропорт прибытия:** {booking['arrival_airport_name']}")
            st.write(f"**Цена:** {booking['price']} руб.")
            
            if booking['status'] == "Подтверждено":
                st.text(f"Бронирование {booking['booking_id']} уже подтверждено.")
            else:
                if st.button(f"Подтвердить бронирование {booking['booking_id']}"):
                    success = await confirm_booking(pool, booking['booking_id'], booking['price'])
                    
                    if success:
                        st.success(f"Бронирование {booking['booking_id']} подтверждено.")
                    else:
                        st.error(f"Не удалось подтвердить бронирование {booking['booking_id']}.")
        st.markdown("---") 
    else:
        st.write("У вас нет забронированных билетов.")


    st.title("Профиль")
    

    user_data = await get_user_data(pool, user_id)
    
    if user_data:
        user_info = user_data[0]
        st.write(f"**Пользователь:** {user_info['username']}")
        st.write(f"**Логин:** {user_info['login']}")
        st.write(f"**Роль:** {user_info['role']}")

        st.subheader("Изменить данные пользователя")
        
        new_username = st.text_input("Новое имя пользователя", value=user_info['username'])
        if st.button("Изменить имя пользователя"):
            if new_username != user_info['username']:
                success = await update_username(pool, user_id, new_username)
                if success:
                    st.success("Имя пользователя успешно обновлено.")
                else:
                    st.error("Ошибка: имя пользователя уже используется.")
            else:
                st.warning("Введите новое имя пользователя.")

        new_login = st.text_input("Новый логин", value=user_info['login'])
        if st.button("Изменить логин"):
            if new_login != user_info['login']:
                success = await update_login(pool, user_id, new_login)
                if success:
                    st.success("Логин успешно обновлен.")
                else:
                    st.error("Ошибка: логин уже используется.")
            else:
                st.warning("Введите новый логин.")

    else:
        st.write("Не удалось получить данные пользователя.")

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
