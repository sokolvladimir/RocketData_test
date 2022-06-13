import requests
import json
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from time import sleep


# Функция получения рабочих часов
def get_working_hours_kfc(lst):

    working_hours = []
    str_ = ''
    day, start, finish = '', '', ''
    for i in lst:
        if str_ == '':
            day = i["weekDayName"]
            start = i["timeFrom"]
            finish = i["timeTill"]
            str_ = day
        elif start == i["timeFrom"] and finish == i["timeTill"]:
            day = i["weekDayName"]
        else:
            if day == str_:
                str_ = f"{day}: c {start[:-3]} до {finish[:-3]}"
                working_hours.append(str_)
                day = i["weekDayName"]
                start = i["timeFrom"]
                finish = i["timeTill"]
                str_ = day
            else:
                str_ = f"{str_} - {day}: c {start[:-3]} до {finish[:-3]}"
                working_hours.append(str_)
                day = i["weekDayName"]
                start = i["timeFrom"]
                finish = i["timeTill"]
                str_ = day
    else:
        if day == str_:
            str_ = f"{day}: c {start[:-3]} до {finish[:-3]}"
            working_hours.append(str_)
        else:
            str_ = f"{str_} - {day}: c {start[:-3]} до {finish[:-3]}"
            working_hours.append(str_)

    return working_hours


def kfc_site():
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/102.0.0.0 Mobile Safari/537.36',
    }

    params = {
        'showClosed': 'true',
    }

    response = requests.get('https://api.kfc.com/api/store/v2/store.get_restaurants', params=params, headers=headers)

    cards = response.json()["searchResults"]
    result = {}

    for card in cards:
        # фильтр пустых карточек или карточек с некорректными данными
        if card["storePublic"]["title"]["ru"] == "Текст по умолчанию" or len(card["storePublic"]["storeId"]) != 8:
            continue

        data = {}

        address = card["storePublic"]["contacts"]["streetAddress"]["ru"]
        data["address"] = address

        location = card["storePublic"]["contacts"]["coordinates"]["geometry"]["coordinates"]
        data["location"] = location

        name = card["storePublic"]["title"]["ru"]
        data["name"] = name

        phone = card["storePublic"]["contacts"]["phone"]["number"]
        data["phones"] = [phone]

        if card["storePublic"]["status"] == "Open":
            lst = card["storePublic"]["openingHours"]["regularDaily"]
            working_hours = get_working_hours_kfc(lst)
            data["working_hours"] = working_hours
        else:
            data["working_hours"] = ["closed"]

        result[card["storePublic"]["storeId"]] = data

    with open('kfc.json', 'w', encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)


def ziko_site():
    url = "https://www.ziko.pl/lokalizator/"
    request = requests.get(url)
    soup = BeautifulSoup(request.text, "lxml")

    cards = soup.findAll("tr", class_="mp-pharmacy-element")
    dct_ziko = {}
    id = 0
    for card in cards:
        name = card.find("span", class_="mp-pharmacy-head").text.strip()
        information = card.find("td", class_="mp-table-address").text.strip()
        address = information.split("tel.")[0].strip()
        telephone = information.split("tel.")[1].split("Infolinia:")[0].strip()

        # Получение часов работы
        list_hours = card.find("td", class_="mp-table-hours").findAll('span')
        working_hours = []
        for i in range(0, len(list_hours), 2):
            str_ = f"{list_hours[i].text} {list_hours[i + 1].text}"
            working_hours.append(str_)

        # Ссылка на карточку магазина. Там хранится информация с долготой и широтой
        link = card.find("td", class_="mp-table-access"). \
            find("div", class_="morepharmacy").find('a').get('href')
        link = "https://www.ziko.pl" + link

        # Парсим карточку магазина
        soup_link = BeautifulSoup(requests.get(link).text, "lxml")

        coordinat = soup_link.find("div", class_="coordinates").findAll("span")
        # Широта
        latitude = float(coordinat[0].text.split(":")[1].strip())
        # Долгота
        longitude = float(coordinat[1].text.split(":")[1].strip())
        coordinates = [latitude, longitude]
        dct = {
            "address": address,
            "location": coordinates,
            "name": name,
            "phones": telephone,
            "working_hours": working_hours
        }
        dct_ziko[id] = dct
        id += 1

    with open("ziko.json", "w", encoding="utf-8") as file:
        json.dump(dct_ziko, file, indent=4, ensure_ascii=False)


def monomah_site():

    url = "https://monomax.by/map"
    request = requests.get(url)
    soup = BeautifulSoup(request.text, "lxml")

    list_shops = soup.findAll("div", class_="shop")
    id = 0
    dct_shop = {}
    for shop in list_shops:
        dct = {"address": shop.find("p", class_="name").text,
               "phones": shop.find("a").text,
               "name": "Мономах"}
        try:
            geolocator = Nominatim(
                user_agent="Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/102.0.0.0 Mobile Safari/537.36")
            address = dct["address"].split("(")[0] + "Минск"
            if "пр-т" in address:
                address = "проспект" + address[4:]
            if address.find(".", 3) != -1:
                address = address[:3] + address[address.find(".", 3) + 1:]
            address = address.replace(",", ' ')
            location = geolocator.geocode(address)
            dct["latlon"] = [location.latitude, location.longitude]
            sleep(3)
        except:
            dct["latlon"] = "Я пытался"

        dct_shop[id] = dct
        id += 1

    with open("manomah.json", "w", encoding="utf-8") as file:
        json.dump(dct_shop, file, indent=4, ensure_ascii=False)


def main():
    kfc_site()
    ziko_site()
    monomah_site()


if __name__ == '__main__':
    main()
