import streamlit as st
import pandas as pd
import logging
import repositories.flights
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def get_airlines(pool) -> list[dict]:
    
    try:
        logger.info("Получение авиакомпаний")
        airlines = await repositories.flights.get_airlines(pool)
        
        airlines = [dict(airline) for airline in airlines]
        if not airlines:
            st.warning("Не удалось получить список авиакомпаний.")
            return []
        
        return airlines
    except Exception as e:
        logger.error(f"Ошибка при получении авиакомпаний: {e}")
        st.error("Произошла ошибка при загрузке списка авиакомпаний.")
        return []
    
async def add_review(pool, user_id, airline_id, rating, comment):
    try:
        await repositories.flights.add_review(pool, user_id, airline_id, rating, comment)
    except Exception as e:
        logger.error(f"Ошибка при добавлении отзыва: {e}")
        st.error("Произошла ошибка при добавлении отзыва.")
        return False

async def get_reviews(pool, airline_id) -> list[dict]:
    try:
        logger.info("Получение отзывов")
        reviews = await repositories.flights.get_reviews(pool, airline_id)
        
        
        return [dict(review) for review in reviews]
    except Exception as e:
        logger.error(f"Ошибка при получении отзывов: {e}")
        st.error("Произошла ошибка при загрузке списка отзывов.")
        return []
    
    

async def show_airline_reviews_page(pool, user_id):
    st.title("Отзывы об авиакомпаниях")

    airlines =  await get_airlines(pool)

    if not airlines:
        st.write("Нет доступных авиакомпаний.")
        return

    airlines_df = pd.DataFrame(airlines)
    
    st.subheader("Список авиакомпаний")
    st.dataframe(airlines_df[['name', 'code', 'country']], use_container_width=True)

    st.subheader("Подробная информация об авиакомпаниях")
    for index, airline in airlines_df.iterrows():
        with st.expander(airline['name'], expanded=False):
            st.write(f"**Код авиакомпании:** {airline['code']}")
            st.write(f"**Страна:** {airline['country']}")
            
            review = st.text_area(f"Оставьте отзыв об авиакомпании {airline['name']}", key=f"review_{index}")
            rating = st.slider(f"Выберите рейтинг для {airline['name']}", 1, 5, 1, key=f"rating_{index}")
            if st.button("Отправить отзыв", key=f"submit_{index}"):
                if review:
                    await add_review(pool, user_id, airline['airline_id'], rating, review)
                    st.success("Ваш отзыв успешно отправлен!")
                else:
                    st.warning("Пожалуйста, напишите отзыв перед отправкой.")
            st.subheader("Отзывы пользователей")
            reviews = await get_reviews(pool, airline['airline_id'])
            if reviews:
                for review in reviews:
                    st.write(f"**Пользователь:** {review['username']}")
                    st.write(f"**Рейтинг:** {review['rating']}")
                    st.write(f"**Отзыв:** {review['comment']}")
                    st.write("---")
            else:
                st.write("Нет отзывов для отображения.")
    if st.button("Выход"):
        st.session_state['user'] = None
        st.session_state['page'] = 'login'
        st.rerun()

