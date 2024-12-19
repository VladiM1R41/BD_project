-- Таблица для хранения информации о пользователях
CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    login VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL
);
COMMENT ON TABLE Users IS 'Информация о пользователях системы';
COMMENT ON COLUMN Users.user_id IS 'Уникальный идентификатор пользователя';
COMMENT ON COLUMN Users.username IS 'Имя пользователя';
COMMENT ON COLUMN Users.login IS 'Логин почта пользователя';
COMMENT ON COLUMN Users.password_hash IS 'Хэш пароля пользователя';
COMMENT ON COLUMN Users.role IS 'Роль пользователя (например, пользователь или администратор)';

-- Таблица для хранения информации об авиакомпаниях
CREATE TABLE Airlines (
    airline_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(3) NOT NULL,
    country VARCHAR(50) NOT NULL
);
COMMENT ON TABLE Airlines IS 'Информация об авиакомпаниях';
COMMENT ON COLUMN Airlines.airline_id IS 'Уникальный идентификатор авиакомпании';
COMMENT ON COLUMN Airlines.name IS 'Название авиакомпании';
COMMENT ON COLUMN Airlines.code IS 'Код авиакомпании';
COMMENT ON COLUMN Airlines.country IS 'Страна авиакомпании';

-- Таблица для хранения информации об аэропортах
CREATE TABLE Airports (
    airport_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);
COMMENT ON TABLE Airports IS 'Информация об аэропортах';
COMMENT ON COLUMN Airports.airport_id IS 'Уникальный идентификатор аэропорта';
COMMENT ON COLUMN Airports.name IS 'Название аэропорта';
COMMENT ON COLUMN Airports.city IS 'Город, в котором расположен аэропорт';
COMMENT ON COLUMN Airports.country IS 'Страна, в которой расположен аэропорт';

-- Таблица для хранения информации о рейсах
CREATE TABLE Flights (
    flight_id SERIAL PRIMARY KEY,
    airline_id INT REFERENCES Airlines(airline_id),
    departure_airport_id INT REFERENCES Airports(airport_id),
    arrival_airport_id INT REFERENCES Airports(airport_id),
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    number_seats INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);
COMMENT ON TABLE Flights IS 'Информация о рейсах';
COMMENT ON COLUMN Flights.flight_id IS 'Уникальный идентификатор рейса';
COMMENT ON COLUMN Flights.airline_id IS 'Идентификатор авиакомпании, выполняющей рейс';
COMMENT ON COLUMN Flights.departure_airport_id IS 'Аэропорт отправления';
COMMENT ON COLUMN Flights.arrival_airport_id IS 'Аэропорт назначения';
COMMENT ON COLUMN Flights.departure_time IS 'Время отправления рейса'
COMMENT ON COLUMN Flights.arrival_time IS 'Время прибытия рейса';
COMMENT ON COLUMN Flights.number_seats IS 'Кол-во мест';
COMMENT ON COLUMN Flights.price IS 'Цена билета на рейс';

-- Таблица для хранения информации о бронированиях
CREATE TABLE Bookings (
    booking_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    flight_id INT REFERENCES Flights(flight_id),
    booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(100) NOT NULL
);
COMMENT ON TABLE Bookings IS 'Информация о бронированиях рейсов';
COMMENT ON COLUMN Bookings.booking_id IS 'Уникальный идентификатор бронирования';
COMMENT ON COLUMN Bookings.user_id IS 'Идентификатор пользователя, который сделал бронирование';
COMMENT ON COLUMN Bookings.flight_id IS 'Идентификатор рейса, который был забронирован';
COMMENT ON COLUMN Bookings.booking_time IS 'Время, когда было сделано бронирование';
COMMENT ON COLUMN Bookings.status IS 'Статус бронирования (например, подтверждено, ожидает)';

-- Таблица для хранения отзывов о рейсах
CREATE TABLE Reviews (
    review_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES Users(user_id),
    airline_id INT REFERENCES Airlines(airline_id),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT
);
COMMENT ON TABLE Reviews IS 'Отзывы пользователей о авиакомпаниях';
COMMENT ON COLUMN Reviews.review_id IS 'Уникальный идентификатор отзыва';
COMMENT ON COLUMN Reviews.user_id IS 'Идентификатор пользователя, оставившего отзыв';
COMMENT ON COLUMN Reviews.airline_id IS 'Идентификатор авикомпании, на который оставлен отзыв';
COMMENT ON COLUMN Reviews.rating IS 'Оценка авиакомпании (от 1 до 5)';
COMMENT ON COLUMN Reviews.comment IS 'Комментарий пользователя к отзыву';

-- Таблица для хранения информации о платежах
CREATE TABLE Payments (
    payment_id SERIAL PRIMARY KEY,
    booking_id INT REFERENCES Bookings(booking_id),
    amount DECIMAL(10, 2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_method VARCHAR(50) NOT NULL
);
COMMENT ON TABLE Payments IS 'Информация о платежах за бронирования';
COMMENT ON COLUMN Payments.payment_id IS 'Уникальный идентификатор платежа';
COMMENT ON COLUMN Payments.booking_id IS 'Идентификатор бронирования, за которое был произведен платеж';
COMMENT ON COLUMN Payments.amount IS 'Сумма платежа';
COMMENT ON COLUMN Payments.payment_date IS 'Дата и время, когда был произведен платеж';
COMMENT ON COLUMN Payments.payment_method IS 'Способ оплаты (например, кредитная карта, PayPal)';


CREATE VIEW flight_details AS
SELECT 
    f.flight_id,
    a.name AS airline_name,
    dep.name AS departure_airport_name,
    arr.name AS arrival_airport_name,
    f.departure_time,
    f.arrival_time,
    f.price,
    f.number_seats
FROM 
    Flights f
JOIN 
    Airlines a ON f.airline_id = a.airline_id
JOIN 
    Airports dep ON f.departure_airport_id = dep.airport_id
JOIN 
    Airports arr ON f.arrival_airport_id = arr.airport_id;


CREATE OR REPLACE FUNCTION decrement_seat_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Уменьшаем количество мест на 1 для рейса, на который делается бронирование
    UPDATE Flights
    SET number_seats = number_seats - 1
    WHERE flight_id = NEW.flight_id AND number_seats > 0;

    -- Возвращаем новую запись
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER after_booking_insert
AFTER INSERT ON Bookings
FOR EACH ROW
EXECUTE FUNCTION decrement_seat_count();


CREATE OR REPLACE FUNCTION increment_seat_count()
RETURNS TRIGGER AS $$
BEGIN
    -- Увеличиваем количество мест на 1 для рейса, на который было удалено бронирование
    UPDATE Flights
    SET number_seats = number_seats + 1
    WHERE flight_id = OLD.flight_id;

    -- Возвращаем удалённую запись
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Триггер для удаления бронирования
CREATE TRIGGER after_booking_delete
AFTER DELETE ON Bookings
FOR EACH ROW
EXECUTE FUNCTION increment_seat_count();