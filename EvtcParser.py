from collections import OrderedDict
import zipfile
import json
import sys
import os

class Iff:
  IFF_FRIEND   = 0
  IFF_FOE      = 1
  IFF_UNKNOWN  = 2 # or uncertain

class CbtResult:
  CBTR_NORMAL      = 0 # good physical hit
  CBTR_CRIT        = 1 # physical hit was crit
  CBTR_GLANCE      = 2 # physical hit was glance
  CBTR_BLOCK       = 3 # physical hit was blocked eg. mesmer shield 4
  CBTR_EVADE       = 4 # physical hit was evaded, eg. dodge or mesmer sword 2
  CBTR_INTERRUPT   = 5 # physical hit interrupted something
  CBTR_ABSORB      = 6 # physical hit was "invlun" or absorbed eg. guardian elite
  CBTR_BLIND       = 7 # physical hit missed
  CBTR_KILLINGBLOW = 8 # hit was killing hit
  CBTR_DOWNED      = 9 # hit was downing hit
 
class CbtActivation:
  ACTV_NONE          = 0 # not used - not this kind of event
  ACTV_NORMAL        = 1 # activation without quickness
  ACTV_QUICKNESS     = 2 # activation with quickness
  ACTV_CANCEL_FIRE   = 3 # cancel with reaching channel time
  ACTV_CANCEL_CANCEL = 4 # cancel without reaching channel time
  ACTV_RESET         = 5 # animation completed fully

class CbtStateChange:
  CBTS_NONE            = 0  # not used - not this kind of event
  CBTS_ENTERCOMBAT     = 1  # src_agent entered combat, dst_agent is subgroup
  CBTS_EXITCOMBAT      = 2  # src_agent left combat
  CBTS_CHANGEUP        = 3  # src_agent is now alive
  CBTS_CHANGEDEAD      = 4  # src_agent is now dead
  CBTS_CHANGEDOWN      = 5  # src_agent is now downed
  CBTS_SPAWN           = 6  # src_agent is now in game tracking range
  CBTS_DESPAWN         = 7  # src_agent is no longer being tracked
  CBTS_HEALTHUPDATE    = 8  # src_agent has reached a health marker. dst_agent = percent * 10000 (eg. 99.5% will be 9950)
  CBTS_LOGSTART        = 9  # log start. value = server unix timestamp **uint32**. buff_dmg = local unix timestamp. src_agent = 0x637261 (arcdps id)
  CBTS_LOGEND          = 10 # log end. value = server unix timestamp **uint32**. buff_dmg = local unix timestamp. src_agent = 0x637261 (arcdps id)
  CBTS_WEAPSWAP        = 11 # src_agent swapped weapon set. dst_agent = current set id (0/1 water, 4/5 land)
  CBTS_MAXHEALTHUPDATE = 12 # src_agent has had it's maximum health changed. dst_agent = new max health
  CBTS_POINTOFVIEW     = 13 # src_agent will be agent of "recording" player
  CBTS_LANGUAGE        = 14 # src_agent will be text language
  CBTS_GWBUILD         = 15 # src_agent will be game build
  CBTS_SHARDID         = 16 # src_agent will be sever shard id
  CBTS_REWARD          = 17 # src_agent is self, dst_agent is reward id, value is reward type. these are the wiggly boxes that you get
  CBTS_BUFFINITIAL     = 18 # combat event that will appear once per buff per agent on logging start (zero duration, buff==18)
  CBTS_POSITION        = 19 # src_agent changed, cast float* p = (float*)&dst_agent, access as x/y/z (float[3])
  CBTS_VELOCITY        = 20 # src_agent changed, cast float* v = (float*)&dst_agent, access as x/y/z (float[3])
  CBTS_FACING          = 21 # src_agent changed, cast float* f = (float*)&dst_agent, access as x/y (float[2])
  CBTS_TEAMCHANGE      = 22 # src_agent change, dst_agent new team id  

class CbtBuffRemove:
  CBTB_NONE   = 0 # not used - not this kind of event
  CBTB_ALL    = 2 # last/all stacks removed (sent by server)
  CBTB_SINGLE = 3 # single stack removed (sent by server). will happen for each stack on cleanse
  CBTB_MANUAL = 4 # single stack removed (auto by arc on ooc or all stack, ignore for strip/cleanse calc, use for in/out volume)
 
class CbtCustomSkill:
  CSK_RESURRECT = 1066, # not custom but important and unnamed
  CSK_BANDAGE   = 1175, # personal healing only
  CSK_DODGE     = 65001 # will occur in is_activation==normal event

class GwLanguage:
  GWL_ENG = 0,
  GWL_FRE = 2,
  GWL_GEM = 3,
  GWL_SPA = 4,

class Agent:
  LEN = 96
  def __init__(self, bytes):
    self.addr          = int.from_bytes(bytes[0:8], byteorder="little", signed=False)
    self.porf          = int.from_bytes(bytes[8:12], byteorder="little", signed=False)
    self.isElite       = int.from_bytes(bytes[12:16], byteorder="little", signed=False)
    self.toughness     = int.from_bytes(bytes[16:18], byteorder="little", signed=False)
    self.concentration = int.from_bytes(bytes[18:20], byteorder="little", signed=False)
    self.healing       = int.from_bytes(bytes[20:22], byteorder="little", signed=False)
    self.pad1          = int.from_bytes(bytes[22:24], byteorder="little", signed=False)
    self.condition     = int.from_bytes(bytes[24:26], byteorder="little", signed=False)
    self.pad2          = int.from_bytes(bytes[26:28], byteorder="little", signed=False)
    names = bytes[28:92].decode("utf8").split("\x00")
    self.name = names[0]
    if self.isPlayer:
      self.displayName = names[1][1:]
      self.subgroup = int(names[2])


  @property
  def isgadget(self):
    if self.isElite != 0xFFFFFFFF:
      return False 
    if self.porf >> 8 != 0xFFFF:
      return False
    return True
  
  @property
  def isNpc(self):
    if self.isElite != 0xFFFFFFFF:
      return False 
    if self.porf >> 8 == 0xFFFF:
      return False
    return True

  @property
  def isPlayer(self):
    if self.isElite == 0xFFFFFFFF:
      return False 
    return True
  
  @property
  def specialID(self):
    return self.porf & 0xFFFF


class Skill:
  LEN = 68
  def __init__(self, bytes):
    self.id = int.from_bytes(bytes[0:4], byteorder="little", signed=False)
    self.name = bytes[4:68].decode("utf8").split("\x00")[0]


class CombatEvent0:
  LEN = 8 * 3 + 4 * 2 + 2 * 5 + 22
  def __init__(self, bytes):
    self.time                  = int.from_bytes(bytes[0:8], byteorder="little", signed=False)    #8 byte
    self.src_agent             = int.from_bytes(bytes[8:16], byteorder="little", signed=False)   #8 byte
    self.dst_agent             = int.from_bytes(bytes[16:24], byteorder="little", signed=False)  #8 byte
    self.value                 = int.from_bytes(bytes[24:28], byteorder="little", signed=False)  #4 byte
    self.buff_dmg              = int.from_bytes(bytes[28:32], byteorder="little", signed=False)  #4 byte
    self.overstack_value       = int.from_bytes(bytes[32:34], byteorder="little", signed=False)  #2 byte
    self.skillid               = int.from_bytes(bytes[34:36], byteorder="little", signed=False)  #2 byte
    self.src_instid            = int.from_bytes(bytes[36:38], byteorder="little", signed=False)  #2 byte
    self.dst_instid            = int.from_bytes(bytes[38:40], byteorder="little", signed=False)  #2 byte
    self.src_master_instid     = int.from_bytes(bytes[40:42], byteorder="little", signed=False)  #2 byte
    self.iss_offset            = int(bytes[42])
    self.iss_offset_target     = int(bytes[43])
    self.iss_bd_offset         = int(bytes[44])
    self.iss_bd_offset_target  = int(bytes[45])
    self.iss_alt_offset        = int(bytes[46])
    self.iss_alt_offset_target = int(bytes[47])
    self.skar                  = int(bytes[48])
    self.skar_alt              = int(bytes[49])
    self.skar_use_alt          = int(bytes[50])
    self.iff                   = int(bytes[51])
    self.buff                  = int(bytes[52])
    self.result                = int(bytes[53])
    self.is_activation         = int(bytes[54])
    self.is_buffremove         = int(bytes[55])
    self.is_ninety             = int(bytes[56])
    self.is_fifty              = int(bytes[57])
    self.is_moving             = int(bytes[58])
    self.is_statechange        = int(bytes[59])
    self.is_flanking           = int(bytes[60])
    self.is_shields            = int(bytes[61])
    self.is_offcycle           = int(bytes[62])
    self.pad64                 = int(bytes[63])

class CombatEvent1:
  LEN = 8 * 3 + 4 * 4 + 2 * 4 + 16
  def __init__(self, bytes):
    self.time = int.from_bytes(bytes[0:8], byteorder="little", signed=False)                 #8 byte
    self.src_agent         = int.from_bytes(bytes[8:16], byteorder="little", signed=False)   #8 byte
    self.dst_agent         = int.from_bytes(bytes[16:24], byteorder="little", signed=False)  #8 byte
    self.value             = int.from_bytes(bytes[24:28], byteorder="little", signed=True)   #4 byte
    self.buff_dmg          = int.from_bytes(bytes[28:32], byteorder="little", signed=True)   #4 byte
    self.overstack_value   = int.from_bytes(bytes[32:36], byteorder="little", signed=False)  #4 byte
    self.skillid           = int.from_bytes(bytes[36:40], byteorder="little", signed=False)  #4 byte
    self.src_instid        = int.from_bytes(bytes[40:42], byteorder="little", signed=False)  #2 byte
    self.dst_instid        = int.from_bytes(bytes[42:44], byteorder="little", signed=False)  #2 byte
    self.src_master_instid = int.from_bytes(bytes[44:46], byteorder="little", signed=False)  #2 byte
    self.dst_master_instid = int.from_bytes(bytes[46:48], byteorder="little", signed=False)  #2 byte
    self.iff               = int(bytes[48])
    self.buff              = int(bytes[49])
    self.result            = int(bytes[50])
    self.is_activation     = int(bytes[51])
    self.is_buffremove     = int(bytes[52])
    self.is_ninety         = int(bytes[53])
    self.is_fifty          = int(bytes[54])
    self.is_moving         = int(bytes[55])
    self.is_statechange    = int(bytes[56])
    self.is_flanking       = int(bytes[57])
    self.is_shields        = int(bytes[58])
    self.is_offcycle       = int(bytes[59])
    self.pad61             = int(bytes[60])
    self.pad62             = int(bytes[61])
    self.pad63             = int(bytes[62])
    self.pad63             = int(bytes[63])


class EvtcLog:
  def __init__(self, filepath, quickParse=False, lifeThreshold = 50):
    if zipfile.is_zipfile(filepath):
      with zipfile.ZipFile(filepath) as zipFile:
        namelist = zipFile.namelist()
        for n in namelist:
          if n.endswith(".evtc") or n.endswith(".evtc.tmp"):
            filename = n
        try:
          filename
        except:
          raise BaseException("can't find evtc file in zip file {}".format(filepath))
        with zipFile.open(filename) as evtcFile:
          self.parseEvtc(evtcFile, lifeThreshold, zipFile.infolist()[0].file_size, quickParse)
    else:
      with open(filepath, "rb") as evtcFile:
        self.parseEvtc(evtcFile, lifeThreshold, os.path.getsize(filepath), quickParse)
  
  def parseEvtc(self, evtc, lifeThreshold, size, quickParse):
    if evtc.read(4).decode("ascii") != "EVTC":
      raise BaseException("Input file isn't evtc file or standard zip.")
    self.dateText = evtc.read(8).decode("ascii")
    self.revision = evtc.read(1)[0]
    self.bossId = int.from_bytes(evtc.read(2), byteorder="little", signed=False)
    #evtc.seek(16)
    evtc.read(1)

    if self.bossId == 16246:   #For Xera
      self.bossId = 16286

    self.cbtResult = False
    self.playerNames = []
    self.agentCount = int.from_bytes(evtc.read(4), byteorder="little", signed=False)
    self.agents = []
    self.bossName = ""
    playersAddr = []
    bossAddr = None
    for i in range(0, self.agentCount):
      agent = Agent(evtc.read(Agent.LEN))
      self.agents.append(agent)
      if agent.isPlayer:
        playersAddr.append(agent.addr)
        self.playerNames.append(agent.displayName)
        self.playerNames.append(agent.name)
      else:
        if bossAddr == None and agent.specialID == self.bossId:
          bossAddr = agent.addr
          self.bossName = agent.name

    self.skillCount = int.from_bytes(evtc.read(4), byteorder="little", signed=False)
    self.skills = []
    for i in range(0, self.skillCount):
      self.skills.append(Skill(evtc.read(Skill.LEN)))
    if self.revision == 0:
      CombatEvent = CombatEvent0
    else:
      CombatEvent = CombatEvent1
    if not quickParse:
      self.combatEvents = []
      data = evtc.read(CombatEvent.LEN)
      while len(data) == CombatEvent.LEN:
        evtcLog = CombatEvent(data)
        if not self.cbtResult and evtcLog.src_agent == bossAddr:
          if evtcLog.is_statechange == CbtStateChange.CBTS_CHANGEDEAD:
            self.cbtResult = True
          elif lifeThreshold >= 0 and evtcLog.is_statechange == CbtStateChange.CBTS_HEALTHUPDATE and evtcLog.dst_agent < lifeThreshold:
            self.cbtResult = True
        self.combatEvents.append(evtcLog)
        data = evtc.read(CombatEvent.LEN)

      self.combatTimeUsed = self.combatEvents[-1].time - self.combatEvents[0].time
    #seek is broken in python 3.7
    #else:
    #  data = evtc.read(CombatEvent.LEN)
    #  firstLog = CombatEvent(data)
    #  evtc.seek(size - CombatEvent.LEN)
    #  data = evtc.read(CombatEvent.LEN)
    #  lastLog = CombatEvent(data)
    #  self.combatTimeUsed = lastLog.time - firstLog.time

if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(sys.argv[0], "EvtcFile [-json]: dump evtc file.")
    print(sys.argv[0], "SuccessEvtcFile -config: config specific boss in BossList by given log.")
    sys.exit(0)
  log = EvtcLog(sys.argv[1])
  lastLifeChange = -1
  bossAddr = 0
  isDead = False
  for agent in log.agents:
    if not agent.isPlayer:
      if agent.specialID == log.bossId:
        bossAddr = agent.addr
        break
  for event in log.combatEvents:
    if event.is_statechange == CbtStateChange.CBTS_HEALTHUPDATE and event.src_agent == bossAddr:
      lastLifeChange = event.dst_agent
    if event.is_statechange == CbtStateChange.CBTS_CHANGEDEAD and event.src_agent == bossAddr:
      isDead = True
  if len(sys.argv) > 2 and sys.argv[2] == "-config":
    with open("BossList.json", "r") as listFile:
      bossList = json.load(listFile)
    for boss in bossList["Bosses"]:
      if boss["Name"] == log.bossName:
        if isDead:
          if "LifeThreshold" in boss:
            del boss["LifeThreshold"]
        else:
          boss["LifeThreshold"] = lastLifeChange + 30
        with open("BossList.json", "w") as listFile:
          json.dump(bossList, listFile, indent=2)
        sys.exit(0)
  else:
    if len(sys.argv) > 2 and sys.argv[2] == "-json":
      fileName = "EvtcLog.json"
    else:
      fileName = "EvtcLog.txt"
    with open(fileName, "w", encoding="utf8") as output:
      if len(sys.argv) > 2 and sys.argv[2] == "-json":
        outputDict = OrderedDict()
        outputDict["BossId"] = log.bossId
        outputDict["LastLifeChange"] = lastLifeChange
        outputDict["IsBossDead"] = isDead
        outputDict["Agents"] = []
        for agents in log.agents:
          outputDict["Agents"].append(agents.__dict__)
        json.dump(outputDict, output, indent=2)
        outputDict["Skills"] = []
        for skill in log.skills:
          outputDict["Skills"].append(skill.__dict__)
        outputDict["Events"] = []
        for event in log.combatEvents:
          outputDict["Events"].append(event.__dict__)
        json.dump(outputDict, output, indent=2)
      else:
        print("BossId:", log.bossId, file=output)
        print("Last Life Change:", lastLifeChange, file=output)
        print("Is Boss Dead:", isDead, file=output)
        print("Agents:", file=output)
        for agent in log.agents:
          print(" ", agent.name, end=" ", file=output)
          if agent.isPlayer:
            print(agent.displayName, agent.addr, file=output)
          else:
            print(agent.specialID, agent.addr, file=output)            
        print("Events:", file=output)
        for event in log.combatEvents:
          if event.is_statechange == CbtStateChange.CBTS_HEALTHUPDATE and event.src_agent == bossAddr:        
            lastLifeChange = event.dst_agent
          print("  Src:", event.src_agent, "Dst:", event.dst_agent, "StateChange:", event.is_statechange, file=output)
      
