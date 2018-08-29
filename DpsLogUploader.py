import requests
import json
import os
import threading
import asyncio
import sys
import datetime
from collections import OrderedDict
import re

class LogFilter:
  def __init__(self, args, bossList):
    index = 0
    self.bosses = []
    self.startTime = datetime.datetime.now().replace(hour=0, minute=0, second=0)
    self.endTime = self.startTime.replace(hour=23, minute=59, second=59)
    self.last = False
    self.allTime = False

    while index < len(args):
      if args[index] == "-b":
        index += 1
        while index < len(args) and not args[index].startswith("-"):
          self.bosses.extend(searchBossName(bossList, args[index]))
          index += 1
      elif args[index].lower() == "-today":
        self.startTime = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        self.endTime = datetime.datetime.now().replace(hour=23, minute=59, second=59)
        index += 1
      elif args[index].lower() == "-yesterday":
        secondsInADay = 24 * 60 * 60
        self.startTime = datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp - secondsInADay).replace(hour=0, minute=0, second=0)
        self.endTime = self.startTime.replace(hour=23, minute=59, second=59)
        index += 1
      elif args[index].lower() == "-last":
        self.last = True
        index += 1
      elif args[index].lower() == "-allTime":
        self.allTime = True
        index += 1
      elif args[index].lower() == "-starttime":
        index += 1
        while index < len(args) and not args[index].startswith("-"):
          match = re.match("(\\d+)/(\\d+)/(\\d+)", args[index])
          if match:
            self.startTime = self.startTime.replace(year=int(match.group(1)), month=int(match.group(2)), day=int(match.group(3)))
          match = re.match("(\\d+):(\\d+):(\\d+)", args[index])
          if match:
            self.startTime = self.startTime.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=int(match.group(3)))
          match = re.match("(\\d+):(\\d+)", args[index])
          if match:
            self.startTime = self.startTime.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=0)
          index += 1
      elif args[index].lower() == "-endtime":
        index += 1
        while index < len(args) and not args[index].startswith("-"):
          match = re.match("(\\d+)/(\\d+)/(\\d+)", args[index])
          if match:
            self.endTime = self.endTime.replace(year=int(match.group(1)), month=int(match.group(2)), day=int(match.group(3)))
          match = re.match("(\\d+):(\\d+):(\\d+)", args[index])
          if match:
            self.endTime = self.endTime.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=int(match.group(3)))
          match = re.match("(\\d+):(\\d+)", args[index])
          if match:
            self.endTime = self.endTime.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=0)
          index += 1
      elif args[index].lower() == "-past":
        index += 1
        self.endTime = datetime.datetime.now()
        while index < len(args) and not args[index].startswith("-"):
          match = re.match("(\\d+)(d|D)", args[index])
          if match:
            secondsInADay = 24 * 60 * 60
            self.startTime = datetime.datetime.fromtimestamp(self.endTime.timestamp() - secondsInADay * int(match.group(1))).replace(hour=0, minute=0, second=0)
          match = re.match("(\\d+)(h|H)", args[index])
          if match:
            secondsInAHour = 60 * 60
            self.startTime = datetime.datetime.fromtimestamp(self.endTime.timestamp() - secondsInAHour * int(match.group(1)))
          index += 1
      else:
        index += 1
    if len(self.bosses) == 0:
      self.bosses = searchBossName(bossList, "all")
    
  def filterLogs(self, root):
    ret = []
    start = self.startTime.timestamp()
    end   = self.endTime.timestamp()
    for boss in self.bosses:
      if not os.path.exists(os.path.join(root, boss)):
        continue
      dirpath = os.path.join(root, boss)
      fileList = []
      for f in os.listdir(dirpath):
        if re.match(".+\\.evtc(\\.zip)?", f):
          fileList.append(os.path.join(dirpath, f))
      if len(fileList) == 0:
        continue
      if self.last:
        maxtime = 0
        for log in fileList:
          if os.path.getmtime(log) > maxtime:
            maxtime = os.path.getmtime(log)
          lastlog = log
        timestamp = os.path.getmtime(lastlog)
        if timestamp >= start and timestamp <= end:
          ret.append(lastlog)
        continue
      if self.allTime:
        for log in fileList:
          ret.append(os.path.join(dirpath, log))
        continue
      for log in fileList:
        timestamp = os.path.getmtime(log)
        if timestamp >= start and timestamp <= end:
          ret.append(log)

    return ret


def searchBossName(bossList, name):
  name = name.lower()
  if name == "all":
    ret = []
    for boss in bossList["Bosses"]:
      ret.append(boss["Name"])
    return ret
  for boss in bossList["Bosses"]:
    if boss["Name"].lower() == name:
      return [boss["Name"]]
    for alias in boss["Aliases"]:
      if alias.lower() == name:
        return [boss["Name"]]
  
  for group in bossList["Groups"]:
    if group["Name"].lower() == name:
      return group["Bosses"]
  return None

def uploadDpsReport(path, gen="rh"):
  dps_endpoint = "https://dps.report/uploadContent"
  print("Uploading dps.report ({})".format(gen), path, "......")
  with open(path, "rb") as file:
    files = {
      "file": file
    }
    param = {
      "json": 1,
      "generator": gen
    }
    response = requests.post(dps_endpoint, files=files, params=param)
    if response.status_code == 200:
      return response.json()['permalink']
    else:
      print("Upload file", path, "error:", response.status_code)

def gw2RaidarGetToken(user, paswd):
  url = "https://www.gw2raidar.com/api/v2/token"
  data = {
    "username": user,
    "password": paswd
  }
  response = requests.post(url, data=data)
  if response.status_code == 200:
    return response.json()["token"]
  else:
    return None

def uploadGw2Raidar(path, token):
  url = "https://www.gw2raidar.com/api/v2/encounters/new"
  print("Uploading Gw2 Raidar", path, "......")
  with open(path, "rb") as file:
    files = {
      "file": file
    }
    headers = {
      "Authorization": "Token " + token
    }
    response = requests.put(url, files=files, headers=headers)
    if response.status_code != 200:
      print("Error: ", response.status_code, response.text)

def getGw2RaiderEncounterList(token, offset=0, limit=100):
  url = "https://www.gw2raidar.com/api/v2/encounters"
  headers = {
    "Authorization": "Token " + token
  }
  param = {
    "limit": limit,
    "offset": offset
  }
  response = requests.get(url, headers=headers, params=param)
  if response.status_code == 200:
    return response.json()
  else:
    print("Error: ", response.status_code, response.text)

def findGw2RaidarLog(path, token, limit=100):
  name = os.path.basename(path)
  encounters = getGw2RaiderEncounterList(token, limit=limit)
  for encounter in encounters["results"]:
    if encounter["filename"] == name:
      return "https://www.gw2raidar.com/encounter/" + encounter["url_id"]
  return None

async def findAllRaidarLog(files, token, bossList, future, timegap=20, maxcount=15, limit=100):
  while True:
    ret = syncFindAllRaidarLog(files, token, bossList, limit=limit)
    if ret["LostCount"] == 0:
      future.set_result(ret)
    if maxcount == 0:
      future.set_result(ret)
    print("Waiting Gw2Raidar... remaining {} times({}s), lost {}".format(maxcount, timegap, ret["LostCount"]))
    await asyncio.sleep(timegap)
    maxcount -= 1

def syncFindAllRaidarLog(files, token, bossList, limit=100):
  encounters = getGw2RaiderEncounterList(token, limit=limit)
  ret = dict([("LostCount", 0), ("Results", [])])
  for file in files:
    found = False
    if not isRaidarAcceptable(file, bossList):
      ret["Results"].append(None)
      continue
    for encounter in encounters["results"]:
      if os.path.basename(file) == encounter["filename"]:
        ret["Results"].append("https://www.gw2raidar.com/encounter/" + encounter["url_id"])
        found = True
    if not found:
      ret["Results"].append(None)
      ret["LostCount"] += 1
  return ret

def isRaidarAcceptable(file, bossList):
  pathComponent = file.split(os.path.sep)
  bossname = pathComponent[len(pathComponent) - 2]
  for boss in bossList["Bosses"]:
    if boss["Name"] == bossname:
      return boss["Gw2RaidarAcceptable"]
  return False

"""
  Main Start
"""

try:
  with open("Config.json", "r") as configFile:
    config = json.load(configFile)
except BaseException as e:
  print("load config fail:", str(e), "trying create a sample...")
  with open("Config.json") as configFile:
    config = dict([("LogPath", "arcdps combat log path"), ("Gw2RaidarToken", "use argument -raidarlogin username password to update this field")])
    json.dump(config, configFile)
    print("create sample config success.")
  sys.exit(0)

if sys.argv[1] == "-raidarlogin":
  config["Gw2RaidarToken"] = gw2RaidarGetToken(sys.argv[2], sys.argv[3])
  with open("Config.json", "w") as configFile:
    json.dump(config, configFile)
  sys.exit(0)

try:
  with open("BossList.json", "r") as bosslistfile:
    bossList = json.load(bosslistfile)
except BaseException as e:
  print("load boss list fail:", str(e))
  sys.exit(0)

if "LogPath" not in config:
  print("Can't find arcdps log path in config file! (field name: LogPath)")
  sys.exit(0)

filter = LogFilter(sys.argv, bossList)
uploadFiles = filter.filterLogs(config["LogPath"])

raidheroesLinks = []
eliteinsightLinks = []

for log in uploadFiles:
  if isRaidarAcceptable(log, bossList):
    uploadGw2Raidar(log, config["Gw2RaidarToken"])
print("\n", end="")

for log in uploadFiles:
  raidheroesLinks.append(uploadDpsReport(log, gen="rh"))
  eliteinsightLinks.append(uploadDpsReport(log, gen="ei"))
  

loop = asyncio.get_event_loop()
fu = asyncio.Future()
asyncio.ensure_future(findAllRaidarLog(uploadFiles, config["Gw2RaidarToken"], bossList, fu))
loop.run_until_complete(fu)  
raidarlinks = fu.result()  

output = OrderedDict()
output["Result"] = []

for index in range(0, len(uploadFiles)):
  pathComponent = uploadFiles[index].split(os.path.sep)
  d = OrderedDict()
  d["Boss"] = pathComponent[len(pathComponent) - 2]
  d["File"] = pathComponent[len(pathComponent) - 1]
  d["RaidHeroes"] = raidheroesLinks[index]
  d["EliteInsight"] = eliteinsightLinks[index]
  d["Raidar"] = raidarlinks["Results"][index]
  output["Result"].append(d)

with open("output.json", "w") as outfile:
  json.dump(output, outfile, indent=2)

print("All complete.")