# arso-vremenska-integracija (BETA)
Vremenska integracija za Home Assistant

ARSO Weather Integration

This is a custom Home Assistant integration for ARSO Weather. It fetches real-time weather data, daily forecasts, and hourly forecasts from the ARSO API (Slovenian Environment Agency).
Features

Current Weather Conditions: Retrieves real-time weather observations from ARSO, including temperature, wind speed, pressure, and weather conditions.
Hourly and Daily Forecasts: Displays weather forecasts for each hour and up to 11 days ahead.
Cascading Logic for Weather Conditions: The integration uses cascading logic to determine weather conditions, checking clouds_icon_wwsyn_icon, wwsyn_shortText, and clouds_shortText to ensure accurate conditions are displayed.
Unique ID Support: Each entity now has a unique ID, allowing you to edit and customize entities in Home Assistant.
Slovenian Cloud Condition Translation: Slovenian cloud conditions are translated into English for compatibility with Home Assistant.

Installation
Manual Installation

Download or clone this repository.
Copy the arso_weather_integration folder to your Home Assistant custom_components directory:

    <config directory>/custom_components/arso_weather_integration

Restart Home Assistant to recognize the new integration.

Setup

Go to the Home Assistant Settings.
Navigate to Devices & Services.
Click Add Integration and search for "ARSO Weather".
Select the integration and follow the prompts to choose your location.

Configuration

This integration requires selecting a location (city or region) from ARSO for weather data.

Choose your location during setup.
The integration will automatically pull the weather data for the selected location.


Data Source

The real-time weather observations are retrieved from the observation section of the ARSO.
Hourly and daily weather forecasts are retrieved from the forecast3h and forecast24h sections of the ARSO.

Supported Features

    Current Temperature (°C)
    Humidity (%)
    Pressure (hPa)
    Wind Speed (km/h)
    Cloud Conditions (translated to Home Assistant-compatible terms)
    Daily and Hourly Forecasts

Unique ID Support

Each weather entity now gets a unique ID based on its location and configuration entry. This allows you to customize and edit the entity from the Home Assistant UI.
Debugging

If you encounter issues, you can enable debug logging for the integration by adding the following to your configuration.yaml:

    logger:
      default: info
      logs:
        custom_components.arso_weather_integration: debug

Known Issues

Precipitation Data: Real-time precipitation may not always be available. But is visible as attribute to weather entitiy.
Forecast Availability: Ensure the selected location supports both hourly and daily forecasts.

Release Notes
Version 1.1.0

Unique ID support: Added unique IDs for weather entities, allowing editing via the Home Assistant UI.
Cascading logic: Implemented cascading logic for selecting weather conditions for both current weather and forecasts.
Bug fixes: Fixed issues where some weather conditions were shown as "unknown" due to improper mapping.
Action call to update works for hourly and daily forecasts (twice daily forecast is not yet supported).

Contributing

If you find any bugs or have feature requests, feel free to open an issue or submit a pull request on GitHub.
