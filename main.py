import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import folium
from streamlit_folium import st_folium

# Setting the page configuration
st.set_page_config(page_title='Wind Turbine Analysis', page_icon=':dash:')

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
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        daily_data = data.get('daily')
        if daily_data:
            dates = pd.to_datetime(daily_data['time'])  # Converting date strings to datetime
            return pd.DataFrame({
                'date': dates,
                'wind_speed_10m_max': daily_data['wind_speed_10m_max'],
                'wind_gusts_10m_max': daily_data['wind_gusts_10m_max']
            })
    return pd.DataFrame()  # Return an empty DataFrame if there are issues

# Function to calculate energy generation
def calculate_energy(wind_speeds, rated_speed, max_speed, rated_power):
    # Simplified power curve model for demonstration
    energy = []
    for speed in wind_speeds:
        if speed < rated_speed:
            energy.append(0)
        elif rated_speed <= speed < max_speed:
            energy.append(rated_power)
        else:
            energy.append(0)
    return np.sum(energy)  # Summing up the energy for the given period

# Function to create a map for address selection
def create_map(latitude, longitude):
    m = folium.Map(location=[latitude, longitude], zoom_start=12)
    folium.Marker([latitude, longitude], tooltip="Selected Location").add_to(m)
    return m

# Main application
def main():
    st.title('Wind Turbine Analysis Tool')

    # Default date range for January 1-31st of the current year
    default_start_date = datetime(datetime.now().year, 1, 1)
    default_end_date = datetime(datetime.now().year, 1, 31)

    # State management for wind data and map location
    if 'wind_data' not in st.session_state:
        st.session_state['wind_data'] = pd.DataFrame()
    if 'latitude' not in st.session_state:
        st.session_state['latitude'] = 52.52
    if 'longitude' not in st.session_state:
        st.session_state['longitude'] = 13.41

    # Inputs for location and date range
    with st.form("location_form"):
        col1, col2 = st.columns(2)
        latitude = col1.number_input('Latitude', value=st.session_state['latitude'])
        longitude = col2.number_input('Longitude', value=st.session_state['longitude'])
        start_date = col1.date_input('Start Date', value=default_start_date)
        end_date = col2.date_input('End Date', value=default_end_date)
        submitted = st.form_submit_button('Fetch Data')
    
    # Fetch data after form submission
    if submitted:
        st.write("Fetching data...")
        st.session_state['wind_data'] = fetch_wind_data(latitude, longitude, start_date, end_date)
    
    # Display the data if available
    wind_data = st.session_state['wind_data']
    if not wind_data.empty:
        st.subheader('Daily Wind Data')
        st.line_chart(wind_data.set_index('date'))  # Plotting the data on the chart

    # Wind turbine parameters input
    with st.form("turbine_form"):
        st.subheader('Wind Turbine Parameters')
        col1, col2 = st.columns(2)
        start_wind_speed = col1.number_input('Start Wind Speed (m/s)', value=3.0)
        max_wind_speed = col2.number_input('Max Wind Speed (m/s)', value=40.0)
        rated_wind_speed = col1.number_input('Rated Wind Speed (m/s)', value=10.0)
        rated_power = col2.number_input('Rated Power (KW)', value=10.0)
        calculate = st.form_submit_button('Calculate Energy')
    
    # Calculate energy only if button was clicked and data is available
    if calculate and not wind_data.empty:
        energy_generated = calculate_energy(wind_data['wind_speed_10m_max'], rated_wind_speed, max_wind_speed, rated_power)
        st.metric("Total Energy Generated (kWh)", f"{energy_generated/1000:.2f} kWh")
        st.subheader(f"Wind Turbine Analysis for {start_date.year}")
        st.markdown("---")
        st.write(f"### {latitude}°N, {longitude}°E")
        col1, col2 = st.columns(2)
        col1.metric("Max Wind Speed (m/s)", f"{wind_data['wind_speed_10m_max'].max():.2f}", delta="n/a", delta_color="off")
        col2.metric("Average Wind Speed (m/s)", f"{wind_data['wind_speed_10m_max'].mean():.2f}", delta="n/a", delta_color="off")
        col1.metric("Total Energy Generated (kWh)", f"{energy_generated/1000:.2f}", delta="n/a", delta_color="off")
        col2.metric("Rated Power (KW)", f"{rated_power:.2f}", delta="n/a", delta_color="off")

    # Address change input with a map
    st.subheader('Change Address')
    m = create_map(st.session_state['latitude'], st.session_state['longitude'])
    st_data = st_folium(m, width=700, height=500)
    if st_data and st_data['last_clicked']:
        st.session_state['latitude'], st.session_state['longitude'] = st_data['last_clicked']['lat'], st_data['last_clicked']['lng']
        st.write(f"Updated Location: Latitude {st.session_state['latitude']}, Longitude {st.session_state['longitude']}")

if __name__ == "__main__":
    main()
