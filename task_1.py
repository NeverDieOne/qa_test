import asyncio
from dotenv import load_dotenv
import requests_async as requests
import os
from dateutil import parser
import datetime
import pytest
import time
import math

load_dotenv()
BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"


def get_percentile(data, percentile):
    size = len(data)
    return sorted(data)[int(math.ceil((size * percentile) / 100)) - 1]


async def get_latest_value(count=10):
    """Получение данных о count тикерах с наибольшим объемом за последние 24 часа"""
    parameters = {
        'start': '1',
        'limit': count,
        'sort': 'volume_24h'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': os.getenv("API_KEY"),
    }

    async with requests.Session() as session:
        session.headers.update(headers)
        try:
            response = await session.get(BASE_URL, params=parameters)
            response.raise_for_status()

            return (
                response.elapsed.total_seconds(),
                len(response.content),
                [currency["last_updated"] for currency in response.json()["data"]]
            )

        except (ConnectionError, requests.Timeout, requests.TooManyRedirects) as e:
            print(e)


async def async_test_time_response_and_response_size_and_relevance_data(count=8):
    """Запуск первого теста count раз.
    Расчет RPS.
    Расчет 80% latency
    """
    start_time = time.time()
    time_for_response = await asyncio.gather(*(test_time_response_and_response_size_and_relevance_data() for _ in range(count)))
    finish_time = time.time()

    rps = count / (finish_time - start_time)

    return (
        rps,
        get_percentile(time_for_response, 80)
    )


@pytest.mark.asyncio
async def test_time_response_and_response_size_and_relevance_data():
    """Тест на время запроса, размер ответа и актуальность полученных данных.
    Успешен если:
        Ответ получен менее чем за 500 мс.
        Размер ответа меньше 10 кб.
        Данные получены за сегодняшний день
    """
    time_for_response, response_size, currency_updated_list = await get_latest_value()

    current_day = datetime.datetime.today()

    assert time_for_response < 0.5
    assert response_size < 10 * 1024
    for currency_updated in currency_updated_list:
        last_updated = parser.parse(currency_updated)
        assert (current_day.year, current_day.month, current_day.day) == (
            last_updated.year, last_updated.month, last_updated.day)

    return time_for_response


def test_rps_and_time_response():
    """Асинхронный тест RPS и времени ответа от сервера.
    Успешен если:
        Запущенный тест №1 выполнился успешно.
        RPS > 5.
        80% latency < 450 мс.
    """
    rps, latency = asyncio.run(async_test_one())
    assert rps > 5
    assert latency < 0.45
