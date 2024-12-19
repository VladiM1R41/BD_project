from datetime import datetime

from repositories.flights import add_booking
from pandas import DataFrame
import time


class BookingService:
    async def process_sale(self, sale_date: datetime, items: DataFrame, pool) -> int:
        # time.sleep(10)
        items = items.rename(columns={"Рейс": "flight_id", "Пользователь": "user_id"})
        items["booking_time"] = sale_date
        await add_booking(pool, items)
