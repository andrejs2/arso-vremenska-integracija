# arso-vremenska-integracija (BETA)
Vremenska integracija za Home Assistant

ARSO Weather Integration

This is a custom Home Assistant integration for ARSO Weather. It fetches real-time weather data, daily forecasts, and hourly forecasts from the ARSO API (Slovenian Environment Agency).
Features

    Current Weather Conditions: Retrieves real-time weather observations from ARSO.
    Hourly Forecasts: Displays weather forecasts for each hour.
    Daily Forecasts: Provides 11 days of daily forecasts.
    Slovenian Cloud Condition Translation: Translates Slovenian cloud conditions into English for Home Assistant compatibility.

Installation
Manual Installation

    Download or clone this repository.
    Copy the arso_weather_integration folder to your Home Assistant custom_components directory:

    javascript

    <config directory>/custom_components/arso_weather_integration

    Restart Home Assistant to recognize the new integration.

Installation via HACS

    Open HACS in Home Assistant.
    Search for "ARSO Weather Integration".
    Click Install.
    Restart Home Assistant.

Setup

    Go to the Home Assistant Settings.
    Navigate to Devices & Services.
    Click Add Integration and search for "ARSO Weather".
    Select the integration and follow the prompts to choose your location.

Configuration

This integration requires selecting a location (city or region) from ARSO for weather data.

    Choose your location during setup.
    The integration will automatically pull the weather data for the selected location.

Example configuration.yaml

If you prefer YAML configuration, you can add the integration as follows:

yaml

arso_weather_integration:
  location: "Ljubljana"

Data Source

    The real-time weather observations are retrieved from the observation section of the ARSO API.
    Hourly and daily weather forecasts are retrieved from forecast3h and forecast24h sections of the ARSO API.

Supported Features

    Current Temperature (°C)
    Humidity (%)
    Pressure (hPa)
    Wind Speed (km/h)
    Cloud Conditions (translated to Home Assistant-compatible terms)
    Daily and Hourly Forecasts

Debugging

If you encounter issues, you can enable debug logging for the integration by adding the following to your configuration.yaml:

yaml

logger:
  default: info
  logs:
    custom_components.arso_weather_integration: debug

Known Issues

    Precipitation Data: Real-time precipitation may not always be available.
    Forecast Availability: Ensure the selected location supports both hourly and daily forecasts.

Contributing

If you find any bugs or have feature requests, feel free to open an issue or submit a pull request on GitHub.
