## Euroscope Sweatbox Scenario Generator

### Overview
This script generates a Euroscope sweatbox scenario with arrivals and departures based on JSON configuration and flight data. It is tailored for approach training scenarios on Vatsim. At this point it's rather rudimentary and tested only for EPWA TMA. The package includes data accurate as of AIRAC 

### Usage

#### Command-Line Arguments
- `-output_path` (optional): Path to the output text file for the scenario. Defaults to `test_scenario.txt` if not provided.
- `TMA` (required): TMA name, e.g., `EPWA`.
- `-arr` (required): List of arrival runways, e.g., `WA33 MO26 LL25`.
- `-dep` (required): List of departure runways followed by the number of departures, e.g., `WA33 10 MO26 5`.

#### Example Command
```bash
python generator.py -output_path scenario.txt EPWA -arr WA33 MO26 -dep WA33 10 MO26 5
```

This command generates a scenario for the EPWA TMA with arrivals on runways WA33 and MO26, and departures from WA33 (10 departures) and MO26 (5 departures). The output is saved to `scenario.txt`.

### Requirements
Requires Python 3.12 or higher.

### Notes
- Ensure the `data` folder contains the required JSON files for the specified TMA (e.g., `EPWA_config.json` and `EPWA_flights.json`).
- The script validates input and raises errors for missing or invalid arguments.

### To do:

##### basic functions
* prepare ~20 more arrivals and ~10 departures from real life data for EPWA TMA

##### long term
* customizable and arrivals departures? (directions?)
* add EPKK/EPKT support