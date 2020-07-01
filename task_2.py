import requests
import pytest
from selenium import webdriver


def get_available_languages():
    """Возвращает список с кодами доступных языков"""
    browser = webdriver.Chrome()
    link = "https://coinmarketcap.com/"
    browser.get(link)
    element = browser.find_element_by_xpath("//*[normalize-space() = 'EN']")
    element.click()
    languages = browser.find_elements_by_class_name('cmc-language-picker__option')

    available_langs = []

    for language in languages:
        href = language.get_property("href")
        lang_code = href.split('/')[-2]

        if len(lang_code) > 5:  # чтобы исключить попадание "coinmarketcap.com" в список и добавить туда английский
            available_langs.append("en")
            continue

        available_langs.append(lang_code)

    browser.quit()

    return available_langs


@pytest.mark.parametrize('language', get_available_languages())
def test_languages(language):
    """Тест для проверки переключения языков.
    Успешен если:
        Страница с языком из списка существует.
        Язык страницы совпадает с языком в URL.
    """
    response = requests.get(f'https://coinmarketcap.com/{language}/')
    response.raise_for_status()

    assert response.status_code == 200
    assert response.headers["Content-Language"] == language
