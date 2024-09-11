import aiohttp
import logging
from datetime import datetime
from homeassistant.components.weather import WeatherEntity
from homeassistant.const import UnitOfTemperature, UnitOfPressure, UnitOfSpeed
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from homeassistant.components.weather import WeatherEntityFeature

_LOGGER = logging.getLogger(__name__)

WIND_DIRECTION_MAP = {
    "S": "S",
    "J": "S",  # South
    "SZ": "NW",  # Northwest
    "SV": "NE",  # Northeast
    "Z": "W",  # West
    "V": "E",  # East
    "JZ": "SW",  # Southwest
    "JV": "SE",  # Southeast
    "N": "N"  # North
}

# Translation map for Slovenian cloud conditions to Home Assistant-compatible terms
CLOUD_CONDITION_MAP = {
    "jasno": "sunny",
    "delno oblačno": "partlycloudy",
    "pretežno oblačno": "cloudy",
    "oblačno": "cloudy",
    "megla": "fog",
    "dež": "rainy",
    "sneg": "snowy",
    "plohe": "pouring",
    "sneženje": "snowy",
    "možnost neviht": "lightning-rainy",
    "nevihte": "lightning",
    "toča": "hail",
    "vetrovno": "windy",
    "veter z oblaki": "windy-variant",
    "sneg z dežjem": "snowy-rainy",
}

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up ARSO Weather platform from a config entry."""
    location = config_entry.data.get('location', 'Ljubljana')  # Get location from user input
    async_add_entities([ArsoWeather(location)], True)

class ArsoWeather(WeatherEntity):
    """Representation of ARSO Weather entity."""

    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, location):
        self._location = location
        self._attr_native_temperature = None
        self._attr_native_pressure = None
        self._attr_humidity = None
        self._attr_native_wind_speed = None
        self._attr_wind_bearing = None
        self._attr_native_precipitation = None
        self._attr_condition = None
        self._daily_forecast = None
        self._hourly_forecast = None

    @property
    def name(self):
        """Return the name of the entity."""
        return f"ARSO Weather - {self._location}"

    @property
    def native_temperature(self):
        return self._attr_native_temperature

    @property
    def native_temperature_unit(self):
        return UnitOfTemperature.CELSIUS

    @property
    def native_pressure(self):
        return self._attr_native_pressure

    @property
    def native_pressure_unit(self):
        return UnitOfPressure.HPA

    @property
    def humidity(self):
        return self._attr_humidity

    @property
    def native_wind_speed(self):
        return self._attr_native_wind_speed

    @property
    def native_wind_speed_unit(self):
        return UnitOfSpeed.KILOMETERS_PER_HOUR

    @property
    def wind_bearing(self):
        return self._attr_wind_bearing

    @property
    def condition(self):
        return self._attr_condition

    @property
    def forecast(self):
        """Return the daily forecast."""
        return self._daily_forecast

    @property
    def native_precipitation(self):
        return self._attr_native_precipitation

    @property
    def precipitation_unit(self):
        return 'mm'

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {
            "location": self._location,
            "attribution": "Powered by ARSO",
        }

    async def async_update(self):
        """Fetch new state data for the sensor and update the forecast."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://vreme.arso.gov.si/api/1.0/location/?location={self._location}") as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug("Data: %s", data)

                    # Use observation for current weather
                    observation = data.get("observation", {}).get("features", [])[0].get("properties", {}).get("days", [])[0]["timeline"][0]

                    try:
                        self._attr_native_temperature = float(observation.get("t", 0))
                        self._attr_humidity = float(observation.get("rh", 0))
                        self._attr_native_pressure = float(observation.get("msl", 0))
                        self._attr_native_wind_speed = float(observation.get("ff_val", 0))
                        self._attr_wind_bearing = WIND_DIRECTION_MAP.get(observation.get("dd_shortText", ""), "")
                        self._attr_condition = CLOUD_CONDITION_MAP.get(observation.get("clouds_shortText", "").lower(), "unknown")
                        self._attr_native_precipitation = 0  # No direct precipitation data in observation
                    except (ValueError, KeyError) as e:
                        _LOGGER.error("Error processing weather observation data: %s", e)

        # Fetch forecast data
        await self._fetch_forecasts()

    async def _fetch_forecasts(self):
        """Fetch both daily and hourly forecast data."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://vreme.arso.gov.si/api/1.0/location/?location={self._location}") as response:
                if response.status == 200:
                    forecast_data = await response.json()

                    # Log the entire forecast data for debugging purposes
                    _LOGGER.debug("Full Forecast Data: %s", forecast_data)

                    # Process the forecast data
                    self._hourly_forecast = self._process_hourly_forecast(forecast_data)
                    self._daily_forecast = self._process_daily_forecast(forecast_data)

    def _process_hourly_forecast(self, forecast_data):
        """Process the hourly forecast data."""
        hourly_forecasts = []

        # Loop over all days in the forecast data
        for day in forecast_data["forecast3h"]["features"][0]["properties"]["days"]:
            # Loop over each hourly timeline entry within each day
            for entry in day["timeline"]:
                forecast_time = datetime.strptime(entry["valid"], "%Y-%m-%dT%H:%M:%S%z")

                # Get the cloud condition for the hour
                cloud_condition = entry.get("clouds_shortText", "unknown")
                
                # Translate the cloud condition from Slovenian to English
                cloud_condition_translated = CLOUD_CONDITION_MAP.get(cloud_condition.lower(), "unknown")

                # Build the hourly forecast entry
                hourly_forecasts.append({
                    "datetime": forecast_time,
                    "temperature": float(entry.get("t", 0)),
                    "precipitation": float(entry.get("tp_acc", 0)),
                    "wind_speed": float(entry.get("ff_val", 0)),
                    "wind_bearing": WIND_DIRECTION_MAP.get(entry.get("dd_shortText", ""), ""),
                    "condition": cloud_condition_translated,  # Translated condition
                })

        # Log the processed hourly forecasts for debugging
        _LOGGER.debug("Processed Hourly Forecasts for All Days: %s", hourly_forecasts)

        return hourly_forecasts

    def _process_daily_forecast(self, forecast_data):
        """Process the daily forecast data."""
        daily_forecasts = []
        
        # Loop over all available forecast days in the data
        for day in forecast_data["forecast3h"]["features"][0]["properties"]["days"]:
            # Extract the date for the forecast
            forecast_time = day["date"]

            # Get min/max temperature by iterating over all entries in the day's timeline
            temperatures = [float(entry.get("t", 0)) for entry in day["timeline"] if "t" in entry]
            min_temp = min(temperatures) if temperatures else None
            max_temp = max(temperatures) if temperatures else None

            # Get the cloud condition for the day
            cloud_conditions = [entry.get("clouds_shortText", "unknown") for entry in day["timeline"]]
            cloud_condition = cloud_conditions[0] if cloud_conditions else "unknown"

            # Translate the cloud condition from Slovenian to English
            cloud_condition_translated = CLOUD_CONDITION_MAP.get(cloud_condition.lower(), "unknown")

            # Build the daily forecast entry
            daily_forecasts.append({
                "datetime": forecast_time,
                "temperature": max_temp,  # Max temperature for the day
                "templow": min_temp,  # Min temperature for the day
                "precipitation": float(day["timeline"][0].get("tp_acc", 0)),
                "wind_speed": float(day["timeline"][0].get("ff_val", 0)),
                "wind_bearing": WIND_DIRECTION_MAP.get(day["timeline"][0].get("dd_shortText", ""), ""),
                "condition": cloud_condition_translated,
            })

        # Log the processed daily forecasts for debugging
        _LOGGER.debug("Processed Daily Forecasts: %s", daily_forecasts)

        # Return all available daily forecasts, up to 11 days
        return daily_forecasts[:11]  # Return 11 days

    async def async_forecast_hourly(self):
        """Return the hourly forecast."""
        return self._hourly_forecast

    async def async_forecast_daily(self):
        """Return the daily forecast."""
        return self._daily_forecast

    def _map_condition(self, clouds_short_text):
        """Map ARSO cloud conditions to Home Assistant weather conditions."""
        return CLOUD_CONDITION_MAP.get(clouds_short_text.lower(), "unknown")
