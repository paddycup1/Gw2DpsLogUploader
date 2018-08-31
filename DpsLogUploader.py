import requests  #pip3 install requests2
import json
import os
import threading
import asyncio
import sys
import datetime
from collections import OrderedDict
import re
import EvtcParser

class ArgParser:
  SECONDS_IN_HOUR = 60 * 60
  SECONDS_IN_DAY  = 24 * 60 * 60
  def __init__(self, args, bossList):
    self.bosses = []
    self.startTime = datetime.datetime.now()
    self.endTime = datetime.datetime.fromtimestamp(self.startTime.timestamp() - ArgParser.SECONDS_IN_DAY)
    self.last = True
    self.allTime = False
    self.win = 0
    self.sort = 0
    self.sortReverse = False
    self.embed = False
    self.outputPath = "output.json"
    self.rh = True
    self.ei = True
    self.raidar = True

    for index in range(0, len(args)):
      args[index] = args[index].lower()

    index = 0
    while index < len(args):
      if args[index] == "-b" or args[index] == "-boss":
        index += 1
        while index < len(args) and not args[index].startswith("-"):
          self.bosses.extend(searchBossName(bossList, args[index]))
          index += 1
      elif args[index] == "-today":
        self.startTime = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        self.endTime = datetime.datetime.now().replace(hour=23, minute=59, second=59)
        index += 1
      elif args[index] == "-yesterday":
        self.startTime = datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp - ArgParser.SECONDS_IN_DAY).replace(hour=0, minute=0, second=0)
        self.endTime = self.startTime.replace(hour=23, minute=59, second=59)
        index += 1
      elif args[index] == "-last":
        self.last = True
        index += 1
      elif args[index] == "-alltime":
        self.allTime = True
        index += 1
      elif args[index] == "-starttime" or args[index] == "-start":
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
      elif args[index] == "-endtime" or args[index] == "-end":
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
      elif args[index] == "-past":
        index += 1
        self.endTime = datetime.datetime.now()
        while index < len(args) and not args[index].startswith("-"):
          match = re.match("(\\d+)(d|D)", args[index])
          if match:
            self.startTime = datetime.datetime.fromtimestamp(self.endTime.timestamp() - ArgParser.SECONDS_IN_DAY * int(match.group(1)))
          match = re.match("(\\d+)(h|H)", args[index])
          if match:
            self.startTime = datetime.datetime.fromtimestamp(self.endTime.timestamp() - ArgParser.SECONDS_IN_HOUR * int(match.group(1)))
          index += 1
      elif args[index] == "-win":
        self.win = 1
        index += 1
      elif args[index] == "-fail":
        self.win = -1
        index += 1
      elif args[index] == "-sort":
        if args[index + 1] == "time":
          self.sort = 1
        elif args[index + 1] == "name":
          self.sort = 2
        elif args[index + 1] == "encounter":
          self.sort = 3
        else:
          print("Invalid sort type!!")
          sys.exit(0)
        index += 2
      elif args[index] == "-reverse":
        self.sortReverse = True
        index += 1
      elif args[index] == "-o":
        self.outputPath = args[index + 1]
        index += 2
      elif args[index] == "-embed":
        self.embed = True
        self.title = args[index + 1]
        if index + 2 < len(args) and not args[index + 2].startswith("-"):
          self.description = args[index + 2]
        else:
          self.description = ""
        index += 3
      elif args[index] == "-gen":
        index += 1
        self.rh = False
        self.ei = False
        self.raidar = False
        while index < len(args) and not args[index].startswith("-"):
          if args[index] == "rh" or args[index] == "raidheroes":
            self.rh = True
          elif args[index] == "ei" or args[index] == "eilteinsight":
            self.ei = True
          elif args[index] == "rd" or args[index] == "raidar":
            self.raidar = True
          index += 1
        if not (self.rh or self.ei or self.raidar):
          print("No generator selected!!")
          sys.exit(0)
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
          filepath = os.path.join(dirpath, f)
          timestamp = os.path.getmtime(filepath)
          if (timestamp >= start and timestamp <= end) or self.allTime:
            if self.win == 0:
              fileList.append(filepath)
            else:
              print("Parsing {} log {}...".format(boss, f))
              evtc = EvtcParser.EvtcLog(filepath)
              if self.win == 1 and evtc.cbtWin:
                fileList.append(filepath)
              elif self.win == -1 and not evtc.cbtWin:
                fileList.append(filepath)
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

    if self.win != 0:
      print("\n", end="")

    if self.sort:
      if self.sort == 1:
        ret.sort(key=lambda path:os.path.getmtime(path))
      elif self.sort == 2:
        ret.sort()
      elif self.sort == 3:
        ret.sort(key=getBossOrder)
    return ret


def getBossOrder(boss):
  for index in range(0, len(bossList["Bosses"])):
    if bossList["Bosses"][index]["Name"] == boss:
      return index
  return 0


def searchBossName(bossList, name):
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

def getRaidarBossAreas(token):
  url = "https://www.gw2raidar.com/api/v2/areas"
  headers = {
    "Authorization": "Token " + token
  }
  response = requests.get(url, headers=headers)
  if response.status_code == 200:
    return response.json()
  else:
    print("Error: ", response.status_code, response.text)


"""
  Main Start
"""

if sys.argv[1] == "-init":
  raidarToken = gw2RaidarGetToken(sys.argv[2], sys.argv[3])
  if not raidarToken:
    print("Get GW2 Raidar token fail, please chekck username and password then use command \"-raidarlogin\" update config file.")
  config = dict([ 
    ("LogPath", "arcdps combat log path"),
    ("Gw2RaidarToken", raidarToken),
    ("DiscordBotToken", "Token used by discord embed helper bot, optional")
  ])
  with open("Config.json", "w") as configFile:
    json.dump(config, configFile, indent=2)
  print("Initialize config complete, but please update LogPath and DiscordBotToken (optional) manually")
  sys.exit(0)

try:
  with open("Config.json", "r") as configFile:
    config = json.load(configFile)
except BaseException as e:
  print("load config fail:", str(e), "trying create a sample...")
  with open("Config.json", "w") as configFile:
    config = dict([
      ("LogPath", "arcdps combat log path"),
      ("Gw2RaidarToken", "use command -raidarlogin username password to update this field"),
      ("DiscordBotToken", "Token used by discord embed helper bot, optional")])
    json.dump(config, configFile, indent=2)
    print("create sample config success.")
  sys.exit(0)

if sys.argv[1] == "-raidarlogin":
  config["Gw2RaidarToken"] = gw2RaidarGetToken(sys.argv[2], sys.argv[3])
  with open("Config.json", "w") as configFile:
    json.dump(config, configFile, indent=2)
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

argParser = ArgParser(sys.argv, bossList)
uploadFiles = argParser.filterLogs(config["LogPath"])

raidheroesLinks = []
eliteinsightLinks = []
if argParser.raidar:
  for log in uploadFiles:
    if isRaidarAcceptable(log, bossList):
      uploadGw2Raidar(log, config["Gw2RaidarToken"])
  print("\n", end="")

for log in uploadFiles:
  if argParser.rh:
    raidheroesLinks.append(uploadDpsReport(log, gen="rh"))
  if argParser.ei:
    eliteinsightLinks.append(uploadDpsReport(log, gen="ei"))
  
if argParser.raidar:
  loop = asyncio.get_event_loop()
  fu = asyncio.Future()
  asyncio.ensure_future(findAllRaidarLog(uploadFiles, config["Gw2RaidarToken"], bossList, fu))
  loop.run_until_complete(fu)
  raidarlinks = fu.result()

if argParser.embed:
  output = OrderedDict()
  output["title"] = argParser.title
  output["description"] = argParser.description
  output["color"] = 31743
  output["thumbnail"] = dict([("url", "https://render.guildwars2.com/file/5866630DA52DCB5C423FB81ECF69FD071611E36B/1128644.png")])
  output["fields"] = []
  for index in range(0, len(uploadFiles)):
    pathComponent = uploadFiles[index].split(os.path.sep)
    d = OrderedDict()
    d["name"] = pathComponent[len(pathComponent) - 2]
    value = []
    if argParser.raidar:
      if raidheroesLinks[index]:
        value.append("[Raider]({})".format(raidarlinks["Results"][index]))
      else:
        value.append("~~Raider~~")
    if argParser.rh:
      value.append("[RaidHeroes]({})".format(raidheroesLinks[index]))
    if argParser.ei:
      value.append("[EliteInsight]({})".format(eliteinsightLinks[index]))
    
    d["value"] = value[0]
    for i in range(1, len(value)):
      d["value"] += " | "
      d["value"] += value[i]
    output["fields"].append(d)
else:
  output = OrderedDict()
  output["Result"] = []
  for index in range(0, len(uploadFiles)):
    pathComponent = uploadFiles[index].split(os.path.sep)
    d = OrderedDict()
    d["Boss"] = pathComponent[len(pathComponent) - 2]
    d["File"] = pathComponent[len(pathComponent) - 1]
    if argParser.rh:
      d["RaidHeroes"] = raidheroesLinks[index]
    if argParser.ei:
      d["EliteInsight"] = eliteinsightLinks[index]
    if argParser.raidar:
      d["Raidar"] = raidarlinks["Results"][index]
    output["Result"].append(d)

try:
  if len(os.path.dirname(argParser.outputPath)) > 0 and not os.path.exists(os.path.dirname(argParser.outputPath)):
    os.makedirs(os.path.dirname(argParser.outputPath))
  with open(argParser.outputPath, "w") as outfile:
    json.dump(output, outfile, indent=2)
except IOError as e:
  print("write output file fail:", str(e))

print("All complete.")