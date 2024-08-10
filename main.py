import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from geopy.geocoders import Nominatim
import plotly.graph_objects as go
from io import BytesIO

# Set the title and favicon that appear in the browser's tab bar.
st.set_page_config(
    page_title='WindProfit',
    page_icon='⚡',
)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data(ttl=86400)
def fetch_wind_data(latitude, longitude, start_date, end_date):
    """Fetch historical wind data using the Open-Meteo API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d'),
        "hourly": ["wind_speed_10m", "wind_gusts_10m"],
        "wind_speed_unit": "ms"
    }
    try:
        with st.spinner("Fetching data..."):
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            hourly_data = data.get('hourly')
            if hourly_data:
                dates = pd.date_range(
                    start=pd.to_datetime(hourly_data['time'][0], utc=True),
                    periods=len(hourly_data['time']),
                    freq=pd.Timedelta(hours=1)
                )
                return pd.DataFrame({
                    'date': dates,
                    'wind_speed_10m': hourly_data['wind_speed_10m'],
                    'wind_gusts_10m': hourly_data['wind_gusts_10m']
                })
            else:
                st.error("No data returned from API.")
                return pd.DataFrame()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from API: {e}")
        return pd.DataFrame()

def calculate_energy(wind_speeds, start_speed, rated_speed, max_speed, rated_power):
    """Calculate the energy generation based on wind speed."""
    energy = []
    power_generation = []
    for speed in wind_speeds:
        if speed < start_speed:
            power_output = 0
        elif start_speed <= speed < rated_speed:
            power_output = rated_power * ((speed - start_speed) / (rated_speed - start_speed)) ** 3
        elif rated_speed <= speed <= max_speed:
            power_output = rated_power
        else:
            power_output = 0
        power_generation.append(power_output)
        energy.append(power_output * 1)  # Energy = Power * Time (1 hour in this case)

    total_energy = np.sum(energy)  # Sum up energy generated for all the wind speeds in kWh
    return total_energy, power_generation

def get_lat_lon_from_address(address):
    """Convert address to latitude and longitude."""
    geolocator = Nominatim(user_agent="wind_profit_analysis")
    location = geolocator.geocode(address)
    if location:
        return round(location.latitude, 2), round(location.longitude, 2)
    else:
        st.error(f"Could not find location for address: {address}")
        return None, None

def to_excel(df, metadata, filename='wind_data.xlsx'):
    """Convert DataFrame to Excel format with metadata."""
    # Convert timezone-aware datetimes to naive datetimes
    df['date'] = df['date'].dt.tz_localize(None)
    
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Write the main data to the first sheet
    df.to_excel(writer, index=False, sheet_name='Wind Data')

    # Write metadata to a second sheet
    metadata_df = pd.DataFrame(metadata, index=[0])
    metadata_df.to_excel(writer, index=False, sheet_name='Metadata')

    writer.close()
    processed_data = output.getvalue()

    return processed_data

# -----------------------------------------------------------------------------
# Main application

def main():
    # Set the title that appears at the top of the page.
    st.title('⚡ WindProfit')

    # Add some spacing
    st.markdown('''
    Analyze potential horizontal wind turbine energy generation based on historical wind data.
    ''')

    # Sidebar for Wind Turbine Parameters
    st.sidebar.subheader('Wind Turbine Parameters')
    rated_power = st.sidebar.number_input('Rated Power (KW)', value=10.0)
    rated_wind_speed = st.sidebar.number_input('Rated Wind Speed (m/s)', value=10.0)
    start_wind_speed = st.sidebar.number_input('Start Wind Speed (m/s)', value=3.0)
    max_wind_speed = st.sidebar.number_input('Max Wind Speed (m/s)', value=40.0)

    # Empty line for separation
    st.sidebar.text("")

    # Electricity Price section with updated default value
    st.sidebar.subheader('Electricity Price')
    electricity_price = st.sidebar.number_input('USD per kWh', value=0.3)

    # Layout: Start and End Date in the first row, Address, Latitude, Longitude, and Google Maps link in the second row, Fetch Data button in the third row
    with st.form("location_form"):
        # First row: Start and End Date
        col1, col2 = st.columns(2)
        start_date = col1.date_input('Start Date', value=datetime(datetime.now().year, 1, 1))
        end_date = col2.date_input('End Date', value=datetime(datetime.now().year, 1, 31))

        # Second row: Address, Latitude, Longitude, and Fetch Data button
        col3, col4, col5, col6 = st.columns([2, 1, 1, 1])
        address = col3.text_input('Address', value="Warszawa, Aleje Jerozolimskie")
        latitude, longitude = None, None

        if 'latitude' in st.session_state and 'longitude' in st.session_state:
            latitude = st.session_state['latitude']
            longitude = st.session_state['longitude']
        
        if latitude and longitude:
            col4.text_input('Latitude', value=str(latitude), disabled=True)
            col5.text_input('Longitude', value=str(longitude), disabled=True)
            google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
            col6.markdown(
                f"<div style='text-align: center; color: #6c757d; font-size: small;'>"
                f"<a href='{google_maps_link}' style='color: #6c757d; text-decoration: none;'>"
                f"Verify<br>Google Maps</a></div>",
                unsafe_allow_html=True
            )
        
        # Third row: Fetch Data button
        submitted = st.form_submit_button('Fetch Data')

        if submitted:
            latitude, longitude = get_lat_lon_from_address(address)
            if latitude is not None and longitude is not None:
                st.session_state['latitude'] = latitude
                st.session_state['longitude'] = longitude
                st.session_state['wind_data'] = fetch_wind_data(latitude, longitude, start_date, end_date)
                st.session_state['metadata'] = {
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'Address': address,
                    'Start Date': start_date.strftime('%Y-%m-%d'),
                    'End Date': end_date.strftime('%Y-%m-%d')
                }
                
                # Update the input fields after data fetch
                col4.text_input('Latitude', value=str(latitude), disabled=True)
                col5.text_input('Longitude', value=str(longitude), disabled=True)
                google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
                col6.markdown(
                    f"<div style='text-align: center; color: #6c757d; font-size: small;'>"
                    f"<a href='{google_maps_link}' style='color: #6c757d; text-decoration: none;'>"
                    f"Verify<br>Google Maps</a></div>",
                    unsafe_allow_html=True
                )

    # Display the wind data if available
    wind_data = st.session_state.get('wind_data', pd.DataFrame())
    if not wind_data.empty:
        st.header('Hourly Wind Data', divider='gray')

        # Calculate energy and power generation
        total_energy, power_generation = calculate_energy(
            wind_data['wind_speed_10m'], 
            start_wind_speed, 
            rated_wind_speed, 
            max_wind_speed, 
            rated_power
        )

        wind_data['power_generation'] = power_generation

        # Calculate the Bill Total in USD
        bill_total = total_energy * electricity_price  # No need to divide by 1000 since energy is already in kWh

        # Plotly chart with dual axes
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=wind_data['date'], y=wind_data['wind_speed_10m'], mode='lines', name='Wind Speed (10m)', line=dict(color='rgb(30,144,255)')))  # Blue
        fig.add_trace(go.Scatter(x=wind_data['date'], y=wind_data['wind_gusts_10m'], mode='lines', name='Wind Gusts (10m)', line=dict(color='rgb(173,216,230)')))  # Light Blue
        fig.add_trace(go.Scatter(x=wind_data['date'], y=wind_data['power_generation'], mode='lines', name='Power Generation (kW)', line=dict(color='rgb(255,140,0)'), yaxis='y2'))  # Dark Orange

        fig.add_hline(y=max_wind_speed, line_dash="dash", line_color="red", annotation_text=f"Max Wind Speed ({max_wind_speed} m/s)", annotation_position="top left")

        fig.update_layout(
            title="Hourly Wind Data and Power Generation",
            yaxis=dict(title="Wind Speed (m/s)", titlefont=dict(color="rgb(30,144,255)"), tickfont=dict(color="rgb(30,144,255)")),
            yaxis2=dict(title="Power Generation (kW)", titlefont=dict(color="rgb(255,140,0)"), tickfont=dict(color="rgb(255,140,0)"), overlaying="y", side="right"),
            xaxis=dict(title="Date"),
            legend=dict(x=0.01, y=-0.2, orientation="h", bordercolor="Black", borderwidth=1),
            plot_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Source information
        st.markdown("<div style='text-align:right; font-size:small;'><i>Source: Open-Meteo</i></div>", unsafe_allow_html=True)

        st.header('Analysis', divider='gray')

        col1, col2 = st.columns(2)
        col1.metric("Total Energy Generated (kWh)", f"{total_energy:.2f} kWh", f"saved ${bill_total:.2f}", delta_color="normal")
        col1.metric("Max Wind Speed (m/s)", f"{wind_data['wind_speed_10m'].max():.2f}", delta=f"{wind_data['wind_speed_10m'].max() - 28:.2f} m/s")
        col2.metric("Average Wind Speed (m/s)", f"{wind_data['wind_speed_10m'].mean():.2f}", delta=f"{wind_data['wind_speed_10m'].mean() - 5.5:.2f} m/s")
        col2.metric("Minimum Speed (m/s)", f"{start_wind_speed:.2f}", delta=f"{start_wind_speed - 0.5:.2f} m/s", delta_color="off")

        # Save Data button
        filename = f"wind_data_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}_{address.replace(' ', '_')}.xlsx"
        df_xlsx = to_excel(wind_data, st.session_state['metadata'], filename)

        st.download_button(label='📥 Save Wind Data as Excel',
                           data=df_xlsx,
                           file_name=filename)

if __name__ == "__main__":
    main()
