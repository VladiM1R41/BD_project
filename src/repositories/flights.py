import psycopg2
import psycopg2.extras
import asyncpg
from datetime import datetime
from pandas import DataFrame



async def get_cities(pool) -> list[dict]:
    print("Получение городов")
    query = "SELECT DISTINCT city FROM Airports ORDER BY city;"
    async with pool.acquire() as conn:
        return await conn.fetch(query)
        
async def get_airports(pool, city: str) -> list[dict]:
    print(f"Получение аэропортов для города: {city}")
    query = "SELECT name FROM Airports WHERE city = $1 ORDER BY name;"
    async with pool.acquire() as conn:
        return await conn.fetch(query, city)
        

async def search_flights(pool, departure_airport: str, arrival_airport: str, departure_date: str) -> list[dict]:
    print(f"Поиск рейсов из аэропорта {departure_airport} в аэропорт {arrival_airport} на {departure_date}")
    query = """
    SELECT 
            flight_id,
            airline_name,
            departure_airport_name,
            arrival_airport_name,
            departure_time,
            arrival_time,
            price,
            number_seats
        FROM 
            flight_details
        WHERE 
            departure_airport_name = $1
            AND arrival_airport_name = $2
            AND DATE(departure_time) = $3
        ORDER BY 
            departure_time;
    """
    
    async with pool.acquire() as conn:
        return await conn.fetch(query, departure_airport, arrival_airport, departure_date)
        
        
async def add_booking(pool, sales: DataFrame) -> None:
    query = "CALL create_booking($1, $2, $3);"
    async with pool.acquire() as conn:
        for _, row in sales.iterrows():
            await conn.execute(query, row['flight_id'], row['user_id'], row['booking_time'])

async def create_booking(pool, flight_id: int, user_id: int, booking_date: datetime) -> None:
    #booking_time_dt = datetime.strptime(booking_time, "%Y-%m-%d %H:%M:%S")
    query = "CALL create_booking($1, $2, $3, 'ожидает подтверждения');"
    async with pool.acquire() as conn:
        await conn.execute(query, flight_id, user_id, booking_date)

async def get_user_bookings(pool, user_id):
    query = """
    SELECT b.booking_id, f.flight_id, f.departure_time, f.arrival_time, f.price, b.status,
           a.name AS airline_name,
           dep_airport.name AS departure_airport_name,
           arr_airport.name AS arrival_airport_name
    FROM Bookings b
    JOIN Flights f ON b.flight_id = f.flight_id
    JOIN Airlines a ON f.airline_id = a.airline_id
    JOIN Airports dep_airport ON f.departure_airport_id = dep_airport.airport_id
    JOIN Airports arr_airport ON f.arrival_airport_id = arr_airport.airport_id
    WHERE b.user_id = $1;
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, user_id)
        
async def confirm_booking(pool,booking_id: int) -> bool:
    query = """
    UPDATE Bookings
    SET status = 'Подтверждено'
    WHERE booking_id = $1;
    """
    async with pool.acquire() as conn:
        result = await conn.execute(query, booking_id)
        return result == 'UPDATE 1' 
    
async def add_payment(pool, booking_id: int, amount: float,payment_date, payment_method: str) -> bool:
    query = """
    INSERT INTO Payments (booking_id, amount, payment_date, payment_method)
    VALUES ($1, $2, $3, $4);
    """
    async with pool.acquire() as conn:
        try:
            result = await conn.execute(query, booking_id, amount, payment_date, payment_method)
            return result is not None 
        except Exception as e:
            print(f"Ошибка при добавлении платежа: {e}")
            return False

async def get_all_flights(pool):
    async with pool.acquire() as conn:
        try:
            flights = await conn.fetch("SELECT * FROM Flights")
            return flights
        except Exception as e:
            print(f"Ошибка при получении рейсов: {e}")
            return []

async def add_flight(pool, airline_id, departure_airport_id, arrival_airport_id, departure_time, arrival_time, number_seats, price):
    async with pool.acquire() as conn:
        try:
            max_flight_id_row = await conn.fetch("SELECT COALESCE(MAX(flight_id), 0) AS max_flight_id FROM Flights")
            max_flight_id = max_flight_id_row[0]['max_flight_id'] + 1

            await conn.execute("""
                INSERT INTO Flights (flight_id, airline_id, departure_airport_id, arrival_airport_id, 
                                     departure_time, arrival_time, number_seats, price)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8);
            """, max_flight_id, airline_id, departure_airport_id, arrival_airport_id, 
            departure_time, arrival_time, number_seats, price)
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False


async def get_all_bookings(pool):
    async with pool.acquire() as conn:
        try:
            bookings = await conn.fetch("SELECT * FROM Bookings")
            return bookings
        except Exception as e:
            print(f"Ошибка при получении бронирований: {e}")
            return []

async def get_all_payments(pool):
    async with pool.acquire() as conn:
        try:
            payments = await conn.fetch("SELECT * FROM Payments")
            return payments
        except Exception as e:
            print(f"Ошибка при получении платежей: {e}")
            return []

async def add_review(pool, user_id, airline_id, rating, comment):
    async with pool.acquire() as conn:
        try:
            await conn.execute("""
                INSERT INTO Reviews (user_id, airline_id, rating, comment)
                VALUES ($1, $2, $3, $4);
            """, user_id, airline_id, rating, comment)
            return True
        except Exception as e:
            print(f"Ошибка: {e}")
            return False

async def get_airlines(pool) -> list[dict]:
    print("Получение авиакомпаний")
    query = "SELECT * FROM Airlines ORDER BY name;"
    async with pool.acquire() as conn:
        return await conn.fetch(query)

async def get_reviews(pool, airline_id) -> list[dict]:
    query = """
    SELECT r.rating, r.comment, u.username
    FROM Reviews r
    JOIN Users u ON r.user_id = u.user_id
    WHERE r.airline_id = $1
    ORDER BY r.review_id DESC;
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query, airline_id)
    
async def get_all_reviews(pool):
    async with pool.acquire() as conn:
        reviews = await conn.fetch("SELECT * FROM Reviews")
        return reviews