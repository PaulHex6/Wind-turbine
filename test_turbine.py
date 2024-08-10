import numpy as np
import matplotlib.pyplot as plt

def calculate_energy(wind_speeds, start_speed, rated_speed, max_speed, rated_power, peak_power, peak_power_speed):
    """Calculate the energy generation based on wind speed according to the given power curve."""
    energy = 0
    power_generation = []
    time_interval = 1 / len(wind_speeds)  # assuming each speed step corresponds to an equal portion of time

    for speed in wind_speeds:
        if speed < start_speed:
            # Region 1: No power generated below the cut-in speed
            power_output = 0
        elif start_speed <= speed < rated_speed:
            # Region 2: Power increases non-linearly (cubic) as wind speed increases
            power_output = peak_power * ((speed - start_speed) / (rated_speed - start_speed)) ** 3
        elif rated_speed <= speed <= peak_power_speed:
            # Region 3: Power remains at peak (14,000 W) after reaching rated speed
            power_output = peak_power
        elif peak_power_speed < speed <= max_speed:
            # Region 4: Power decreases linearly as wind speed increases
            power_output = peak_power - ((speed - peak_power_speed) / (max_speed - peak_power_speed)) * (peak_power - rated_power)
        else:
            # Region 5: Cut-out region, no power generated
            power_output = 0
        
        power_generation.append(power_output)
        energy += power_output * time_interval  # accumulate energy over each time interval

    total_energy = energy / 1000  # convert to kWh
    return total_energy, power_generation

# Parameters
start_speed = 3        # m/s
rated_speed = 10       # m/s
peak_power_speed = 15  # m/s (peak power occurs here)
max_speed = 25         # m/s
rated_power = 10000    # W (rated power)
peak_power = 14000     # W (peak power)

# Wind speeds to test (from 0 to 30 m/s with 1 m/s increments)
wind_speeds = np.arange(0, 30, 1)

# Calculate energy and power generation
total_energy, power_generation = calculate_energy(wind_speeds, start_speed, rated_speed, max_speed, rated_power, peak_power, peak_power_speed)

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(wind_speeds, power_generation, label='Power Generation (W)')
plt.xlabel('Wind Speed (m/s)')
plt.ylabel('Power Generation (W)')
plt.title('Wind Power Generation vs Wind Speed')
plt.axvline(start_speed, color='green', linestyle='--', label=f'Start Speed: {start_speed} m/s')
plt.axvline(rated_speed, color='orange', linestyle='--', label=f'Rated Speed: {rated_speed} m/s')
plt.axvline(peak_power_speed, color='blue', linestyle='--', label=f'Peak Power Speed: {peak_power_speed} m/s')
plt.axvline(max_speed, color='red', linestyle='--', label=f'Max Speed: {max_speed} m/s')
plt.legend()
plt.grid(True)
plt.show()

# Print total energy generated (optional)
print(f"Total energy generated: {total_energy:.2f} kWh")
