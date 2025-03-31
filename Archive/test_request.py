import requests
import json

# URL API
url = "http://127.0.0.1:8000/your-endpoint"

# Данные для отправки в формате JSON
data = {
    "key1": "value1",
    "key2": "value2"
}

# Заголовки запроса
headers = {
    "Content-Type": "application/json"
}

# Отправка POST-запроса
response = requests.post(url, headers=headers, data=json.dumps(data))

# Проверка статуса ответа
if response.status_code == 200:
    print("Запрос успешен!")
    print("Ответ от сервера:", response.json())
else:
    print("Ошибка при выполнении запроса. Код статуса:", response.status_code)
    print("Текст ошибки:", response.text)
