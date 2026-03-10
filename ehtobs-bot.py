from collections import defaultdict
import time
from argparse import ArgumentParser
from datetime import datetime, timezone

import humanize
import pyvexfile
import slack_utils

vex_date_format = '%Yy%jd%Hh%Mm%Ss'


def vex_duration(value):
    return int(value.replace(' sec', '').strip())


def get_events(vexfile, verbose=0):
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
        start = datetime.strptime(start, vex_date_format).timestamp()
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
        events.append((start+s_ends[0], 'end of scan   '+scan.name, station_string, source))

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


def main(args=None):
    parser = ArgumentParser(description='slackbot that posts the schedule')
    parser.add_argument('--debug', '-d', action='store_true', help='do not post to slack')
    parser.add_argument('--hello', action='store_true', help='say something nice at startup')
    parser.add_argument('--verbose', '-v', action='count', help='be more verbose')
    parser.add_argument('vexfile')
    cmd = parser.parse_args(args=args)

    now_utc = datetime.now(timezone.utc)
    formatted = now_utc.strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f'restart {formatted} {cmd.vexfile}', flush=True)

    events = get_events(cmd.vexfile, verbose=cmd.verbose)

    if cmd.verbose:
        print(f'there are {len(events)} events')
        if cmd.verbose > 1:
            for e in events:
                t, message, stations, source = e
                print(message+' '+stations+' '+source)

    # grab the webhook even in debug mode, so that we know it's there
    webhook = slack_utils.get_slack_webhook('eht', 'ehtobs_bots_schedule')

    beginning = True

    for e in events:
        now = time.time()
        t, message, stations, source = e

        if t < now-10 and beginning:  # 10 seconds where we might double-post at restart
            if cmd.verbose:
                print('skipping', message, stations, source)
            continue

        delta = t - now

        if beginning and cmd.hello:
            mmessage = f'Hello! We are running {cmd.vexfile} and the first scan is in {humanize.precisedelta(round(delta,0))}'
            print(mmessage)
            if not cmd.debug:
                slack_utils.slack_message(mmessage, webhook)

        beginning = False

        if delta > 0:
            if cmd.verbose:
                print(f'sleeping for {delta} seconds', flush=True)
            time.sleep(delta)

        print(message, stations, source, flush=True)
        if not cmd.debug:
            slack_utils.slack_message(message+' '+stations+' '+source, webhook)


if __name__ == '__main__':
    main()
