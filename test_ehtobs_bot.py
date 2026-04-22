import ehtobs_bot_utils


def test_stations_slack_format():
    stations = ['Aa', 'Ax', 'Kt', 'Mg', 'Pc', 'Sz']
    stations_str = ':'.join(stations)

    tests = [
        ('', [], ''),
        ('', ['Aa'], ''),
        (stations_str, [], '*`Aa`*:*`Ax`*:*`Kt`*:*`Mg`*:*`Pc`*:*`Sz`*'),
        (stations_str, ['xx'], '*`Aa`*:*`Ax`*:*`Kt`*:*`Mg`*:*`Pc`*:*`Sz`*'),
        (stations_str, ['xxx'], '*`Aa`*:*`Ax`*:*`Kt`*:*`Mg`*:*`Pc`*:*`Sz`*'),
        (stations_str, ['Aa'], '*`Ax`*:*`Kt`*:*`Mg`*:*`Pc`*:*`Sz`*:~`Aa`~'),
        (stations_str, ['Ax'], '*`Aa`*:*`Kt`*:*`Mg`*:*`Pc`*:*`Sz`*:~`Ax`~'),
        (stations_str, ['Pc'], '*`Aa`*:*`Ax`*:*`Kt`*:*`Mg`*:*`Sz`*:~`Pc`~'),
        (stations_str, ['Sz'], '*`Aa`*:*`Ax`*:*`Kt`*:*`Mg`*:*`Pc`*:~`Sz`~'),
        (stations_str, ['Aa', 'Sz'], '*`Ax`*:*`Kt`*:*`Mg`*:*`Pc`*:~`Aa`~:~`Sz`~'),
        (stations_str, stations, '~`Aa`~:~`Ax`~:~`Kt`~:~`Mg`~:~`Pc`~:~`Sz`~'),
    ]

    for stations, dropped, answer in tests:
        assert ehtobs_bot_utils.stations_slack_format(stations, dropped) == answer, dropped
