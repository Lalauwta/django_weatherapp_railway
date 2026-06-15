from django.shortcuts import redirect, render ,HttpResponse
from django.http import JsonResponse
import requests
from .models import City
from django.contrib import messages

# Create your views here.

def index(request):

    #define API key and URL for the OpenWeatherMap API
    API_KEY = "1e782839d6906ec76bb73173088033df"
    url = "https://api.openweathermap.org/data/2.5/weather?q={}&units=metric&appid={}"
    
    # make a POST request to the API when the user submits a city name,
    # if the city name is valid, add it to the database and redirect to the index page, 

    if request.method == "POST":
        city_name = request.POST.get("city")
        
        response = requests.get(url.format(city_name, API_KEY)).json()
    
    # if the response code is 200, it means the city name is valid, so we can add it to the database and redirect to the index page
        if response.get("cod") == 200:
            city_name = response.get("name", city_name)
            if not  City.objects.filter(name__iexact=city_name).exists(): # check if the city already exists in the database
                    City.objects.create(name=city_name) # add the city to the database
                    messages.success(request,f'{city_name} city has been added succesfuly.')
            else:
                 messages.info(request,f'{city_name} already exist.')
        else:
            messages.error(request,f'{city_name} was not found.')
            return redirect("index")
    

    weather_data = []
    
    # try to get the weather data for each city in the database and add it to the weather_data list
    # if the city is not found in the API, delete it from the database
    try:
        cities = City.objects.all()
        for city in cities:
            response = requests.get(url.format(city.name, API_KEY))
            data = response.json()


            if data.get("cod") == 200:
                city_weather = {
                    'city': city.name,
                    'temperature': data["main"]["temp"],
                    'description': data["weather"][0]["description"],
                    'icon': data["weather"][0]["icon"],
                }
                weather_data.append(city_weather)
            else:
                    City.objects.filter(name=city.name).delete()

    except requests.exceptions.RequestException as e:
        print('error connect to API', e)
    
    context = {'weather_data': weather_data}

    return render(request, 'index.html', context)