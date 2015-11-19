video-archiver
===

At a very high level, this is a web UI around youtube-dl with a few extra features that make it better for long-term downloading (e.g. keeping a YouTube channel synced locally, automatically archiving livestreams, etc.)

Features implemented:

* Start/stop controls
* Basic adding (interface needs a good facelift though...)

TODO:

* Automatic start/stop times on add screen
* Scheduling on add screen

Notes:

* A fair bit of the multiprocessing backend feels very hacked together, but it seems to be by far the most reliable way to keep everything synchronized without having to keep track of log files. Pull requests are more than welcome.
