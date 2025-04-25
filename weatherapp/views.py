from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from .ai import get_ai_suggestion
import requests
import datetime
import logging

# Get user location based on IP (fallback: Dubai)
def get_user_location():
    try:
        response = requests.get('http://ip-api.com/json').json()
        return response.get('city', 'Dubai')
    except Exception:
        return 'Dubai'

# API endpoint for real-time AI weather suggestion
def weather_suggestion(request):
    main = request.GET.get('main', 'clear')
    desc = request.GET.get('desc', 'clear sky')
    temp = float(request.GET.get('temp', 32))
    suggestion = get_ai_suggestion(main, desc, temp)
    return JsonResponse({"suggestion": suggestion})

# Home view: show current weather and AI-based suggestion
def home(request):
    city = request.POST.get('city', '').strip() or get_user_location()

    params = {
        'q': city,
        'appid': 'a60f676a6c63a7cc8b9e1844f12e9cd2',
        'units': 'metric'
    }

    try:
        data = requests.get('https://api.openweathermap.org/data/2.5/weather', params=params).json()
        logging.info("Weather API Response: %s", data)

        if "weather" in data and "main" in data:
            desc = data['weather'][0]['description']
            icon = data['weather'][0]['icon']
            temp = data['main']['temp']
            main_weather = data['weather'][0]['main']
            icon_class = get_icon_class(main_weather, desc)
            suggestion = get_ai_suggestion(main_weather, desc, temp)

            return render(request, "weatherapp/index.html", {
                'description': desc,
                'icon': icon,
                'icon_class': icon_class,
                'temp': temp,
                'day': datetime.date.today(),
                'city': city,
                'exception_occured': False,
                'suggestion': suggestion
            })
        raise KeyError

    except (requests.RequestException, KeyError):
        # Fallback using user location
        fallback_city = get_user_location()
        fallback_params = {**params, 'q': fallback_city}

        try:
            fallback_data = requests.get('https://api.openweathermap.org/data/2.5/weather', params=fallback_params).json()
            if "weather" in fallback_data and "main" in fallback_data:
                desc = fallback_data['weather'][0]['description']
                icon = fallback_data['weather'][0]['icon']
                temp = fallback_data['main']['temp']
                main_weather = fallback_data['weather'][0]['main']
                icon_class = get_icon_class(main_weather, desc)

                messages.warning(request, f"Couldn't find '{city}'. Showing weather for your location: {fallback_city}.")
                return render(request, "weatherapp/index.html", {
                    'description': desc,
                    'icon': icon,
                    'icon_class': icon_class,
                    'temp': temp,
                    'day': datetime.date.today(),
                    'city': fallback_city,
                    'exception_occured': True,
                })

        except Exception:
            pass

        messages.error(request, "Weather data could not be retrieved. Please try again later.")
        return render(request, "weatherapp/index.html", {
            'description': None,
            'icon': None,
            'temp': None,
            'day': datetime.date.today(),
            'city': None,
            'exception_occured': True,
        })
# Results view: detailed weather report
def results(request):
    if request.method != 'POST' or 'city' not in request.POST:
        return redirect('home')

    city = request.POST['city'] or 'Dubai'
    api_key = 'fcaf7e67b23af140ead09edb2d76dabe'
    params = {'units': 'metric', 'appid': api_key, 'q': city}

    current_url = 'https://api.openweathermap.org/data/2.5/weather'
    forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'
    uv_url_template = 'https://api.openweathermap.org/data/2.5/uvi'

    try:
        current_data = requests.get(current_url, params=params).json()

        # Check if the response is valid
        if current_data.get('cod') != 200:
            raise ValueError(f"Error: {current_data.get('message', 'City not found')}")
        
        desc = current_data['weather'][0]['description']
        main_weather = current_data['weather'][0]['main']
        temp = current_data['main']['temp']
        suggestion = get_ai_suggestion(main_weather, desc, temp)
        icon_class = get_icon_class(main_weather, desc)
        icon = current_data['weather'][0]['icon']

        # Additional details
        feels_like = current_data['main']['feels_like']
        humidity = current_data['main']['humidity']
        pressure = current_data['main']['pressure']
        wind_speed = current_data['wind']['speed']
        wind_deg = current_data['wind'].get('deg', 0)
        visibility = current_data.get('visibility', 0) / 1000
        cloudiness = current_data['clouds']['all']
        sunrise = datetime.datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M:%S')
        sunset = datetime.datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M:%S')

        # Rain/Snow check
        precipitation = current_data.get('rain', {}).get('1h', 0) or current_data.get('snow', {}).get('1h', 0)

        # UV Index
        lat, lon = current_data['coord']['lat'], current_data['coord']['lon']
        uv_data = requests.get(uv_url_template, params={'appid': api_key, 'lat': lat, 'lon': lon}).json()
        uv_index = uv_data.get('value', 'N/A')

        # Forecast data
        forecast_data = requests.get(forecast_url, params=params).json()
        forecast_by_day = {}
        today = datetime.date.today()

        for forecast in forecast_data.get('list', []):
            forecast_time = datetime.datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S')
            forecast_date = forecast_time.date()
            if forecast_date == today:
                continue
            if forecast_date not in forecast_by_day:
                forecast_by_day[forecast_date] = {
                    'day_name': forecast_time.strftime('%A'),
                    'temp': forecast['main']['temp'],
                    'humidity': forecast['main']['humidity'],
                    'description': forecast['weather'][0]['description'],
                    'icon': forecast['weather'][0]['icon'],
                }

        return render(request, 'weatherapp/weather.html', {
            'description': desc,
            'icon': icon,
            'icon_class': icon_class,
            'temp': temp,
            'feels_like': feels_like,
            'humidity': humidity,
            'pressure': pressure,
            'wind_speed': wind_speed,
            'wind_deg': wind_deg,
            'visibility': visibility,
            'cloudiness': cloudiness,
            'sunrise': sunrise,
            'sunset': sunset,
            'precipitation': precipitation,
            'uv_index': uv_index,
            'day': today,
            'city': city,
            'suggestion': suggestion,
            'forecast_list': list(forecast_by_day.values())
        })

    except (requests.RequestException, ValueError) as e:
        # Handle invalid city name error
        if 'City not found' in str(e):
            messages.error(request, f"Could not retrieve weather data for '{city}'. Please check the city name and try again.")
        else:
            messages.error(request, f"Error retrieving weather data for {city}. Please try again later.")
        return render(request, 'weatherapp/weather.html', {'error': f"Could not retrieve weather data for {city}.", 'city': city})

    except KeyError as e:
        logging.error(f"Missing data in weather response: {e}")
        messages.error(request, "An error occurred while retrieving weather data. Please try again later.")
        return render(request, 'weatherapp/weather.html', {'error': "An error occurred. Please try again later.", 'city': city})

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, 'weatherapp/weather.html', {'error': "An unexpected error occurred.", 'city': city})


# Maps weather condition to icon class
def get_icon_class(main, description):
    main = main.lower()
    description = description.lower()

    icon_map = {
        "thunderstorm": "wi-thunderstorm",
        "drizzle": "wi-sprinkle",
        "rain": "wi-rain",
        "snow": "wi-snow",
        "mist": "wi-fog",
        "smoke": "wi-smoke",
        "haze": "wi-day-haze",
        "dust": "wi-dust",
        "fog": "wi-fog",
        "sand": "wi-sandstorm",
        "ash": "wi-volcano",
        "squall": "wi-strong-wind",
        "tornado": "wi-tornado",
        "clear": "wi-day-sunny",
        "clouds": {
            "few clouds": "wi-day-cloudy",
            "scattered clouds": "wi-cloud",
            "broken clouds": "wi-cloudy",
            "overcast clouds": "wi-cloudy"
        }
    }

    if main == "clouds":
        return icon_map["clouds"].get(description, "wi-cloudy")
    return icon_map.get(main, "wi-na")
