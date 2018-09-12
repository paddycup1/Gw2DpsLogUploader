from collections import OrderedDict
from time import sleep
import requests  #pip3 install requests2
import json
import os
import threading
import sys
import datetime
import re
import EvtcParser

class ArgParser:
  SECONDS_IN_HOUR = 60 * 60
  SECONDS_IN_DAY  = 24 * 60 * 60

  FORMAT_PLAIN = 0
  FORMAT_EMBED = 1
  FORMAT_JSON  = 2

  SORT_NONE      = 0
  SORT_TIME      = 1
  SORT_BOSS_NAME = 2
  SORT_ENCOUNTER = 3

  RESULT_WIN  = 1
  RESULT_ALL  = 0
  RESULT_FAIL = -1
  def __init__(self, inputArgs, bossList):
    self.bosses = []
    self.endTime = datetime.datetime.now()
    self.startTime = datetime.datetime.fromtimestamp(self.endTime.timestamp() - ArgParser.SECONDS_IN_DAY)
    self.last = False
    self.allTime = False
    self.win = ArgParser.RESULT_ALL
    self.sort = ArgParser.SORT_NONE
    self.sortReverse = False
    self.format = ArgParser.FORMAT_PLAIN
    self.outputPath = "output/output.txt"
    self.rh = True
    self.ei = True
    self.raidar = True
    self.longest = False
    self.longerthan = None
    self.withNames = []

    args = []
    for arg in inputArgs:
      args.append(arg.lower())

    index = 0
    while index < len(args):
      if args[index] == "-b" or args[index] == "-boss":
        index += 1
        while index < len(args) and not args[index].startswith("-"):
          newBoss = searchBossName(bossList, args[index])
          for boss in newBoss:
            if boss not in self.bosses:
              self.bosses.append(boss)
          index += 1
      elif args[index] == "-today":
        self.startTime = datetime.datetime.now().replace(hour=0, minute=0, second=0)
        self.endTime = datetime.datetime.now().replace(hour=23, minute=59, second=59)
        index += 1
      elif args[index] == "-yesterday":
        self.startTime = datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp() - ArgParser.SECONDS_IN_DAY).replace(hour=0, minute=0, second=0)
        self.endTime = self.startTime.replace(hour=23, minute=59, second=59)
        index += 1
      elif args[index] == "-week":
        self.startTime = datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp() - ArgParser.SECONDS_IN_DAY * datetime.datetime.now().weekday()).replace(hour=0, minute=0, second=0)
        self.endTime = datetime.datetime.fromtimestamp(self.startTime.timestamp() + ArgParser.SECONDS_IN_DAY * 6).replace(hour=23, minute=59, second=59)
        index += 1
      elif args[index] == "-raidreset":
        self.startTime = datetime.datetime.utcfromtimestamp(datetime.datetime.utcnow().timestamp() - ArgParser.SECONDS_IN_DAY * datetime.datetime.utcnow().weekday()).replace(hour=7, minute=30, second=0)
        self.endTime = datetime.datetime.utcfromtimestamp(self.startTime.timestamp() + ArgParser.SECONDS_IN_DAY * 7).replace(hour=7, minute=29, second=59)
        index += 1
      elif args[index] == "-dailyreset":
        self.startTime = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0)
        self.endTime = datetime.datetime.utcnow().replace(hour=23, minute=59, second=59)
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
            self.startTime = datetime.datetime(year=int(match.group(1)), month=int(match.group(2)), day=int(match.group(3)), hour=0, minute=0, second=0)
          match = re.match("(\\d+)/(\\d+)", args[index])
          if match:
            self.startTime = datetime.datetime.now().replace(month=int(match.group(1)), day=int(match.group(2)), hour=0, minute=0, second=0)
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
            self.endTime = datetime.datetime(year=int(match.group(1)), month=int(match.group(2)), day=int(match.group(3)), hour=23, minute=59, second=59)
          match = re.match("(\\d+)/(\\d+)", args[index])
          if match:
            self.endTime = datetime.datetime.now().replace(month=int(match.group(1)), day=int(match.group(2)), hour=23, minute=59, second=59)
          match = re.match("(\\d+):(\\d+):(\\d+)", args[index])
          if match:
            self.endTime = self.endTime.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=int(match.group(3)))
          match = re.match("(\\d+):(\\d+)", args[index])
          if match:
            self.endTime = self.endTime.replace(hour=int(match.group(1)), minute=int(match.group(2)), second=0)
          index += 1
      elif args[index] == "-past" or args[index] == "-p":
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
        self.win = ArgParser.RESULT_WIN
        index += 1
      elif args[index] == "-fail":
        self.win = ArgParser.RESULT_FAIL
        index += 1
      elif args[index] == "-sort":
        if args[index + 1] == "time":
          self.sort = ArgParser.SORT_TIME
        elif args[index + 1] == "name":
          self.sort = ArgParser.SORT_BOSS_NAME
        elif args[index + 1] == "encounter":
          self.sort = ArgParser.SORT_ENCOUNTER
        else:
          print("Invalid sort type!!")
          sys.exit(0)
        index += 2
      elif args[index] == "-reverse" or args[index] == "-r":
        self.sortReverse = True
        index += 1
      elif args[index] == "-o":
        self.outputPath = inputArgs[index + 1]
        index += 2
      elif args[index] == "-embed":
        self.format = ArgParser.FORMAT_EMBED
        self.title = args[index + 1]
        if index + 2 < len(args) and not args[index + 2].startswith("-"):
          self.description = args[index + 2]
          index += 3
        else:
          self.description = ""
          index += 2
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
      elif args[index] == "-json":
        self.format = ArgParser.FORMAT_JSON
      elif args[index] == "-longest":
        index += 1
        self.longest = True
      elif args[index] == "-longerthan":
        match = re.match("(\\d+)m(\\d+)s", args[index + 1])
        if match:
          self.longerthan = int(match.group(1)) * 60 + int(match.group(2))
        match = re.match("(\\d+)s", args[index + 1])
        if match:
          self.longerthan = int(match.group(1))
        match = re.match("(\\d+)m", args[index + 1])
        if match:
          self.longerthan = int(match.group(1)) * 60
        index += 2
      elif args[index] == "-shorterthan":
        match = re.match("(\\d+)m(\\d+)s", args[index + 1])
        if match:
          self.longerthan = int(match.group(1)) * 60 + int(match.group(2))
        match = re.match("(\\d+)s", args[index + 1])
        if match:
          self.longerthan = int(match.group(1))
        match = re.match("(\\d+)m", args[index + 1])
        if match:
          self.longerthan = int(match.group(1)) * 60
        self.longerthan *= -1
        index += 2
      elif args[index] == "-with":
        index += 1
        while index < len(args) and not args[index].startswith("-"):
          self.withNames.append(inputArgs[index])
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
      combatData = []
      files = []
      for path, dirs, filenames in os.walk(dirpath):
        for f in filenames:
          files.append(os.path.join(path, f))
      for f in files:
        if re.match(".+\\.evtc(\\.zip)?", f):
          filepath = os.path.join(dirpath, f)
          timestamp = os.path.getmtime(filepath)
          if (timestamp >= start and timestamp <= end) or self.allTime:
            fileList.append(filepath)
            if self.win != ArgParser.RESULT_ALL or self.longest == True or self.longerthan != None or len(self.withNames) != 0:
              print("Parsing {} log {}...".format(boss, f))
              evtc = EvtcParser.EvtcLog(filepath)
              combatData.append((filepath, evtc.combatTimeUsed, evtc.playerNames, evtc.cbtResult))
            #elif self.longest == True or self.longerthan != None or len(self.withNames) != 0:
            #  print("Quick parsing {} log {}...".format(boss, f))
            #  evtc = EvtcParser.EvtcLog(filepath, quickParse=True)
            #  combatData.append((filepath, evtc.combatTimeUsed, evtc.playerNames))
                  
      if len(fileList) == 0:
        continue

      if self.win != ArgParser.RESULT_ALL or self.longerthan != None or len(self.withNames) != 0:
        for cbtData in combatData:
          if self.win == ArgParser.RESULT_WIN and not cbtData[3]:
            fileList.remove(cbtData[0])
          elif self.win == ArgParser.RESULT_FAIL and cbtData[3]:
            fileList.remove(cbtData[0])
          elif self.longerthan:
            if self.longerthan > 0:
              if cbtData[1] < (self.longerthan * 1000):
                fileList.remove(cbtData[0])
            else:
              if cbtData[1] > (self.longerthan * -1000):
                fileList.remove(cbtData[0])
          elif len(self.withNames) > 0:
            found = False
            for name in self.withNames:
              for player in cbtData[2]:
                if player == name:
                  found = True
                  break
              if found:
                break
            if not found:
              fileList.remove(cbtData[0])

      if self.last:
        maxtime = 0
        lastlog = None
        for log in fileList:
          if os.path.getmtime(log) > maxtime:
            maxtime = os.path.getmtime(log)
            lastlog = log
        ret.append(lastlog)
        continue
      elif self.longest:
        maxtime = 0
        maxlog = None
        for i in range(0, len(fileList)):
          if combatData[i][2] > maxtime:
            maxtime = combatData[i][2]
            maxlog = fileList[i]
        ret.append(maxlog)
      else:
        for log in fileList:
          ret.append(log)


    if self.win != 0:
      print("\n", end="")

    if self.sort:
      if self.sort == ArgParser.SORT_TIME:
        ret.sort(key=lambda path:os.path.getmtime(path), reverse=self.sortReverse)
      elif self.sort == ArgParser.SORT_BOSS_NAME:
        ret.sort(reverse=self.sortReverse)
      elif self.sort == ArgParser.SORT_ENCOUNTER:
        ret.sort(key=getBossOrder, reverse=self.sortReverse)
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

  for group in bossList["Groups"]:
    if group["Name"].lower() == name:
      return group["Bosses"]

  for boss in bossList["Bosses"]:
    if boss["Name"].lower() == name:
      return [boss["Name"]]
    for alias in boss["Aliases"]:
      if alias.lower() == name:
        return [boss["Name"]]  
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

def findAllRaidarLog(files, token, bossList, timegap=20, maxcount=15, limit=100):
  while True:
    ret = syncFindAllRaidarLog(files, token, bossList, limit=limit)
    if ret["LostCount"] == 0:
      return ret
    if maxcount == 0:
      return ret
    print("Checking Gw2Raidar... remaining {} times({}s), lost {}".format(maxcount, timegap, ret["LostCount"]))
    sleep(timegap)
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
        break
    if not found:
      ret["Results"].append(None)
      ret["LostCount"] += 1
  return ret

def isRaidarAcceptable(log, bossList):
  bossname = log.split(os.path.sep)[len(config["LogPath"].split(os.path.sep))]
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
  raidarlinks = findAllRaidarLog(uploadFiles, config["Gw2RaidarToken"], bossList)

if argParser.format == ArgParser.FORMAT_EMBED:
  output = OrderedDict()
  output["title"] = argParser.title
  output["description"] = argParser.description
  output["color"] = 0xD02906
  output["thumbnail"] = dict([("url", "https://render.guildwars2.com/file/5866630DA52DCB5C423FB81ECF69FD071611E36B/1128644.png")])
  output["fields"] = []
  for index in range(0, len(uploadFiles)):
    pathComponent = uploadFiles[index].split(os.path.sep)
    d = OrderedDict()
    d["name"] = uploadFiles[index].split(os.path.sep)[len(config["LogPath"].split(os.path.sep))]
    value = []
    if argParser.rh:
      value.append("[RaidHeroes]({})".format(raidheroesLinks[index]))
    if argParser.ei:
      value.append("[EliteInsight]({})".format(eliteinsightLinks[index]))
    if argParser.raidar:
      if raidarlinks["Results"][index]:
        value.append("[Raidar]({})".format(raidarlinks["Results"][index]))
      else:
        value.append("~~Raidar~~")
    
    d["value"] = value[0]
    for i in range(1, len(value)):
      d["value"] += " | "
      d["value"] += value[i]
    output["fields"].append(d)
elif argParser.format == ArgParser.FORMAT_JSON:
  output = OrderedDict()
  output["Result"] = []
  for index in range(0, len(uploadFiles)):
    pathComponent = uploadFiles[index].split(os.path.sep)
    d = OrderedDict()
    d["Boss"] = pathComponent[-2]
    d["File"] = pathComponent[-1]
    if argParser.rh:
      d["RaidHeroes"] = raidheroesLinks[index]
    if argParser.ei:
      d["EliteInsight"] = eliteinsightLinks[index]
    if argParser.raidar:
      d["Raidar"] = raidarlinks["Results"][index]
    output["Result"].append(d)
elif argParser.format == ArgParser.FORMAT_PLAIN:
  if len(os.path.dirname(argParser.outputPath)) > 0 and not os.path.exists(os.path.dirname(argParser.outputPath)):
    os.makedirs(os.path.dirname(argParser.outputPath))
  with open(argParser.outputPath, "w") as outfile:
    for index in range(0, len(uploadFiles)):
      pathComponent = uploadFiles[index].split(os.path.sep)
      print("{}: {}".format(pathComponent[-2], pathComponent[-1]), file=outfile)
      if argParser.rh:
        print("  Raid Heroes: ", raidheroesLinks[index], file=outfile)
      if argParser.ei:
        print("  EliteInsight:", eliteinsightLinks[index], file=outfile)
      if argParser.raidar and raidarlinks["Results"][index]:
        print("  Gw2Raidar:   ", raidarlinks["Results"][index], file=outfile)
  print("All complete.")
  sys.exit(0)

try:
  if len(os.path.dirname(argParser.outputPath)) > 0 and not os.path.exists(os.path.dirname(argParser.outputPath)):
    os.makedirs(os.path.dirname(argParser.outputPath))
  with open(argParser.outputPath, "w") as outfile:
    json.dump(output, outfile, indent=2)
except IOError as e:
  print("write output file fail:", str(e))

print("All complete.")