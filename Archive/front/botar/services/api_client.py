import aiohttp
from config import API_BASE_URL

class ApiError(Exception):
    """Исключение для ошибок API."""
    pass

async def search_speaker(full_name: str) -> dict:
    """
    Отправляет POST-запрос на /speaker/search, передавая первые два слова ФИО.
    Формируется запрос:
      { "first_name": "<Capitalized>", "second_name": "<Capitalized>" }
    """
    url = f"{API_BASE_URL}/speaker/search"
    words = full_name.split()
    if len(words) < 2:
        raise ApiError("Недостаточно слов для формирования запроса (требуются минимум 2 слова)")
    payload = {
        "second_name": words[0].capitalize(),
        "first_name": words[1].capitalize()
    }
    print(payload)
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=5) as resp:
            print(resp)
            if resp.status == 200:
                return await resp.json()
            if resp.status == 401:
                return None
            text = await resp.text()
            raise ApiError(f"Unexpected status {resp.status}: {text}")

class ApiError(Exception):
    """Исключение для ошибок API."""
    pass

async def auth_chaperone(login: str, password: str) -> dict:
    """
    Отправляет POST-запрос на /auth для аутентификации сопровождающего.
    Если возвращается 200, возвращает данные пользователя.
    Если возвращается 401 или 404, выбрасывает исключение с сообщением
    "Неправильный логин или пароль, попробуйте снова".
    В остальных случаях выбрасывает исключение с информацией об ошибке.
    """
    url = f"{API_BASE_URL}/teacher/auth"
    payload = {"login": login, "password": password}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=5) as resp:
            if resp.status == 200:
                return await resp.json()
            if resp.status in (401, 404):
                raise ApiError("Неправильный логин или пароль, попробуйте снова")
            text = await resp.text()
            raise ApiError(f"Unexpected status {resp.status}: {text}")

async def get_speaker_details(project_id: str) -> dict:
    """
    Отправляет GET-запрос на /speaker/<id> для получения детальной информации о спикере.
    """
    url = f"{API_BASE_URL}/speaker/{project_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                return await resp.json()
            text = await resp.text()
            raise ApiError(f"Error fetching speaker details: status {resp.status}: {text}")

async def get_workshops() -> list:
    """
    Отправляет POST-запрос на /workshops с сегодняшней датой в формате:
    {
        "date": "2024-05-02"
    }
    для получения списка мастер-классов.
    """
    from datetime import date
    url = f"{API_BASE_URL}/workshops"
    payload = { "date": date.today().isoformat() }
    print(payload)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=5) as resp:
            if resp.status == 200:
                return await resp.json()
            text = await resp.text()
            raise ApiError(f"Unexpected status {resp.status}: {text}")
