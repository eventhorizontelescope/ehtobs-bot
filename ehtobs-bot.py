import sys
import datetime
from collections import defaultdict
import time

import pyvexfile
import slack_utils

vex_date_format = '%Yy%jd%Hh%Mm%Ss'


def vex_duration(value):
    return int(value.replace(' sec', '').strip())


def get_events(vexfile):
    v = pyvexfile.Vex('foo', vexfile=vexfile)
    events = []
    all_stations = set()
    sfirst = {}
    slast = {}

    for scan in v['SCHED'].values():
        if 'Scan' not in str(type(scan)):
            continue

        entry = scan['start']
        # start = 2023y109d17h25m00s; mode=band6; source=3C84;
        # in theory the vex parser should split these entries, but it doesn't
        parts = entry.value.split(';')
        start = parts[0]
        start = datetime.datetime.strptime(start, vex_date_format).timestamp()
        if len(parts) > 2:
            source = parts[2].replace(' source=', '', 1)
        else:
            source = ''

        s_stations = []
        s_starts = []
        s_ends = []

        entries = scan['station']
        if not isinstance(entries, list):
            # single-station scans come back as scalar, not list
            entries = [entries]
        for entry in entries:
            s_station = entry.value[0]

            # 2025 quirk
            if s_station == 'Pc':
                continue

            all_stations.add(s_station)
            s_start = vex_duration(entry.value[1])
            if s_station not in sfirst:
                sfirst[s_station] = start + s_start
            s_end = vex_duration(entry.value[2])
            slast[s_station] = start + s_end
            s_stations.append(s_station)
            s_starts.append(s_start)
            s_ends.append(s_end)

        if any(x != s_starts[0] for x in s_starts):
            for x in s_starts:
                print(x)
            raise ValueError('different s_start in', s_starts)
        if any(x != s_ends[0] for x in s_ends):
            raise ValueError('different s_start in', s_ends)

        station_string = ':'.join(sorted(s_stations))
        events.append((start, 'start of scan '+scan.name, station_string, source))
        events.append((start+s_ends[0], 'end of scan '+scan.name, station_string, source))

    assert len(s_starts) == len(s_ends)

    start_to_stations = defaultdict(list)
    for station, start in sfirst.items():
        start_to_stations[start].append(station)
    end_to_stations = defaultdict(list)
    for station, end in slast.items():
        end_to_stations[end].append(station)

    for start, stations in start_to_stations.items():
        station_string = ':'.join(sorted(stations))
        events.append((start - 3600, 'first scan in 1 hour', station_string, ''))
        events.append((start - 300, 'first scan in 5 minutes', station_string, ''))
    for end, stations in end_to_stations.items():
        events.append((end, 'last scan done', ':'.join(sorted(stations)), ''))

    # sort events by time
    events = sorted(events)  # defaults to first element
    final = max([x for x in end_to_stations.keys()])
    events.append((final, 'end of schedule', 'for all stations', ''))

    return events


events = get_events(sys.argv[1])
beginning = True
webhook = slack_utils.get_slack_webhook('eht', 'ehtobs_bots_schedule')

for e in events:
    now = time.time()
    t, message, stations, source = e

    if t < now-2 and beginning:
        print('skipping', message, stations, source)
        continue
    beginning = False

    delta = t - now
    if delta > 0:
        time.sleep(delta)

    print(message, stations, source)
    slack_utils.slack_message(message+' '+stations+' '+source, webhook)
