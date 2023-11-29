import requests

from .celery import app
from datetime import timedelta
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     sender.add_periodic_task(
#         crontab(minute='*/2'),  # Запускать каждые 5 минут
#         check_user_activity_periodic.s(),
#     )


# def check_user_activity_task(user_id):
#     from chat.models import Threads
#     logger.info(f"Задача для пользователя с ID {user_id} выполнилась")
#     # Получаем активную сессию пользователя
#     existing_session = Threads.objects.filter(user_id=user_id, is_active_session=True).first()
#
#     if existing_session:
#         # Проверяем время последнего запроса и текущее время
#         last_activity_time = existing_session.last_activity_time
#         current_time = timezone.now()
#         # Если прошло более 2 минут с последнего запроса, закрываем сессию
#         if current_time - last_activity_time > timedelta(minutes=2):
#             existing_session.is_active_session = False
#             existing_session.save()
#             return f"Сессия пользователя с ID: {user_id} закрыта из-за отсутствия активности"
#         else:
#             return f"Сессия пользователя с ID: {user_id} продолжается"
#     else:
#         return f"Нет активной сессии для пользователя с ID: {user_id}"


def check_user_activity_task(user_id):
    from chat.models import Threads
    logger.info(f"Задача для пользователя с ID {user_id} выполнилась")
    # Получаем активную сессию пользователя
    existing_session = Threads.objects.filter(user_id=user_id, is_active_session=True).first()

    if existing_session:
        # Проверяем время последнего запроса и текущее время
        last_activity_time = existing_session.last_activity_time
        current_time = timezone.now()
        # Если прошло более 5 минут с последнего запроса, закрываем сессию
        if current_time - last_activity_time > timedelta(minutes=5):
            existing_session.is_active_session = False
            existing_session.save()
            return f"Сессия пользователя с ID: {user_id} закрыта из-за отсутствия активности"
        elif timedelta(minutes=3) < current_time - last_activity_time < timedelta(minutes=5):  # Если прошло больше 3 минут и меньше 5 минут
            # Отправляем POST-запрос на определенный URL с сообщением
            url = 'https://eokpbzbviu045ql.m.pipedream.net'
            message = "У вас будут дополнительные вопросы?"
            data = {'message': message}
            response = requests.post(url, data=data)
            if response.status_code == 200:
                return f"Отправлено уведомление пользователю с ID: {user_id} о дополнительных вопросах"
            else:
                return f"Не удалось отправить уведомление пользователю с ID: {user_id}"
        else:
            return f"Сессия пользователя с ID: {user_id} продолжается"
    else:
        return f"Нет активной сессии для пользователя с ID: {user_id}"


# Получает все user_id, у которых есть активная сессия и проверяет разницу времени с момента
# последнего выполнения запроса и если прошло больше n минут, то закрывает активную сессию
@app.task
def check_user_activity_periodic():
    from chat.models import Threads
    # Получаем список всех пользователей, для которых нужно проверить активность
    active_sessions = Threads.objects.filter(is_active_session=True)
    for session in active_sessions:
        user_id = session.user_id
        check_user_activity_task(user_id)


# TODO
'''
1. Доработать job, чтобы он проверял если прошло 4 минуты с момента последнего запроса отправлял 
письмо "У вас будут дополнительные вопросы?",

2. Сделать ограничения количества запросов в минуту по адресу устройства или по ip или по user_id.

'''
