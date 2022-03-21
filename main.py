from datetime import datetime
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET


def check_files(file_1, file_2):
    for file in (file_1, file_2):
        if not Path(file).is_file():
            print(f'File {file} not found.')
            return None

    return True


def get_time(timestamp):
    return datetime.strptime(timestamp, '%Y-%m-%dT%H%M')


def format_time(time):
    return time.strftime('%d.%m %H:%M')


def format_mins(mins):
    if mins < 60:
        return f'{mins}m'
    elif mins % 60 == 0:
        return f'{mins // 60}h'
    else:
        return f'{mins // 60}h{mins % 60}m'


def format_cost_diff(cost_1, cost_2):
    if cost_1 > cost_2:
        return f'[+{round(cost_1 - cost_2, 2)}]'
    elif cost_1 == cost_2:
        return ''
    else:
        return f'[{round(cost_1 - cost_2, 2)}]'


def format_datetime_with_diff(dt_1, dt_2):
    dt_1_date = datetime(dt_1.year, dt_1.month, dt_1.day)
    dt_2_date = datetime(dt_2.year, dt_2.month, dt_2.day)
    diff_days = (dt_1_date - dt_2_date).days
    coerced_dt_1 = datetime(
        dt_2.year, dt_2.month, dt_2.day,
        dt_1.hour, dt_1.minute
    )

    if diff_days > 0:
        date_diff = f' [+{diff_days}d]'
    elif diff_days == 0:
        date_diff = ''
    else:
        date_diff = f' [{diff_days}d]'

    if coerced_dt_1 > dt_2:
        diff_mins = (coerced_dt_1 - dt_2).seconds // 60
        time_diff = f' [+{format_mins(diff_mins)}]'
    elif coerced_dt_1 == dt_2:
        time_diff = ''
    else:
        diff_mins = (dt_2 - coerced_dt_1).seconds // 60
        time_diff = f' [-{format_mins(diff_mins)}]'

    return (
        f'{dt_1.strftime("%d.%m")}{date_diff}'
        f' {dt_1.strftime("%H:%M")}{time_diff}'
    )


def parse_via_xml(via_xml_file):
    tree = ET.parse(via_xml_file)
    root = tree.getroot()
    itineraries = root.findall('PricedItineraries/Flights')

    parsed_itineraries = []
    for itinerary in itineraries:
        onward_flights = itinerary.findall(
            'OnwardPricedItinerary/Flights/Flight'
        )
        return_flights = itinerary.findall(
            'ReturnPricedItinerary/Flights/Flight'
        )
        pricing = itinerary.find('Pricing')
        source = onward_flights[0].find('Source').text
        destination = onward_flights[-1].find('Destination').text
        departure_time = get_time(
            onward_flights[0].find('DepartureTimeStamp').text
        )
        arrival_time = get_time(
            onward_flights[-1].find('ArrivalTimeStamp').text
        )
        currency = pricing.attrib.get('currency')
        cost = float(pricing.find(
            '.ServiceCharges[@ChargeType="TotalAmount"][@type="SingleAdult"]'
        ).text)

        parsed_onward_flights = []
        for flight in onward_flights:
            flight_source = flight.find('Source').text
            flight_destination = flight.find('Destination').text
            flight_departure_time = get_time(
                flight.find('DepartureTimeStamp').text
            )
            flight_number = flight.find('FlightNumber').text
            flight_arrival_time = get_time(
                flight.find('ArrivalTimeStamp').text
            )
            parsed_flight = {
                'source': flight_source,
                'destination': flight_destination,
                'number': flight_number,
                'departure_time': flight_departure_time,
                'arrival_time': flight_arrival_time,
            }
            parsed_onward_flights.append(parsed_flight)

        parsed_return_flights = []
        for flight in return_flights:
            flight_source = flight.find('Source').text
            flight_destination = flight.find('Destination').text
            flight_departure_time = get_time(
                flight.find('DepartureTimeStamp').text
            )
            flight_number = flight.find('FlightNumber').text
            flight_arrival_time = get_time(
                flight.find('ArrivalTimeStamp').text
            )
            parsed_flight = {
                'source': flight_source,
                'destination': flight_destination,
                'number': flight_number,
                'departure_time': flight_departure_time,
                'arrival_time': flight_arrival_time,
            }
            parsed_return_flights.append(parsed_flight)

        parsed_itinerary = {
            'source': source,
            'destination': destination,
            'onward_flights': parsed_onward_flights,
            'return_flights': parsed_return_flights,
            'cost': cost,
            'currency': currency,
            'departure_time': departure_time,
            'arrival_time': arrival_time,
        }

        parsed_itineraries.append(parsed_itinerary)

    return parsed_itineraries


def show_flight(indent, flight):
    print(
        f'{indent}{flight["source"]} --> {flight["destination"]}'
        f' #{flight["number"]}'
        f' ({format_time(flight["departure_time"])} - '
        f'{format_time(flight["arrival_time"])})'
    )


def show_flights_diff(indent, flight_1, flight_2):
    departure_dt_with_diff = format_datetime_with_diff(
        flight_2["departure_time"],
        flight_1["departure_time"],
    )
    arrival_dt_with_diff = format_datetime_with_diff(
        flight_2["arrival_time"],
        flight_1["arrival_time"],
    )

    print(
        f'{indent}{flight_2["source"]} --> {flight_2["destination"]}'
        f' #{flight_2["number"]}'
        f' ({departure_dt_with_diff} - {arrival_dt_with_diff})'
    )


def show_itinerary(sign, itinerary):
    if len(itinerary['onward_flights']) > 1:
        print(
            f'{sign} {itinerary["source"]} --> {itinerary["destination"]}'
            f' ({format_time(itinerary["departure_time"])} - '
            f'{format_time(itinerary["arrival_time"])}):'
        )
        if itinerary['return_flights']:
            print('  onward:')
        for flight in itinerary['onward_flights']:
            show_flight('    ', flight)
        if itinerary['return_flights']:
            print('  return:')
            if len(itinerary['return_flights']) > 1:
                for flight in itinerary['return_flights']:
                    show_flight('    ', flight)
            else:
                show_flight('  ', itinerary['return_flights'][0])
    else:
        print(
            f'{sign} {itinerary["source"]} --> {itinerary["destination"]}'
            f' #{itinerary["onward_flights"][0]["number"]}'
            f' ({format_time(itinerary["departure_time"])} - '
            f'{format_time(itinerary["arrival_time"])})'
        )
        if itinerary['return_flights']:
            print('  return:')
            if len(itinerary['return_flights']) > 1:
                for flight in itinerary['return_flights']:
                    show_flight('    ', flight)
            else:
                show_flight('  ', itinerary['return_flights'][0])
    print(f'  cost: {itinerary["cost"]} {itinerary["currency"]}\n')


def show_itineraries_diff(itinerary_1, itinerary_2):
    departure_dt_with_diff = format_datetime_with_diff(
        itinerary_2["departure_time"],
        itinerary_1["departure_time"],
    )
    arrival_dt_with_diff = format_datetime_with_diff(
        itinerary_2["arrival_time"],
        itinerary_1["arrival_time"],
    )

    if len(itinerary_1['onward_flights']) > 1:
        print(
            f'~ {itinerary_2["source"]} --> {itinerary_2["destination"]}'
            f' ({departure_dt_with_diff} - {arrival_dt_with_diff}):'
        )
        if itinerary_1['return_flights']:
            print('  onward:')
        for i in range(len(itinerary_1['onward_flights'])):
            flight_1 = itinerary_1["onward_flights"][i]
            flight_2 = itinerary_2["onward_flights"][i]
            show_flights_diff('    ', flight_1, flight_2)
        show_return_flights_diff(
            itinerary_1['return_flights'],
            itinerary_2['return_flights'],
        )
    else:
        print(
            f'~ {itinerary_2["source"]} --> {itinerary_2["destination"]}'
            f' #{itinerary_2["onward_flights"][0]["number"]}'
            f' ({departure_dt_with_diff} - {arrival_dt_with_diff})'
        )
        show_return_flights_diff(
            itinerary_1['return_flights'],
            itinerary_2['return_flights'],
        )
    print(
        f'  cost: {itinerary_2["cost"]} {itinerary_2["currency"]}'
        f' {format_cost_diff(itinerary_2["cost"], itinerary_1["cost"])}\n'
    )


def show_return_flights_diff(flights_1, flights_2, ir=False):
    if ir:
        if flights_1 and not flights_2:
            print('- return:')
            if len(flights_1) > 1:
                indent = '    '
            else:
                indent = '  '
            for flight in flights_1:
                show_flight(indent, flight)
        elif not flights_1 and flights_2:
            print('+ return:')
            if len(flights_2) > 1:
                indent = '    '
            else:
                indent = '  '
            for flight in flights_2:
                show_flight(indent, flight)
        else:
            for i in range(len(flights_1)):
                try:
                    if flights_1[i]['number'] == flights_2[i]['number']:
                        show_flights_diff('    ', flights_1[i], flights_2[i])
                    else:
                        show_flight('  - ', flights_1[i])
                        show_flight('  + ', flights_2[i])
                except IndexError:
                    show_flight('  - ', flights_1[i])
            if len(flights_2) > len(flights_1):
                first_new_flight_index = len(flights_2) - len(flights_1) + 1
                last_new_flight_index = len(flights_2) - 1
                for i in range(first_new_flight_index, last_new_flight_index):
                    show_flight('  + ', flights_2[i])
    else:
        if flights_1:
            print('  return:')
            if len(flights_1) > 1:
                indent = '    '
            else:
                indent = '  '
            for i in range(len(flights_1)):
                show_flights_diff(indent, flights_1[i], flights_2[i])


def show_itineraries_diff_ir(itinerary_1, itinerary_2):
    departure_dt_with_diff = format_datetime_with_diff(
        itinerary_2["departure_time"],
        itinerary_1["departure_time"],
    )
    arrival_dt_with_diff = format_datetime_with_diff(
        itinerary_2["arrival_time"],
        itinerary_1["arrival_time"],
    )

    if len(itinerary_1['onward_flights']) > 1:
        print(
            f'~ {itinerary_2["source"]} --> {itinerary_2["destination"]}'
            f' ({departure_dt_with_diff} - {arrival_dt_with_diff}):'
        )
        if itinerary_1['return_flights'] or itinerary_2['return_flights']:
            print('  onward:')
        for i in range(len(itinerary_1['onward_flights'])):
            flight_1 = itinerary_1["onward_flights"][i]
            flight_2 = itinerary_2["onward_flights"][i]
            show_flights_diff('    ', flight_1, flight_2)
        show_return_flights_diff(
            itinerary_1['return_flights'],
            itinerary_2['return_flights'],
            ir=True,
        )
    else:
        print(
            f'~ {itinerary_2["source"]} --> {itinerary_2["destination"]}'
            f' #{itinerary_2["onward_flights"][0]["number"]}'
            f' ({departure_dt_with_diff} - {arrival_dt_with_diff})'
        )
        show_return_flights_diff(
            itinerary_1['return_flights'],
            itinerary_2['return_flights'],
            ir=True,
        )
    print(
        f'  cost: {itinerary_2["cost"]} {itinerary_2["currency"]}'
        f' {format_cost_diff(itinerary_2["cost"], itinerary_1["cost"])}\n'
    )


def show_itinerary_sets_diff(itineraries_1, itineraries_2):
    for itinerary_1 in itineraries_1:
        itinerary_match_found = False
        for itinerary_2 in itineraries_2:
            itinerary_match = True
            if (
                len(itinerary_1['onward_flights']) ==
                len(itinerary_2['onward_flights'])
            ):
                for i in range(len(itinerary_1['onward_flights'])):
                    if (
                        itinerary_1['onward_flights'][i]['number'] !=
                        itinerary_2['onward_flights'][i]['number']
                    ):
                        itinerary_match = False
            else:
                itinerary_match = False
            if itinerary_match:
                if (
                    len(itinerary_1['return_flights']) ==
                    len(itinerary_2['return_flights'])
                ):
                    for i in range(len(itinerary_1['return_flights'])):
                        if (
                            itinerary_1['return_flights'][i]['number'] !=
                            itinerary_2['return_flights'][i]['number']
                        ):
                            itinerary_match = False
                else:
                    itinerary_match = False
            if itinerary_match:
                show_itineraries_diff(itinerary_1, itinerary_2)
                itinerary_match_found = True
                break
        if itinerary_match_found:
            itineraries_2.remove(itinerary_2)
        else:
            show_itinerary('-', itinerary_1)

    for itinerary_2 in itineraries_2:
        show_itinerary('+', itinerary_2)


def show_itinerary_sets_diff_ir(itineraries_1, itineraries_2):
    for itinerary_1 in itineraries_1:
        itinerary_match_found = False
        for itinerary_2 in itineraries_2:
            itinerary_match = True
            if (
                len(itinerary_1['onward_flights']) ==
                len(itinerary_2['onward_flights'])
            ):
                for i in range(len(itinerary_1['onward_flights'])):
                    if (
                        itinerary_1['onward_flights'][i]['number'] !=
                        itinerary_2['onward_flights'][i]['number']
                    ):
                        itinerary_match = False
            else:
                itinerary_match = False
            if itinerary_match:
                show_itineraries_diff_ir(itinerary_1, itinerary_2)
                itinerary_match_found = True
                break
        if itinerary_match_found:
            itineraries_2.remove(itinerary_2)
        else:
            show_itinerary('-', itinerary_1)

    for itinerary_2 in itineraries_2:
        show_itinerary('+', itinerary_2)


def main():
    parser = argparse.ArgumentParser(
        description='Via XML comparison',
    )
    parser.add_argument(
        '-ir',
        '--ignore_return',
        action='store_true',
        help='Ignore return flights match',
    )
    parser.add_argument(
        'file_1',
        help='1st Via XML file to compare',
    )
    parser.add_argument(
        'file_2',
        help='2nd Via XML file to compare',
    )

    args = parser.parse_args()
    ignore_return_match = args.ignore_return
    file_1 = args.file_1
    file_2 = args.file_2

    if check_files(file_1, file_2):
        itineraries_1 = parse_via_xml(file_1)
        itineraries_2 = parse_via_xml(file_2)
        if ignore_return_match:
            show_itinerary_sets_diff_ir(itineraries_1, itineraries_2)
        else:
            show_itinerary_sets_diff(itineraries_1, itineraries_2)


if __name__ == '__main__':
    main()
