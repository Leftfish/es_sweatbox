import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os

def run_generator():
    tma = tma_entry.get()
    arrivals = arrivals_entry.get()
    departures = departures_entry.get()
    output_path = output_path_entry.get()

    if not tma:
        messagebox.showerror("Error", "TMA name is required.")
        return

    if not arrivals:
        messagebox.showerror("Error", "At least one arrival runway must be specified.")
        return

    if not departures:
        messagebox.showerror("Error", "At least one departure runway must be specified.")
        return

    if not output_path:
        output_path = "test_scenario.txt"

    arrivals_list = arrivals.split()
    departures_list = departures.split()

    generator_path = os.path.join(os.path.dirname(__file__), "generator.py")

    # Update paths for config and flights to locate them in the same directory
    data_dir = os.path.join(os.path.dirname(__file__), "data")

    try:
        command = ["python", generator_path, "-output_path", output_path, tma, "-arr"] + arrivals_list + ["-dep"] + departures_list
        subprocess.run(command, check=True, cwd=os.path.dirname(generator_path))  # Set the working directory
        messagebox.showinfo("Success", f"Scenario generated and saved to {output_path}.")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to generate scenario.\n{e}")

# Create the main window
root = tk.Tk()
root.title("Euroscope Scenario Generator")

# TMA Name
tk.Label(root, text="TMA Name (e.g., EPWA):").grid(row=0, column=0, sticky="w")
tma_entry = tk.Entry(root, width=30)
tma_entry.grid(row=0, column=1, padx=5, pady=5)

# Arrival Runways
tk.Label(root, text="Arrival Runways (e.g., WA33 MO26):").grid(row=1, column=0, sticky="w")
arrivals_entry = tk.Entry(root, width=30)
arrivals_entry.grid(row=1, column=1, padx=5, pady=5)

# Departure Runways
tk.Label(root, text="Departure runways and number of departures from each (e.g., WA29 10 MO26 5):").grid(row=2, column=0, sticky="w")
departures_entry = tk.Entry(root, width=30)
departures_entry.grid(row=2, column=1, padx=5, pady=5)

# Output Path
tk.Label(root, text="Output Path (optional):").grid(row=3, column=0, sticky="w")
output_path_entry = tk.Entry(root, width=30)
output_path_entry.grid(row=3, column=1, padx=5, pady=5)

# Generate Button
generate_button = tk.Button(root, text="Generate Scenario", command=run_generator)
generate_button.grid(row=4, column=0, columnspan=2, pady=10)

# Run the application
root.mainloop()
