import numpy as np
import matplotlib.pyplot as plt

def calculate_energy(wind_speeds, start_speed, rated_speed, max_speed, rated_power):
    """Calculate the energy generation based on wind speed according to the given power curve."""
    energy = 0
    power_generation = []

    for speed in wind_speeds:
        if speed < start_speed:
            # Region 1: No power generated below the cut-in speed
            power_output = 0
        elif start_speed <= speed < rated_speed:
            # Region 2: Power increases non-linearly (cubic) as wind speed increases up to the rated speed
            power_output = rated_power * ((speed - start_speed) / (rated_speed - start_speed)) ** 3
        elif rated_speed <= speed < max_speed:
            # Region 3: Power decreases linearly after reaching rated speed
            power_output = rated_power - ((speed - rated_speed) / (max_speed - rated_speed)) * rated_power
        else:
            # Region 4: Cut-out region, no power generated beyond max speed
            power_output = 0
        
        power_generation.append(power_output)
        energy += power_output  # accumulate energy over each time interval (assuming each interval is 1 hour)

    total_energy = energy  # total energy in kWh, since each interval represents 1 hour
    return total_energy, power_generation


# Parameters
start_speed = 3        # m/s
rated_speed = 10       # m/s
max_speed = 25         # m/s
rated_power = 10000    # W (rated power)

# Wind speeds to test (from 0 to 30 m/s with 1 m/s increments)
wind_speeds = np.arange(0, 30, 1)

# Calculate energy and power generation
total_energy, power_generation = calculate_energy(wind_speeds, start_speed, rated_speed, max_speed, rated_power)

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(wind_speeds, power_generation, label='Power Generation (W)')
plt.xlabel('Wind Speed (m/s)')
plt.ylabel('Power Generation (W)')
plt.title('Wind Power Generation vs Wind Speed')
plt.axvline(start_speed, color='green', linestyle='--', label=f'Start Speed: {start_speed} m/s')
plt.axvline(rated_speed, color='orange', linestyle='--', label=f'Rated Speed: {rated_speed} m/s')
plt.axvline(max_speed, color='red', linestyle='--', label=f'Max Speed: {max_speed} m/s')
plt.legend()
plt.grid(True)
plt.show()

# Print total energy generated (optional)
print(f"Total energy generated: {total_energy:.2f} kWh")
