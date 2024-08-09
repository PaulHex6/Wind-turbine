import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from geopy.geocoders import Nominatim
import plotly.express as px

# Setting the page configuration
st.set_page_config(page_title='Wind Turbine Analysis', page_icon=':dash:')

# Initialize geolocator
geolocator = Nominatim(user_agent="wind_turbine_analysis")

# Function to fetch latitude and longitude based on address
def get_lat_lon_from_address(address):
    location = geolocator.geocode(address)
    if location:
        return round(location.latitude, 2), round(location.longitude, 2)
    else:
        st.error(f"Could not find location for address: {address}")
        return None, None

# Fetching wind data using the Open-Meteo API
@st.cache_data(ttl=86400)  # Cache data for one day to avoid excessive API calls
def fetch_wind_data(latitude, longitude, start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "daily": ["wind_speed_10m_max", "wind_gusts_10m_max"],
        "wind_speed_unit": "ms"
    }
    try:
        with st.spinner("Fetching data..."):
            response = requests.get(url, params=params)
            response.raise_for_status()  # Raise HTTPError for bad responses
            data = response.json()
            daily_data = data.get('daily')
            if daily_data:
                dates = pd.to_datetime(daily_data['time'])  # Converting date strings to datetime
                return pd.DataFrame({
                    'date': dates,
                    'wind_speed_10m_max': daily_data['wind_speed_10m_max'],
                    'wind_gusts_10m_max': daily_data['wind_gusts_10m_max']
                })
            else:
                st.error("No data returned from API.")
                return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return pd.DataFrame()

# Improved function to calculate energy generation based on wind speed
def calculate_energy(wind_speeds, start_speed, rated_speed, max_speed, rated_power):
    energy = []
    for speed in wind_speeds:
        if speed < start_speed:
            energy.append(0)
        elif start_speed <= speed < rated_speed:
            power_output = rated_power * ((speed - start_speed) / (rated_speed - start_speed)) ** 3
            energy.append(power_output)
        elif rated_speed <= speed <= max_speed:
            energy.append(rated_power)
        else:
            energy.append(0)
    total_energy = np.sum(energy)  # Sum up energy generated for all the wind speeds
    return total_energy

# Main application
def main():
    st.title('Wind Turbine Analysis Tool')

    # Default date range for January 1-31st of the current year
    default_start_date = datetime(datetime.now().year, 1, 1)
    default_end_date = datetime(datetime.now().year, 1, 31)

    # State management for wind data and location
    if 'wind_data' not in st.session_state:
        st.session_state['wind_data'] = pd.DataFrame()
    if 'latitude' not in st.session_state:
        st.session_state['latitude'] = 52.20  # Default latitude for Warsaw
    if 'longitude' not in st.session_state:
        st.session_state['longitude'] = 20.93  # Default longitude for Warsaw

    # Sidebar for Wind Turbine Parameters
    st.sidebar.subheader('Wind Turbine Parameters')
    start_wind_speed = st.sidebar.number_input('Start Wind Speed (m/s)', value=3.0)
    max_wind_speed = st.sidebar.number_input('Max Wind Speed (m/s)', value=40.0)
    rated_wind_speed = st.sidebar.number_input('Rated Wind Speed (m/s)', value=10.0)
    rated_power = st.sidebar.number_input('Rated Power (KW)', value=10.0)

    # Layout: Start and End Date in columns, Address below
    with st.form("location_form"):
        col1, col2 = st.columns(2)
        start_date = col1.date_input('Start Date', value=default_start_date)
        end_date = col2.date_input('End Date', value=default_end_date)
        address = st.text_input('Address', value="Warszawa, Aleje Jerozolimskie")
        submitted = st.form_submit_button('Fetch Data')

        if submitted:
            # Fetch coordinates from the address
            latitude, longitude = get_lat_lon_from_address(address)
            if latitude is not None and longitude is not None:
                st.session_state['latitude'] = latitude
                st.session_state['longitude'] = longitude
                st.session_state['wind_data'] = fetch_wind_data(latitude, longitude, start_date, end_date)

    # Display the wind data if available
    wind_data = st.session_state['wind_data']
    if not wind_data.empty:  # Check if wind_data is not empty
        st.subheader('Daily Wind Data')
        
        # Plotly chart
        fig = px.line(wind_data, x='date', y=['wind_speed_10m_max', 'wind_gusts_10m_max'], 
                      labels={'value': 'Wind Speed (m/s)', 'date': 'Date'}, 
                      title='Daily Wind Data')
        
        # Add a red line for max wind speed
        fig.add_hline(y=max_wind_speed, line_dash="dash", line_color="red", 
                      annotation_text=f"Max Wind Speed ({max_wind_speed} m/s)", annotation_position="top left")

        st.plotly_chart(fig, use_container_width=True)

        # Automatically calculate energy after fetching data
        energy_generated = calculate_energy(
            wind_data['wind_speed_10m_max'], 
            start_wind_speed, 
            rated_wind_speed, 
            max_wind_speed, 
            rated_power
        )
        st.subheader("Analysis")
        col1, col2 = st.columns(2)
        col1.metric("Total Energy Generated (kWh)", f"{energy_generated/1000:.2f} kWh")
        col1.metric("Max Wind Speed (m/s)", f"{wind_data['wind_speed_10m_max'].max():.2f}", 
                    delta=f"{wind_data['wind_speed_10m_max'].max() - 28:.2f} m/s")
        col2.metric("Average Wind Speed (m/s)", f"{wind_data['wind_speed_10m_max'].mean():.2f}", 
                    delta=f"{wind_data['wind_speed_10m_max'].mean() - 5.5:.2f} m/s")
        col2.metric("Minimum Speed (m/s)", f"{start_wind_speed:.2f}", 
                    delta=f"{start_wind_speed - 0.5:.2f} m/s", delta_color="off")

if __name__ == "__main__":
    main()
