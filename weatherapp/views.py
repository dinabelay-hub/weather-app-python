from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import datetime

def get_user_location():
    """
    Fetches the user's approximate location based on their IP address.
    Returns the city name or defaults to 'Dubai' if location is not found.
    """
    try:
        response = requests.get('http://ip-api.com/json').json()
        return response.get('city', 'Dubai')  # Default to Dubai if city is not found
    except Exception:
        return 'Dubai'

def home(request):
    """Main view function to render the weather app homepage."""
    city = request.POST.get('city', '').strip()
    if not city:
        city = get_user_location()  # Get the user's real-time location if no input

    # OpenWeather API URL
    weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'q': city,
        'appid': 'a60f676a6c63a7cc8b9e1844f12e9cd2',
        'units': 'metric'
    }

    try:
        weather_data = requests.get(weather_url, params=params).json()
        if "weather" in weather_data and "main" in weather_data:
            description = weather_data['weather'][0]['description']
            icon = weather_data['weather'][0]['icon']
            temp = weather_data['main']['temp']

            return render(request, "weatherapp/index.html", {
                'description': description,
                'icon': icon,
                'temp': temp,
                'day': datetime.date.today(),
                'city': city,
                'exception_occured': False,
            })
        else:
            raise KeyError  # If response is malformed or city not found
    except (requests.RequestException, KeyError):
        # Step 1: Try fallback using user's IP-based city
        fallback_city = get_user_location()
        fallback_params = {
            'q': fallback_city,
            'appid': 'a60f676a6c63a7cc8b9e1844f12e9cd2',
            'units': 'metric'
        }

        try:
            fallback_data = requests.get(weather_url, params=fallback_params).json()
            if "weather" in fallback_data and "main" in fallback_data:
                description = fallback_data['weather'][0]['description']
                icon = fallback_data['weather'][0]['icon']
                temp = fallback_data['main']['temp']

                messages.warning(request, f"Couldn't find '{city}'. Showing weather for your location: {fallback_city}.")
                return render(request, "weatherapp/index.html", {
                    'description': description,
                    'icon': icon,
                    'temp': temp,
                    'day': datetime.date.today(),
                    'city': fallback_city,
                    'exception_occured': True,
                })
        except Exception:
            pass  # Silent fail — we'll show an error message below

        # Step 2: If all else fails, show a meaningful error
        messages.error(request, "Weather data could not be retrieved at this time. Please try again later.")
        return render(request, "weatherapp/index.html", {
            'description': None,
            'icon': None,
            'temp': None,
            'day': datetime.date.today(),
            'city': None,
            'exception_occured': True,
        })

def results(request):
    if request.method != 'POST' or 'city' not in request.POST:
        return redirect('home')  # name='home' must match your URL pattern for index.html

    city = request.POST['city'] or 'Dubai'
    api_key = 'fcaf7e67b23af140ead09edb2d76dabe'
    params = {'units': 'metric', 'appid': api_key, 'q': city}

    # Get current weather data
    current_weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    current_data = requests.get(current_weather_url, params=params).json()

    # Error handling if city is not found
    if current_data.get('cod') != 200:
        return render(request, 'weatherapp/weather.html', {'error': 'City not found', 'city': city})

    description = current_data['weather'][0]['description']
    icon = current_data['weather'][0]['icon']
    temp = current_data['main']['temp']
    feels_like = current_data['main']['feels_like']
    humidity = current_data['main']['humidity']
    pressure = current_data['main']['pressure']
    wind_speed = current_data['wind']['speed']
    wind_deg = current_data['wind'].get('deg', 0)
    visibility = current_data.get('visibility', 0) / 1000  # in km
    cloudiness = current_data['clouds']['all']
    sunrise = datetime.datetime.fromtimestamp(current_data['sys']['sunrise']).strftime('%H:%M:%S')
    sunset = datetime.datetime.fromtimestamp(current_data['sys']['sunset']).strftime('%H:%M:%S')

    # Precipitation (rain/snow)
    precipitation = 0
    if 'rain' in current_data and '1h' in current_data['rain']:
        precipitation = current_data['rain']['1h']
    elif 'snow' in current_data and '1h' in current_data['snow']:
        precipitation = current_data['snow']['1h']

    # UV Index - needs lat/lon
    lat = current_data['coord']['lat']
    lon = current_data['coord']['lon']
    uv_url = f'https://api.openweathermap.org/data/2.5/uvi?appid={api_key}&lat={lat}&lon={lon}'
    uv_data = requests.get(uv_url).json()
    uv_index = uv_data.get('value', 'N/A')

    day = datetime.date.today()

    # Get forecast and skip today
    forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'
    forecast_data = requests.get(forecast_url, params=params).json()

    forecast_by_day = {}
    today = datetime.date.today()

    for forecast in forecast_data['list']:
        forecast_time = datetime.datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S')
        forecast_date = forecast_time.date()
        if forecast_date == today:
            continue  # skip today
        day_name = forecast_time.strftime('%A')

        if forecast_date not in forecast_by_day:
            forecast_by_day[forecast_date] = {
                'day_name': day_name,
                'temp': forecast['main']['temp'],
                'humidity': forecast['main']['humidity'],
                'description': forecast['weather'][0]['description'],
                'icon': forecast['weather'][0]['icon'],
            }


    forecast_list = list(forecast_by_day.values())

    return render(request, 'weatherapp/weather.html', {
        'description': description,
        'icon': icon,
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
        'day': day,
        'city': city,
        'forecast_list': forecast_list
    })
