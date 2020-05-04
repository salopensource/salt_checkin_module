# Overview
This returner module takes the output of a Salt run and processes it into
a Sal ManagedItem and Facts submission format.

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
