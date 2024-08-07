# ehtobs-bot

ehtobs-bot posts slack notifications to a single Slack channel
based on a schedule file.

Notifications are currently:

* first scan in 1 hour
* first scan in 5 minutes
* start of scan
* end of scan
* last scan done
* end of schedule

Usage:

$ make check-secrets
$ python ehtobs-bot.py VEXFILE
