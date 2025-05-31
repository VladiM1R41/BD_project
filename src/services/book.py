from datetime import datetime
from settings import get_redis, REDIS_KEY_PREFIX
from repositories.flights import add_booking
from pandas import DataFrame
import time
import json


class BookingService:
    async def process_sale(self, sale_date: datetime, items: DataFrame, pool) -> int:
        redis_client = get_redis()
        # time.sleep(10)
        items = items.rename(columns={"Рейс": "flight_id", "Пользователь": "user_id"})
        items["booking_time"] = sale_date
        await add_booking(pool, items)

        for _, row in items.iterrows():
            redis_client.publish(
                f"{REDIS_KEY_PREFIX}bookings",
                json.dumps({
                    "event": "new_booking",
                    "flight_id": int(row['flight_id']),
                    "user_id": int(row['user_id']),
                    "timestamp": datetime.now().isoformat()
                }) 
            )