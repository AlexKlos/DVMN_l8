import json
import os
import requests

from charset_normalizer import from_path
from dotenv import load_dotenv
import folium
from geopy import distance


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def get_distance(coffee):
    return coffee['distance']

def detect_file_encoding(path):
    result = from_path(path).best()
    if result is not None:
        return result.encoding
    return None


def main():
    load_dotenv()
    yandex_api_key = os.getenv('YANDEX_API_KEY')

    place = input('Где вы находитесь? ')
    user_coordinates = fetch_coordinates(yandex_api_key, place)
    reversed_user_coordinates = (
        float(user_coordinates[1]), 
        float(user_coordinates[0])
        )
    
    path = 'coffee.json'
    encoding = detect_file_encoding(path)
    if encoding:
        with open(path, 'r', encoding=encoding) as coffee_file:
            coffee_file_contents = json.loads(coffee_file.read())

    coffees = []

    for coffee in coffee_file_contents:
        coffee_coordinates = (
            float(coffee['geoData']['coordinates'][1]), 
            float(coffee['geoData']['coordinates'][0])
            )
        distance_to_coffee = distance.distance(reversed_user_coordinates, 
                                               coffee_coordinates).km
        normalized_coffee = {
            'title': coffee['Name'], 
            'distance': distance_to_coffee, 
            'latitude': coffee['geoData']['coordinates'][1], 
            'longitude': coffee['geoData']['coordinates'][0]
            }
        coffees.append(normalized_coffee)

    sorted_coffees = sorted(coffees, key=get_distance)

    user_map = folium.Map(reversed_user_coordinates)

    for coffee in sorted_coffees[:5]:
        folium.Marker(
            location=[coffee['latitude'], coffee['longitude']],
            tooltip='Click me!',
            popup=coffee['title'],
            icon=folium.Icon(color='green')
        ).add_to(user_map)

    user_map.save('index.html')


if __name__ == '__main__':
    main()