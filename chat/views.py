from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
import time
import json
from rest_framework import status
from rest_framework.response import Response
from .serializers import ChatbotInputSerializer
from openai import OpenAI
import requests
from .models import Threads
from config.tasks import check_user_activity_periodic
from django_ratelimit.decorators import ratelimit
OPENAI_API_KEY = ''
client = OpenAI(api_key=OPENAI_API_KEY)


def send_post_request(url, data):
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        if response.status_code == 200:
            print("POST запрос успешно отправлен")
        else:
            print(f"Ошибка при отправке POST запроса. Код статуса: {response.status_code}")
    except Exception as e:
        print(f"Произошла ошибка при отправке POST запроса: {e}")


url = "https://eokpbzbviu045ql.m.pipedream.net"
data = {"key1": "Hello", "key2": "World"}


def send_message_and_run_assistant(thread, assistant, user_message):
    print(f'Adding user\'s message to the thread: \'{user_message}\'')
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role='user',
        content=user_message
    )

    print('Running th Assistant to process the message ..')
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    return run


def check_and_create_session(user_id):
    # Проверяем, существует ли активная сессия для данного пользователя
    existing_session = Threads.objects.filter(user_id=user_id, is_active_session=True).first()

    if not existing_session:
        # Если нет активной сессии, создаем новую запись
        thread = client.beta.threads.create()
        new_session = Threads(user_id=user_id, is_active_session=True, thread_id=thread.id)
        new_session.save()
        return f"Создана новая сессия для пользователя с ID: {user_id}"
    else:
        return f"У пользователя с ID {user_id} уже есть активная сессия"


def get_active_session_thread_id(user_id):
    # Проверяем, существует ли активная сессия для данного пользователя
    existing_session = Threads.objects.filter(user_id=user_id, is_active_session=True).first()

    if existing_session:
        # Если есть активная сессия, возвращаем thread_id этой сессии
        existing_session.last_activity_time = timezone.now()
        existing_session.save()
        return existing_session.thread_id
    else:
        raise Exception(f"Нет активной сессии для пользователя с ID: {user_id}")


class ChatbotView(APIView):
    # @ratelimit(key='ip', rate='1/m')
    # @method_decorator(csrf_exempt)
    # @method_decorator(ratelimit(key='ip', rate='1/m'))
    def post(self, request):
        serializer = ChatbotInputSerializer(data=request.data)
        print(request.data)
        if serializer.is_valid():

            custom_function_name = 'send_post_request'

            user_message = serializer.validated_data['user_input']
            user_id = serializer.validated_data['user_id']

            assistant_id = "asst_kUJ5bsDz2dlBsfl3ofKcCTCG"
            assistant = client.beta.assistants.retrieve(assistant_id)
            print(f"Assistant retrieved with ID{assistant_id}")

            # Проверяем, существует ли активная сессия для данного пользователя, если нет активной сессии,
            # то создаем новую сессию и новый thread
            check_and_create_session(user_id)

            # Получаем thread_id из базы данных thread_id, если есть активная сессия
            thread_id = get_active_session_thread_id(user_id)
            thread = client.beta.threads.retrieve(thread_id)
            print(f"Thread retrieved with ID: {thread.id}")

            run = send_message_and_run_assistant(thread, assistant, user_message)

            print(f'Run created with ID: {run.id}')

            while True:
                run = client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
                # print(run, '!!!!___')
                if run.status == 'completed':
                    print("Run completed. Retrieving the Assistant's response ")
                    break
                elif run.status == 'requires_action':
                    print('Run requires actions. Preparing to call the functions')
                    required_actions = run.required_action.submit_tool_outputs

                    tool_outputs = []

                    for action in required_actions.tool_calls:
                        function_name = action.function.name
                        arguments = json.loads(action.function.arguments)
                        if function_name == custom_function_name:
                            print(f'Calling custom function:'
                                  f'{function_name} with arguments {arguments}')
                            result = send_post_request(url, data)
                            tool_outputs.append({
                                "tool_call_id": action.id,
                                "output": "POST запрос успешно отправлен"
                            })
                    print("Submitting function call outputs back to the Assistant ..")
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                    print("Functions outputs submitted")
                elif run.status in ['failed', 'cancelled']:
                    print('Run did not complete successfully')
                    break
                else:
                    print('Waiting for Assistant to process ..')
                time.sleep(2)

            messages = client.beta.threads.messages.list(
                thread_id=thread.id,
            )
            for message in messages.data:
                if message.content[0].type == 'text':
                    text_value = message.content[0].text.value
                    break

            print('Displaying the conversation: ')
            for msg in messages.data:
                print(f'{msg.role.capitalize()}: {msg.content[0].text.value}')

            print(messages.data)

            response_data = {
                "message": user_message,
                "gpt_output": text_value,
                "user_id": user_id
            }
            print(response_data)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def test(request):
    return HttpResponse('Текст текст текст ля ял яля л')

# TODO
'''
1. Проверка активной сессии
2. Создание нового thread
3. Записать id thread'a в базу
4. Извлечь id_thread из базы данных по user_id
5. Завершить сессию по тайм-ауту, переписать поле is_active_session на False
6. 
'''

'''
    1. Если нет активной сессии создать новую сессию и новый thread
    2. Получить из БД thread_id из активной сессии
    
    1. Проверить время выполнения последнего запроса в сессии:
            если прошло 2 минуты отправить сообщение: "У вас будут дополнительные вопросы?"
                    если отвечает нет или не ответит в течение 1й минуты, то сессия завершается
                    если продолжает отвечать, то спрашиваем что его интересует      
'''
