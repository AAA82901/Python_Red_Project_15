import requests


def get_localoties(
        api_key: str, 
        name_beginning: str
) -> list[list] | None:
    url = "http://dataservice.accuweather.com/locations/v1/cities/autocomplete"
    params = {
        'apikey': api_key,
        'q': name_beginning,
        'language': 'ru'
    }
    try:
        response = requests.get(url, params=params)
    except requests.exceptions.ConnectionError:
        return None

    if not response.ok:
        return None

    data = response.json()
    result = []
    for loc in data:
        try:
            country = loc['Country']['LocalizedName']
            region = loc['AdministrativeArea']['LocalizedName']
            city = loc['LocalizedName']
            key_ = loc['Key']
            result.append([country, region, city, key_])
        except KeyError:
            continue
    return sorted(result, key=lambda x: x[:3]) # сортируем сначала по стране, затем по региону, затем по названию НП


def get_multiday_forecast(
        api_key: str, 
        location_key: str, 
        days: int = 5
):
    url_map = {
        1: f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}",
        3: f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}", # Нет URL для 3х дней
        5: f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}"
    }
    url = url_map.get(days, url_map[5])

    params = {
        'apikey': api_key,
        'details': True
    }

    try:
        response = requests.get(url, params=params)
    except requests.exceptions.ConnectionError:
        return None

    if not response.ok:
        return None
    data = response.json()

    if "DailyForecasts" not in data:
        return None

    results = []
    for item in data["DailyForecasts"][:days]: # В случае 3х дней, мы из 5ти обработаем только 3
        try:
            # endregion
            # region Средняя температура в °C
            max_temp_f = item["Temperature"]["Maximum"]["Value"]
            min_temp_f = item["Temperature"]["Minimum"]["Value"]
            mean_temp_c = (max_temp_f + min_temp_f) / 2  # в Фаренгейтах
            mean_temp_c = 5 * (mean_temp_c - 32) / 9
            # endregion
            
            # region Скорость ветра в км/ч
            # формулу взял отсюда http://www.for6cl.uznateshe.ru/wp-content/uploads/2018/04/kilometry-v-mili.png
            rain_probability = item["Day"]["RainProbability"]
            wind_speed_mph = item["Day"]["Wind"]["Speed"]["Value"]
            wind_speed_kmh = wind_speed_mph * 15_625 / 25_146 # в км/ч
            # endregion
            
            forecast = {
                "Date": item["Date"],
                "MeanTempC": round(mean_temp_c, 2),
                "RainProb": round(rain_probability, 2),
                "WindSpeedKmH": round(wind_speed_kmh, 2)
            }
            results.append(forecast)
        except KeyError:
            return None

    return results
