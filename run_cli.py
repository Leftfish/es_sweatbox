'''Simple command-line interface for the ES scenario generator.'''

import argparse
import itertools
from generator import save_scenario, generate_scenario

def main():
    arg_parser = argparse.ArgumentParser(description='Generates a Euroscope sweatbox scenario with arrivals and departures.')
    arg_parser.add_argument('-output_path', type=str, help='Path to the output text file for the scenario.')
    arg_parser.add_argument('TMA', type=str, help='TMA name, eg. EPWA.')
    arg_parser.add_argument('-arr', nargs='+', help='List of arrival runways, eg. WA33, MO26, LL25.')
    arg_parser.add_argument('-dep', nargs='+', help='List of departure runways followed by <number of departures>, eg. WA33 10.')
    args = arg_parser.parse_args()

    config_path = f'data//{args.TMA}_config.json'
    flights_path = f'data//{args.TMA}_flights.json'

    try:
        saved_scenario_path = args.output_path

        if not args.arr:
            raise ValueError('At least one arrival runway must be specified with -arr.')
        if not args.dep:
            raise ValueError('At least one departure runway must be specified with -dep.')
        if not saved_scenario_path:
            saved_scenario_path = 'test_scenario.txt'

        batched_departures = [(rwy, int(n)) for rwy, n in itertools.batched(args.dep, 2)]
        save_scenario(saved_scenario_path, generate_scenario(flights_path, config_path, args.arr, batched_departures))

    except FileNotFoundError:
        print(f'{args.TMA} TMA not found. Ensure the config and flights JSON files are in the data folder. The format is <TMA>_<type>.json')
    except ValueError as ve:
        print(f'Error: {ve}')
    except KeyError as ke:
        print(f'Error: Missing runway designation {ke} in the JSON data files. Scenario was not saved.')

if __name__ == "__main__":
    main()
