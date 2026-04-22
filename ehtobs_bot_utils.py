def stations_slack_format(s, broken):
    stations = s.split(':')
    for b in sorted(broken):
        # broken to end with italics
        try:
            stations.remove(b)
            stations.append('~`'+b+'`~')
        except ValueError:
            pass
    # now boldface everything else
    ret = []
    for s in stations:
        if len(s) == 2:
            ret.append('*`'+s+'`*')
        else:
            ret.append(s)
    return ':'.join(ret)
