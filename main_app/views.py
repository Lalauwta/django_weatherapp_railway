import os
import requests
from django.shortcuts import redirect, render
from django.contrib import messages
from .models import City

# Create your views here.

# OpenWeatherMap API config (key loaded from the environment, never hard-coded)
API_KEY = os.getenv("OPENWEATHER_API_KEY")
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid={}"


def index(request):

    # fail loudly if the API key isn't loaded, instead of every city
    # silently coming back "not found"
    if not API_KEY:
        messages.error(request, 'Weather API key is not configured. Check your .env and restart the server.')
        return render(request, 'index.html', {'weather_data': []})

    # when the user submits a city name, look it up via the API and,
    # if it's valid, add it to the database
    if request.method == "POST":
        city_name = request.POST.get("city")

        try:
            response = requests.get(WEATHER_URL.format(city_name, API_KEY), timeout=10).json()
        except requests.exceptions.RequestException as e:
            print('error connecting to API', e)
            messages.error(request, 'Could not reach the weather service. Please try again.')
            return redirect("index")

        # cod == 200 means the city name is valid, so we can add it to the database
        if response.get("cod") == 200:
            city_name = response.get("name", city_name)
            if not City.objects.filter(name__iexact=city_name).exists():  # check if the city already exists
                City.objects.create(name=city_name)  # add the city to the database
                messages.success(request, f'{city_name} has been added successfully.')
            else:
                messages.info(request, f'{city_name} already exists.')
        else:
            messages.error(request, f'{city_name} was not found.')

        # redirect after POST so a browser refresh doesn't re-submit the form
        return redirect("index")

    weather_data = []

    # get the weather data for each city in the database and add it to the weather_data list
    for city in City.objects.all():
        try:
            data = requests.get(WEATHER_URL.format(city.name, API_KEY), timeout=10).json()
        except requests.exceptions.RequestException as e:
            # a transient connection error shouldn't drop this city or hide the others
            print('error connecting to API', e)
            continue

        if data.get("cod") == 200:
            city_weather = {
                'id': city.id,
                'city': city.name,
                'temperature': data["main"]["temp"],
                'description': data["weather"][0]["description"],
                'icon': data["weather"][0]["icon"],
            }
            weather_data.append(city_weather)
        elif str(data.get("cod")) == "404":
            # only prune cities the API definitively doesn't recognise,
            # never on transient errors (rate limits, 5xx, timeouts)
            City.objects.filter(id=city.id).delete()

    context = {'weather_data': weather_data}

    return render(request, 'index.html', context)


def delete_city(request, city_id):
    if request.method == "POST":
        city = City.objects.filter(id=city_id).first()
        if city:
            city.delete()
            messages.success(request, f'{city.name} has been removed.')
    return redirect("index")
