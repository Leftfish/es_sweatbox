## Euroscope Sweatbox Scenario Generator

### Overview
This script generates a Euroscope sweatbox scenario with arrivals and departures based on JSON configuration and flight data. It is tailored for approach training scenarios on Vatsim. At this point it's rather rudimentary and tested only for EPWA TMA. The package includes data accurate as of AIRAC AMDT IFR 08/25 (07 AUG 2025).

### Requirements
Requires Python 3.12 or higher. Scenarios tested in Euroscope 3.2.9.

### Usage

#### Command-Line Interface (CLI)
To run the CLI version, use the `run_cli.py` script:

##### Command-Line Arguments
- `TMA` (required): TMA name, e.g., `EPWA`.
- `-arr` (required): List of arrival runways, e.g., `WA33 MO26 LL25`.
- `-dep` (required): List of departure runways followed by the number of departures, e.g., `WA33 10 MO26 3`.
- `-output_path` (optional): Path to the output text file for the scenario. Defaults to `test_scenario.txt` if not provided.

##### Example Command
```bash
python run_cli.py -output_path scenario.txt EPWA -arr WA33 MO26 LL25 -dep WA29 10 MO26 3
```

This command generates a scenario for the EPWA TMA with arrivals on runways EPWA (33), EPMO (26) and EPLL (25), and departures from WA33 (10 departures) and MO26 (3 departures). The output is saved to `scenario.txt`.

#### Graphical User Interface (GUI)
To run the GUI version, use the `run_gui.py` script:

```bash
python run_gui.py
```

The GUI provides a rudimentary interface to input parameters and generate scenarios without using the command line.

### Notes
- Ensure the `data` folder contains the required JSON files for the specified TMA (e.g., `EPWA_config.json` and `EPWA_flights.json`).
- Depending on the config data, departing aircraft will spawn directly on the runway or next to the holding point. It does not support spawn on stands.
- Due to the simplistic nature of the departure generation, too many departures may lead to weird issues, such as aircraft spawning outside of the aerodrome.
- As of the early release (0.1.0), the difficulty of the scenario can be controlled by changing the following parameters in the config.json file: arrivals_max_capacity (no. of arrivals), arrivals_wave_intervals (minutes), arrivals_wave_minimum and arrivals_wave_maximum (no. of arrivals). The length of the scenario can be modified by changing the DEFAULT_LAST_WAVE in defaults.py. This is rather rough, but I had no time to refactor :) 

### To do
* prepare ~30 more arrivals and departures for EPWA TMA to ensure more variability between the scenarios.
* work on the JSON schema (description, preferably simplification)
* add EPKK/EPKT support after fixing the JSON issues
* customizable and arrivals departures? (directions?)
* more customizability in GUI (difficulty level and/or wave size and frequency) instead of JSON and defaults.py
