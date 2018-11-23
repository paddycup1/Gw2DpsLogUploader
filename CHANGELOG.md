# 2018 / 11 /23 1.1.2 Add -healthover
* Add `-healthover` command.
* Known issue: can't determine Deimos's encounter result.

# 2018 / 10 /31 1.1.1 Bug Fix

# 2018 / 10 / 25 1.1.0 Features Update
* Add commands `-raidarwaittime`, `-raidarretrycount`, `-raidarsearchcount`, `-notonlyraidar`
* Remove `Gw2RaidarAcceptable` filed from `BossList.json`
* Add optional field `LifeThreshold` into `BossList.json`
* Get Gw2Raidar support list before parsing, now the tool will base on this support decide whether upload the log or not.