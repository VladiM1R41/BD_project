import streamlit as st
from datetime import datetime
import repositories.flights
import pandas as pd
import logging
import asyncio
from services.book import BookingService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if "booked_flights" not in st.session_state:
    st.session_state.booked_flights = pd.DataFrame(columns=["Рейс", "пользователь"])

async def get_cities(pool) -> list[str]:
    try:
        print("Получение городов")
        cities = await repositories.flights.get_cities(pool)
        
        # Дополнительная проверка результата
        if not cities:
            st.warning("Не удалось получить список городов. Проверьте подключение к базе данных.")
            return []
        
        return [city["city"] for city in cities]
    except Exception as e:
        logger.error(f"Ошибка при получении городов: {e}")
        st.error("Произошла ошибка при загрузке списка городов.")
        return []

async def get_airports(pool, city: str) -> list[str]:
    try:
        print(f"Получение аэропортов для города: {city}")
        airports = await repositories.flights.get_airports(pool, city)
        
        # Дополнительная проверка результата
        if not airports:
            st.warning(f"Не удалось получить аэропорты для города {city}.")
            return []
        
        return [airport["name"] for airport in airports]
    except Exception as e:
        logger.error(f"Ошибка при получении аэропортов для города {city}: {e}")
        st.error(f"Произошла ошибка при загрузке аэропортов для города {city}.")
        return []


async def search_flights(pool, departure_airport: str, arrival_airport: str, departure_date: datetime.date) -> list[dict]:
    try:
        print(f"Поиск рейсов из {departure_airport} в {arrival_airport} на {departure_date}")
        
        # Проверка, что города и аэропорты не совпадают
        if departure_airport == arrival_airport:
            st.warning("Аэропорт вылета и прилета не могут совпадать!")
            return []
        
        flights = await repositories.flights.search_flights(pool, departure_airport, arrival_airport, departure_date)
        
        return flights
    except Exception as e:
        logger.error(f"Ошибка при поиске рейсов: {e}")
        st.error("Произошла ошибка при поиске рейсов. Попробуйте позже.")
        return []

def clear_table_event():
    st.session_state.booked_flights = pd.DataFrame(
        columns=["Рейс", "Пользователь"]
    )


def book_flight(flight_id, user_id):
    new_row = pd.DataFrame(
        {
            "Рейс": [flight_id],
            "Пользователь": [user_id]
        }
    )
    st.session_state.booked_flights = pd.concat(
        [st.session_state.booked_flights, new_row], ignore_index=True
    )

async def upload_sales(booked_flights: pd.DataFrame, pool):
    booking_date = datetime.now()
    await BookingService().process_sale(
        booking_date,
        booked_flights,
        pool,
    )




async def show_flight_search_and_booking_page(pool, user_id):
    cities = await get_cities(pool)
    st.title("Поиск и бронирование рейсов")

    # Выбор города вылета
    departure_city = st.selectbox("Выберите город вылета", cities, key="departure_city")
    departure_airports = await get_airports(pool, departure_city)
    departure_airport = st.selectbox("Выберите аэропорт вылета", departure_airports, key="departure_airport")

    # Выбор города назначения
    arrival_cities = [city for city in cities if city != departure_city]
    arrival_city = st.selectbox("Выберите город назначения", arrival_cities, key="arrival_city")
    arrival_airports = await get_airports(pool, arrival_city)
    arrival_airport = st.selectbox("Выберите аэропорт назначения", arrival_airports, key="arrival_airport")

    # Выбор даты вылета
    departure_date = st.date_input("Выберите дату вылета", key="departure_date")
    flights = await search_flights(pool, departure_airport, arrival_airport, departure_date)
    # Кнопка для поиска рейсов
    if st.button("Поиск рейсов"):
        if flights:
            st.write("Найденные рейсы:")
            st.subheader(f"Найдено рейсов: {len(flights)}")
            
            for flight in flights:
                container = st.container(border=True)
                container.markdown(f"### Рейс {flight['flight_id']} | {flight['airline_name']}")
                
                col1, col2, col3 = container.columns(3)
                
                with col1:
                    st.markdown("**Вылет:**")
                    st.markdown(f"🏢 {flight['departure_airport_name']}")
                    st.markdown(f"🕒 {pd.to_datetime(flight['departure_time']).strftime('%H:%M %d.%m.%Y')}")
                
                with col2:
                    st.markdown("**Прилёт:**")
                    st.markdown(f"🏢 {flight['arrival_airport_name']}")
                    st.markdown(f"🕒 {pd.to_datetime(flight['arrival_time']).strftime('%H:%M %d.%m.%Y')}")
                
                with col3:
                    st.markdown(f"💰 Цена: {flight['price']} руб.")
                    st.markdown(f"✈️ Свободные места: {flight['number_seats']}")
        else:
            st.write("Рейсы не найдены.")

    flight_ids = [flight['flight_id'] for flight in flights]
    selected_flight= st.selectbox("Выберите рейс", flight_ids)
    add_flight_btn = st.button("Добавить рейс в корзину")

    clear_table_btn = st.button("Очистить корзину")
    apply_btn = st.button("Забронировать билеты")
    if add_flight_btn:
        book_flight(selected_flight, user_id)
    if clear_table_btn:
        clear_table_event()
    if apply_btn and not st.session_state.booked_flights.empty:
        await upload_sales(st.session_state.booked_flights, pool)
        #repositories.flights.decrement_seat_count(selected_flight)
        st.success("Подтвердите бронь на странице 'Мой профиль'")
        clear_table_event()

    st.write("Корзина:")
    st.dataframe(st.session_state.booked_flights)

    if st.button("Выход"):
        # Сбрасываем состояние сессии и возвращаем на страницу входа
        st.session_state['user'] = None
        st.session_state['page'] = 'login'
        st.rerun()
