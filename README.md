# Overview
This returner module takes the output a Salt run and processes it into
a Sal ManagedItem and Facts submission format.

Then, the checkin module opens the results during a Sal checkin, and
adds them to the submission. This setup is primarily to avoid Salt
running at the same time as the Sal checkin from doing crazy things.

# Setup
To make this work, you'll need to configure three pieces.

- Distribute the Sal returner (`sal_returner.py`) to clients (put it into the `_returners` folder of your file root). You can of course use Salt to do this ;)
- Configure your highstate run to use the Sal returner.

e.g.
```
Schedule minion highstate runs:
  schedule.present:
    - name: highstate
	- run_on_start: True
	- function: state.highstate
	- minutes: 30
	- maxrunning: 1
	- enabled: True
	- returner: sal
	- splay: 600
```

- Distribute the `salt_checkin_module.py` to the client machine's Sal checkin_modules directory. (On Mac: `/usr/local/sal/checkin_modules`). Again, you can use Salt to do this.

There is a timing issue with this; if you distribute the returner with Salt, it won't be there in time to get imported during that same run. In practice, this is not a big deal, since it will probably be running a highstate again in not that long. If it's an issue, you can package it up and deploy everything with the sal-scripts.
