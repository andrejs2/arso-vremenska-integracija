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
from astral.sun import sun
from astral import LocationInfo
import pytz
import feedparser
import re
from .const import DOMAIN, RSS_STATION_CODES  # Uvozite RSS_STATION_CODES iz const.py
from homeassistant.const import UnitOfLength
import asyncio

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
    # Common weather conditions from 'wwsyn_shortText' and 'clouds_shortText'
    "jasno": "sunny",
    "delno oblačno": "partlycloudy",
    "pretežno oblačno": "cloudy",
    "oblačno": "cloudy",
    "megla": "fog",
    "dežuje": "rainy",
    "možnost neviht": "lightning-rainy",
    "dež": "rainy",
    "plohe": "pouring",
    "sneži": "snowy",
    "toča": "hail",
    "sneg z dežjem": "snowy-rainy",
    "vetrovno": "windy",
    "veter z oblaki": "windy-variant",

    # Overcast conditions with thunderstorms and rain ('clouds_icon_wwsyn_icon')
    "overcast_heavytsra_day": "lightning-rainy",
    "overcast_heavytsra_night": "lightning-rainy",
    "overcast_heavyra_day": "rainy",  # Corrected to lowercase
    "overcast_heavyra_night": "rainy",
    "overcast_modtsra_day": "lightning-rainy",
    "overcast_modtsra_night": "lightning-rainy",
    "overcast_modra_day": "rainy",  # Corrected to lowercase
    "overcast_modra_night": "rainy",
    "overcast_lightra_day": "rainy",
    "overcast_lightra_night": "rainy",
    "overcast_lighttsra_day": "lightning-rainy",
    "overcast_lighttsra_night": "lightning-rainy",
    "overcast_day": "cloudy",
    "overcast_night": "cloudy",
    "overcast_lightfg_night": "cloudy",
    "overcast_lightfg_day": "cloudy",
    "overcast_lightra_night": "rainy",
    "overcast_lightra_day": "rainy",
    "overcast_modrasn_night": "snowy-rainy",
    "overcast_modrasn_day": "snowy-rainy",
    "overcast_lightrasn_day": "snowy-rainy",
    "overcast_lightrasn_night": "snowy-rainy",
    "overcast_heavyrasn_night": "snowy-rainy",
    "overcast_heavyrasn_day": "snowy-rainy",
    "overcast_modsn_day": "snowy",
    "overcast_modsn_night": "snowy",
    "overcast_lightsn_day": "snowy",
    "overcast_lightsn_night": "snowy",
    "overcast_modra_night": "rainy",
    "overcast_modra_day": "rainy",
    
    # Partly cloudy and rainy conditions ('clouds_icon_wwsyn_icon')
    "partcloudy_night": "partlycloudy", 
    "partcloudy_day": "partlycloudy", 
    "partcloudy_lightra_day": "pouring", 
    "partcloudy_lightra_night": "pouring", 
    "partcloudy_heavytsra_day": "lightning-rainy", 
    "partcloudy_heavytsra_night": "lightning-rainy",
    "partcloudy_modsn_night": "snowy",
    "partcloudy_modsn_day": "snowy",
    "partcloudy_lightsn_night": "snowy",
    "partcloudy_lightsn_day": "snowy",
    "partcloudy_heavysn_night": "snowy",
    "partcloudy_heavysn_day": "snowy",
    "partcloudy_lightfg_day": "fog",
    "partcloudy_lightfg_night": "fog",
    "partcloudy_lightrasn_day": "snowy-rainy",
    "partcloudy_lightrasn_night": "snowy-rainy",
    "partcloudy_modrasn_day": "snowy-rainy",
    "partcloudy_modrasn_night": "snowy-rainy",
    "partcloudy_heavyrasn_day": "snowy-rainy",
    "partcloudy_heavyrasn_night": "snowy-rainy",
    "partcloudy_modra_day": "rainy",
    "partcloudy_modra_night": "rainy",
    "partcloudy_modtsra_day": "rainy",
    "partcloudy_modtsra_night": "rainy",
    "partcloudy_lighttsra_day": "rainy",
    "partcloudy_lighttsra_night": "rainy",
    "partcloudy_heavytsra_day": "rainy",
    "partcloudy_heavytsra_night": "rainy",
    
    # Storm conditions ('clouds_icon_wwsyn_icon')
    "prevcloudy_modts_day": "lightning",  # Corrected to lowercase
    "prevcloudy_modts_night": "lightning",  # Corrected to lowercase
    "prevcloudy_heavyts_day": "lightning",  # Corrected to lowercase
    "prevcloudy_heavyts_night": "lightning",  # Corrected to lowercase
    "prevcloudy_lightra_night": "rainy",
    "prevcloudy_lightra_day": "rainy",
    "prevcloudy_modra_day": "rainy",
    "prevcloudy_modra_night": "rainy",
    "prevcloudy_heavyra_day": "rainy",
    "prevcloudy_heavyra_night": "rainy",
    "prevcloudy_modsn_day": "snowy",
    "prevcloudy_modsn_night": "snowy",
    "prevcloudy_lightsn_day": "snowy",
    "prevcloudy_lightsn_night": "snowy",
    "prevcloudy_heavysn_day": "snowy",
    "prevcloudy_heavysn_night": "snowy",
    "prevcloudy_lightfg_night": "cloudy",
    "prevcloudy_lightfg_day": "cloudy",
    "prevcloudy_modfg_night": "fog",
    "prevcloudy_modfg_day": "fog",
    "prevcloudy_heavyfg_night": "fog",
    "prevcloudy_heavyfg_day": "fog",
    "prevcloudy_lightrasn_day": "snowy-rainy",
    "prevcloudy_lightrasn_night": "snowy-rainy",
    "prevcloudy_lighttsra_day": "rainy",
    "prevcloudy_lighttsra_night": "rainy",
    "prevcloudy_modtsra_day": "rainy",
    "prevcloudy_modtsra_night": "rainy",
    "prevcloudy_heavytsra_day": "rainy",
    "prevcloudy_heavytsra_night": "rainy",

    # Clear conditions
    "clear_night": "clear-night",
    "clear_day": "sunny",
    "clear_lightfg_night": "fog",
    "clear_lightfg_day": "fog",

    # Additional conditions ('clouds_icon_wwsyn_icon', 'wwsyn_shortText', etc.)
    "mostly_clear_night": "clear-night",
    "mostly_clear_day": "sunny",
    "foggy": "fog",
    "drizzle": "rainy",
    "light_snow": "snowy",
    "heavy_snow": "snowy",
    "partly_cloudy_rain": "rainy",
    "partly_cloudy_day": "partlycloudy",
    "partly_cloudy_night": "partlycloudy",
    "thunderstorm": "lightning-rainy",
    "hailstorm": "hail",
    "blizzard": "snowy",
    "prevcloudy_day": "cloudy",
    "prevcloudy_night": "cloudy",
}

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up ARSO Weather platform from a config entry."""
    location = config_entry.data.get('location', 'Ljubljana')  # Get location from user input
    async_add_entities([ArsoWeather(location, config_entry.entry_id)], True)

class ArsoWeather(WeatherEntity):
    """Representation of ARSO Weather entity."""

    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY

    def __init__(self, location, entry_id):
        self._location = location
        self._station_code = RSS_STATION_CODES.get(location)
        self._attr_native_temperature = None
        self._attr_native_pressure = None
        self._attr_humidity = None
        self._attr_native_wind_speed = None
        self._attr_wind_bearing = None
        self._attr_native_wind_gust_speed = None
        self._attr_native_precipitation = None
        self._attr_condition = None
        self._daily_forecast = None
        self._hourly_forecast = None
        self._entry_id = entry_id  # Store entry_id for unique_id
        self._attr_native_dew_point = None
        self._attr_native_visibility = None
        self._attr_native_visibility_unit = None

    def is_daytime(self):
        """Check if it is currently daytime based on the sun position."""
        loc_info = LocationInfo(self._location)
        s = sun(loc_info.observer, date=datetime.now(self.hass.config.time_zone))
        now = pytz.UTC.localize(datetime.utcnow())
        return s['sunrise'] <= now <= s['sunset']

    @property
    def unique_id(self):
        """Return a unique ID for this entity."""
        return f"{self._entry_id}_{self._location.lower()}"

    @property
    def name(self):
        """Return the name of the entity."""
        return f"ARSO VREME - {self._location}"

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
    def native_wind_gust_speed(self):
        """Return the current wind gust speed."""
        return self._attr_native_wind_gust_speed

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
            "attribution": "Vir: Agencija RS za okolje",
        }

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        attrs = {
            "location": self._location,
            "attribution": "Vir: Agencija RS za okolje",
        }
        if self._attr_native_dew_point is not None:
            attrs["dew_point"] = self._attr_native_dew_point
        if self._attr_native_visibility is not None:
            attrs["visibility"] = self._attr_native_visibility
        return attrs

    async def async_update(self):
        """Fetch new state data for the sensor and update the forecast."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://vreme.arso.gov.si/api/1.0/location/?location={self._location}") as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug("Data: %s", data)

                    observation = data.get("observation", {}).get("features", [])[0].get("properties", {}).get("days", [])[0]["timeline"][0]

                    try:
                        self._attr_native_temperature = float(observation.get("t", 0))
                        self._attr_humidity = float(observation.get("rh", 0))
                        self._attr_native_pressure = float(observation.get("msl", 0))
                        self._attr_native_wind_speed = float(observation.get("ff_val", 0))
                        self._attr_wind_bearing = WIND_DIRECTION_MAP.get(observation.get("dd_shortText", ""), "")
                        self._attr_native_wind_gust_speed = float(observation.get("ffmax_val", 0) or 0)

                        clouds_icon = observation.get("clouds_icon_wwsyn_icon", "").lower()
                        wwsyn_short = observation.get("wwsyn_shortText", "").lower()
                        clouds_short = observation.get("clouds_shortText", "").lower()

                        condition = clouds_icon or wwsyn_short or clouds_short

                        # Check if it's daytime or nighttime
                        if condition == "jasno" and not self.is_daytime():
                            self._attr_condition = "clear-night"
                        else:
                            self._attr_condition = CLOUD_CONDITION_MAP.get(condition, "unknown")

                        _LOGGER.debug("Mapped weather condition: %s", self._attr_condition)
                        self._attr_native_precipitation = 0  # No direct precipitation data in observation
                    except (ValueError, KeyError) as e:
                        _LOGGER.error("Error processing weather observation data: %s", e)
        if self._station_code:
            try:
                rss_url = f"https://meteo.arso.gov.si/uploads/probase/www/observ/surface/text/sl/{self._station_code}_latest.rss"
                feed_content = await self._fetch_rss_feed(rss_url)
                if feed_content:
                    # Asynchronously parse the RSS feed
                    feed = await asyncio.to_thread(feedparser.parse, feed_content)
                    entry = feed.entries[0]
                    details = self._extract_weather_details(entry)

                    if 'native_dew_point' in details:
                        self._attr_native_dew_point = float(details['native_dew_point'])
                    if 'native_visibility' in details:
                        self._attr_native_visibility = float(details['native_visibility'])
                        self._attr_native_visibility_unit = UnitOfLength.KILOMETERS
            except Exception as e:
                _LOGGER.error(f"Error fetching or parsing RSS feed for {self._location}: {e}")
        else:
            _LOGGER.warning(f"No RSS feed available for location {self._location}")

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

                # Get the weather conditions for the hour
                clouds_icon = entry.get("clouds_icon_wwsyn_icon", "").lower()
                wwsyn_short = entry.get("wwsyn_shortText", "").lower()
                clouds_short = entry.get("clouds_shortText", "").lower()

                # Use cascading logic to select the condition
                condition = clouds_icon or wwsyn_short or clouds_short

                # Translate the condition
                condition_translated = CLOUD_CONDITION_MAP.get(condition, "unknown")

                # Build the hourly forecast entry
                hourly_forecasts.append({
                    "datetime": forecast_time,
                    "temperature": float(entry.get("t", 0)),
                    "precipitation": float(entry.get("tp_acc", 0)),
                    "wind_speed": float(entry.get("ff_val", 0)),
                    "wind_bearing": WIND_DIRECTION_MAP.get(entry.get("dd_shortText", ""), ""),
                    "wind_gust_speed": float(entry.get("ffmax_val", 0) or 0), 
                    "condition": condition_translated,
                    "pressure": float(day["timeline"][0].get("msl", 0)),  # Add air pressure
                })

        _LOGGER.debug("Processed Hourly Forecasts: %s", hourly_forecasts)
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

            # Get the weather conditions for the day
            clouds_icon = day["timeline"][0].get("clouds_icon_wwsyn_icon", "").lower()
            wwsyn_short = day["timeline"][0].get("wwsyn_shortText", "").lower()
            clouds_short = day["timeline"][0].get("clouds_shortText", "").lower()

            # Use cascading logic to select the condition
            condition = clouds_icon or wwsyn_short or clouds_short

            # Translate the condition
            condition_translated = CLOUD_CONDITION_MAP.get(condition, "unknown")

            # Build the daily forecast entry
            daily_forecasts.append({
                "datetime": forecast_time,
                "temperature": max_temp,  # Max temperature for the day
                "templow": min_temp,  # Min temperature for the day
                "precipitation": float(day["timeline"][0].get("tp_acc", 0)),
                "wind_speed": float(day["timeline"][0].get("ff_val", 0)),
                "wind_bearing": WIND_DIRECTION_MAP.get(day["timeline"][0].get("dd_shortText", ""), ""),
                "wind_gust_speed": float(day["timeline"][0].get("ffmax_val", 0) or 0),
                "condition": condition_translated,
                "pressure": float(day["timeline"][0].get("msl", 0)),  # Add air pressure
            })

        _LOGGER.debug("Processed Daily Forecasts: %s", daily_forecasts)
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

    async def _fetch_rss_feed(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 404:
                    _LOGGER.error(f"RSS feed not found for URL: {url}")
                    return None
                response.raise_for_status()
                return await response.text()

    def _extract_weather_details(self, entry):
        details = {}

        patterns = {
            'native_dew_point': r'Temperatura rosišča:\s*(-?\d+\.?\d*)\s*°C',
            'native_visibility': r'Vidnost:\s*(\d+\.?\d*)\s*km',
        }

        combined_text = f"{entry.title} {entry.summary}"

        for key, pattern in patterns.items():
            match = re.search(pattern, combined_text)
            if match:
                details[key] = match.group(1)

        return details
