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
    self.bossList = bossList
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
    self.description = ""
    self.embedColor = 0xD02906
    self.raidarWaitTime = 20
    self.raidarRetryCount = 15
    self.raidarSearchCount = 100
    self.notOnlyRaidar = False

    args = []
    for arg in inputArgs:
      args.append(arg.lower())

    index = 0
    while index < len(args):
      if args[index] == "-b" or args[index] == "-boss":
        index += 1
        while index < len(args) and not args[index].startswith("-"):
          newBoss = searchBossName(bossList, args[index])
          if newBoss != None:
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
        if index + 1 >= len(inputArgs) or inputArgs[index + 1].startswith("-"):
          print("Please provide title for embed content.")
          sys.exit(0)
        self.title = inputArgs[index + 1]
        index += 2
        while index < len(args) and not args[index].startswith("-"):
          if args[index].startswith("#"):
            self.embedColor = int(args[index][1:], 16)
          else:
            self.description = inputArgs[index]
          index += 1
      elif args[index] == "-gen":
        index += 1
        self.rh = False
        self.ei = False
        self.raidar = False
        while index < len(args) and not args[index].startswith("-"):
          if args[index] == "rh" or args[index] == "raidheroes":
            self.rh = True
          elif args[index] == "ei" or args[index] == "eliteinsights":
            self.ei = True
          elif args[index] == "rd" or args[index] == "raidar":
            self.raidar = True
          index += 1
        if not (self.rh or self.ei or self.raidar):
          print("No generator selected!!")
          sys.exit(0)
      elif args[index] == "-json":
        self.format = ArgParser.FORMAT_JSON
        index += 1
      elif args[index] == "-longest":
        self.longest = True
        index += 1
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
      elif args[index] == "-raidarwaittime":
        self.raidarWaitTime = int(args[index + 1])
        index += 2
      elif args[index] == "-raidarretrycount":
        self.raidarRetryCount = int(args[index + 1])
        index += 2
      elif args[index] == "-raidarsearchcount":
        self.raidarSearchCount = int(args[index + 1])
        index += 2
      elif args[index] == "-notonlyraidar" or args[index] == "-nord":
        self.notOnlyRaidar = True
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
      lifethreshold = -1
      for b in self.bossList["Bosses"]:
        if b["Name"] == boss:
          if "LifeThreshold" in b:
            lifethreshold = b["LifeThreshold"]
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
            if self.win != ArgParser.RESULT_ALL or self.longest == True or self.longerthan != None:
              print("Parsing {} log {}...".format(boss, f))
              evtc = EvtcParser.EvtcLog(filepath, lifeThreshold=lifethreshold)
              combatData.append(dict([
                ("FilePath", filepath),
                ("ElapsedTime", evtc.combatTimeUsed),
                ("Players", evtc.playerNames),
                ("BossId", evtc.bossId),
                ("Result", evtc.cbtResult),
                ("FullParsed", True),
                ("BossName", boss),
                ("RaidarSupported", True)
              ]))
            else:
              print("Quick Parsing {} log {}...".format(boss, f))
              evtc = EvtcParser.EvtcLog(filepath, quickParse=True)
              combatData.append(dict([
                ("FilePath", filepath),
                ("Players", evtc.playerNames),
                ("BossId", evtc.bossId),
                ("FullParsed", False),
                ("BossName", boss),
                ("RaidarSupported", True)
              ]))
            #elif self.longest == True or self.longerthan != None or len(self.withNames) != 0:
            #  print("Quick parsing {} log {}...".format(boss, f))
            #  evtc = EvtcParser.EvtcLog(filepath, quickParse=True)
            #  combatData.append((filepath, evtc.combatTimeUsed, evtc.playerNames))
                  
      if len(combatData) == 0:
        continue

      if gRaidarBossList:
        for log in combatData:
          log["RaidarSupported"] = False
          for raidarBoss in gRaidarBossList:
            if raidarBoss["id"] == log["BossId"]:
              log["RaidarSupported"] = True
              if log["BossId"] != 16286: #For Xera
                log["BossName"] = raidarBoss["name"]
              break

      if self.win != ArgParser.RESULT_ALL or self.longerthan != None or len(self.withNames) != 0:
        for cbtData in combatData:
          flag = True
          if flag and self.win == ArgParser.RESULT_WIN and not cbtData["Result"]:
            flag = False
          if flag and self.win == ArgParser.RESULT_FAIL and cbtData["Result"]:
            flag = False
          if flag and self.longerthan:
            if self.longerthan > 0:
              if cbtData["ElapsedTime"] < (self.longerthan * 1000):
                flag = False
            else:
              if cbtData["ElapsedTime"] > (self.longerthan * -1000):
                flag = False
          if flag and len(self.withNames) > 0:
            found = False
            for name in self.withNames:
              for player in cbtData["Players"]:
                if player == name:
                  found = True
                  break
              if found:
                break
            if not found:
              flag = False
          if flag and not self.notOnlyRaidar and not cbtData["RaidarSupported"]:
            flag = False
          if flag:
            fileList.append(cbtData)
      else:
        for cbtData in combatData:
          if self.notOnlyRaidar or cbtData["RaidarSupported"]:
            fileList.append(cbtData)
      if len(fileList) == 0:
        continue
      if self.last:
        maxtime = 0
        lastlog = None
        for log in fileList:
          if os.path.getmtime(log["FilePath"]) > maxtime:
            maxtime = os.path.getmtime(log["FilePath"])
            lastlog = log
        ret.append(lastlog)
        continue
      elif self.longest:
        maxtime = 0
        maxlog = None
        for log in fileList:
          if log["ElapsedTime"] > maxtime:
            maxtime = log["ElapsedTime"]
            maxlog = log
        ret.append(maxlog)
      else:
        ret.extend(fileList)

    print("\n", end="")

    if self.sort:
      if self.sort == ArgParser.SORT_TIME:
        ret.sort(key=lambda log:os.path.getmtime(log["FilePath"]), reverse=self.sortReverse)
      elif self.sort == ArgParser.SORT_BOSS_NAME:
        ret.sort(key=lambda log: log["BossName"], reverse=self.sortReverse)
      elif self.sort == ArgParser.SORT_ENCOUNTER:
        ret.sort(key=self.getBossOrder, reverse=self.sortReverse)
    return ret

  def getBossOrder(self, log):
    folderName = log["FilePath"].split(os.path.sep)[pathLevel]
    for index in range(0, len(self.bossList["Bosses"])):
      if self.bossList["Bosses"][index]["Name"] == folderName:
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
  try:
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
        print("Upload Dps.report Error:", response.status_code)
        return False
  except BaseException as e:
    print("Upload Dps.report Error: ", str(e))
    return False

def gw2RaidarGetToken(user, paswd):
  try:
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
  except BaseException as e:
    print("Get Gw2 Raidar Token Error: ", str(e))
    return None

def uploadGw2Raidar(path, token):
  try:
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
        print("Upload Gw2 Raidar Error: ", response.status_code)
        return False
      return True
  except BaseException as e:
    print("Upload Gw2 Raidar Error: ", str(e))
    return False

def getGw2RaiderEncounterList(token, offset=0, limit=100):
  try:
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
      print("Get Raidar Encounter List Error: ", response.status_code)
      return None
  except BaseException as e:
    print("Get Raidar Encounter List Error: ", str(e))
    return None

def findGw2RaidarLog(path, token, limit=100):
  name = os.path.basename(path)
  encounters = getGw2RaiderEncounterList(token, limit=limit)
  for encounter in encounters["results"]:
    if encounter["filename"] == name:
      return "https://www.gw2raidar.com/encounter/" + encounter["url_id"]
  return None

def findAllRaidarLog(files, token, timegap=20, maxcount=15, limit=100):
  while True:
    ret = syncFindAllRaidarLog(files, token, limit=limit)
    if ret["LostCount"] == 0:
      return ret
    if maxcount == 0:
      return ret
    print("Checking Gw2Raidar... remaining {} times({}s), lost {}".format(maxcount, timegap, ret["LostCount"]))
    sleep(timegap)
    maxcount -= 1

def syncFindAllRaidarLog(files, token, limit=100):
  encounters = getGw2RaiderEncounterList(token, limit=limit)
  ret = dict([("LostCount", 0), ("Results", [])])
  for log in files:
    found = False
    if not isRaidarAcceptable(log):
      ret["Results"].append(None)
      continue
    if encounters:
      for encounter in encounters["results"]:
        if os.path.basename(log["FilePath"]) == encounter["filename"]:
          ret["Results"].append("https://www.gw2raidar.com/encounter/" + encounter["url_id"])
          found = True
          break

    if not found:
      ret["Results"].append(None)
      ret["LostCount"] += 1
  return ret

def isRaidarAcceptable(log):
  if not log["RaidarSupported"]:
    return False
  if log["FullParsed"] and log["ElapsedTime"] < (60 * 1000):
    return False
  return True

def getRaidarBossAreas(token):
  try:
    url = "https://www.gw2raidar.com/api/v2/areas"
    headers = {
      "Authorization": "Token " + token
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
      return response.json()
    else:
      print("Get Raidar Boss Areas Error: ", response.status_code)
      return None
  except BaseException as e:
    print("Get Raidar Boss Areas Error", str(e))
    return None

"""
Global Variables
"""
gRaidarBossList = None

"""
  Main Start
"""

if len(sys.argv) < 2:
  print("You may need some argument")
  print("Please check https://github.com/paddycup1/Gw2DpsLogUploader/blob/master/README.md")
  sys.exit(0)

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
  if config["Gw2RaidarToken"] == None:
    print("get token fail, please check your id/password.")
    sys.exit(0)
  with open("Config.json", "w") as configFile:
    json.dump(config, configFile, indent=2)
  print("get Raidar token success.")
  sys.exit(0)

print("Get Boss List from Raidar...")
ret = getRaidarBossAreas(config["Gw2RaidarToken"])
if ret == None:
  print("Retry after 1s...")
  ret = getRaidarBossAreas(config["Gw2RaidarToken"])
if ret == None:
  print("Can't get Raidar supported boss list, consider all boss is supported")
else:
  gRaidarBossList = ret["results"]

try:
  with open("BossList.json", "r") as bosslistfile:
    bossList = json.load(bosslistfile)
except BaseException as e:
  print("load boss list fail:", str(e))
  sys.exit(0)

if "LogPath" not in config:
  print("Can't find arcdps log path in config file! (field name: LogPath)")
  sys.exit(0)

pathLevel = len(config["LogPath"].split(os.path.sep))
argParser = ArgParser(sys.argv, bossList)
uploadFiles = argParser.filterLogs(config["LogPath"])

if argParser.raidar:
  for log in uploadFiles:
    if isRaidarAcceptable(log):
      Status = uploadGw2Raidar(log["FilePath"], config["Gw2RaidarToken"])
      if not Status:
        print("Retry after 1s...")
        sleep(1)
        Status = uploadGw2Raidar(log["FilePath"], config["Gw2RaidarToken"])
      if not Status:
        log["RaidarSupported"] = False
    else:
      print("Raidar doesn't support", log["FilePath"])
  print("\n", end="")

for log in uploadFiles:
  if argParser.ei:
    link = uploadDpsReport(log["FilePath"], gen="ei")
    if not link:
      print("Retry after 1s...")
      sleep(1)
      link = uploadDpsReport(log["FilePath"], gen="ei")
    log["EliteInsightsLink"] = link
  if argParser.rh:
    link = uploadDpsReport(log["FilePath"], gen="rh")
    if not link:
      print("Retry after 1s...")
      sleep(1)
      link = uploadDpsReport(log["FilePath"], gen="rh")
    log["RaidHeroesLink"] = link
  
if argParser.raidar:
  raidarlinks = findAllRaidarLog(uploadFiles, config["Gw2RaidarToken"],
    timegap=argParser.raidarWaitTime,
    maxcount=argParser.raidarRetryCount,
    limit=argParser.raidarSearchCount)

if argParser.format == ArgParser.FORMAT_EMBED:
  output = OrderedDict()
  output["title"] = argParser.title
  output["description"] = argParser.description
  output["color"] = argParser.embedColor
  output["thumbnail"] = dict([("url", "https://render.guildwars2.com/file/5866630DA52DCB5C423FB81ECF69FD071611E36B/1128644.png")])
  output["fields"] = []
  for index in range(0, len(uploadFiles)):
    pathComponent = uploadFiles[index]["FilePath"].split(os.path.sep)
    d = OrderedDict()
    d["name"] = uploadFiles[index]["BossName"]
    value = []
    if argParser.ei:
      if uploadFiles[index]["EliteInsightsLink"]:
        value.append("[EliteInsight]({})".format(uploadFiles[index]["EliteInsightsLink"]))
      else:
        value.append("~~EliteInsight~~")
    if argParser.rh:
      if uploadFiles[index]["RaidHeroesLink"]:
        value.append("[RaidHeroes]({})".format(uploadFiles[index]["RaidHeroesLink"]))
      else:
        value.append("~~RaidHeroes~~")
    if argParser.raidar:
      if isRaidarAcceptable(uploadFiles[index]):
        if raidarlinks["Results"][index]:
          value.append("[Raidar]({})".format(raidarlinks["Results"][index]))
        else:
          value.append("~~Raidar~~")
          print("no result for", uploadFiles[index])
    
    d["value"] = value[0]
    for i in range(1, len(value)):
      d["value"] += " | "
      d["value"] += value[i]
    output["fields"].append(d)
elif argParser.format == ArgParser.FORMAT_JSON:
  output = OrderedDict()
  output["Result"] = []
  for index in range(0, len(uploadFiles)):
    pathComponent = uploadFiles[index]["FilePath"].split(os.path.sep)
    d = OrderedDict()
    d["Boss"] = uploadFiles[index]["BossName"]
    d["File"] = uploadFiles[index]["FilePath"]
    if argParser.ei:
      if uploadFiles[index]["EliteInsightsLink"]:
        d["EliteInsight"] = uploadFiles[index]["EliteInsightsLink"]
      else:
        d["EliteInsight"] = "Upload fail"
    if argParser.rh:
      if uploadFiles[index]["RaidHeroesLink"]:
        d["RaidHeroes"] = uploadFiles[index]["RaidHeroesLink"]
      else:
        d["RaidHeroes"] = "Upload fail"
    if argParser.raidar:
      if isRaidarAcceptable(uploadFiles[index]):
        d["Raidar"] = raidarlinks["Results"][index]
      else:
        d["Raidar"] = "Not supported."
    output["Result"].append(d)
elif argParser.format == ArgParser.FORMAT_PLAIN:
  if len(os.path.dirname(argParser.outputPath)) > 0 and not os.path.exists(os.path.dirname(argParser.outputPath)):
    os.makedirs(os.path.dirname(argParser.outputPath))
  with open(argParser.outputPath, "w") as outfile:
    for index in range(0, len(uploadFiles)):
      pathComponent = uploadFiles[index]["FilePath"].split(os.path.sep)
      print("{}: {}".format(uploadFiles[index]["BossName"], pathComponent[-1]), file=outfile)
      if argParser.ei:
        if uploadFiles[index]["EliteInsightsLink"]:
          print("  EliteInsight:", uploadFiles[index]["EliteInsightsLink"], file=outfile)
        else:
          print("  EliteInsight: Upload fail", file=outfile)
      if argParser.rh:
        if uploadFiles[index]["RaidHeroesLink"]:
          print("  Raid Heroes: ", uploadFiles[index]["RaidHeroesLink"], file=outfile)
        else:
          print("  Raid Heroes:  Upload fail", file=outfile)
      if argParser.raidar:
        if not isRaidarAcceptable(uploadFiles[index]):
          print("  Gw2Raidar:    Unsupported", file=outfile)
        elif raidarlinks["Results"][index]:
          print("  Gw2Raidar:   ", raidarlinks["Results"][index], file=outfile)
        else:
          print("  Gw2Raidar:    Upload fail", file=outfile)
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
