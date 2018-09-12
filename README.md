# GW2 DPS Log Uploader

A command line tool used to pick specific log and upload to [Gw2Raidar](https://www.gw2raidar.com) and [dps.report](https://dps.report/).

## Download

[Releases Page](https://github.com/paddycup1/Gw2DpsLogUploader/releases)

## Initialize

Run `DpsLogUploader.exe -init username password`  
username and password is used to get account token from Gw2Raidar.  
This command will generate `Config.json` in current directory, please open it with any text editor, update your acrdps log path into `LogPath` field.  
You should seperate your path with double back slash (`\\`) because I use json format. ex: `C:\\Users\\username\\Documents\\Guild Wars 2\\addons\\arcdps\\arcdps.cbtlogs`  
The field `Gw2RaidarToken` should be automatically filled by `-init` command.  
The field `DiscordBotToken` is optional, this is used by `EmbedHelper.exe` to print embed report to discord channel. It can be any value or deleted if `EmbedHelper.exe` doesn't used.

## Usage
`DpsLogUploader.exe [arguments]`  

There are two things need to give with arguments: which bosses and which time section  
Select bosses with `-boss` command.  
Select time section with `-starttime` + `-endtime` combination or `-past`, `-today`, `-yesterday`, `-alltime`.

## Supported Arguments

### Select boss
* `-boss name1 name2 ...` (`-b`) : Select bosses names need to be uploaded. Use names or alias defined in `BossList.json`.Bosses, or use group name defined in `BossList.json`.Groups to select multiple boss.  

### Select time section
* `-starttime [yy/]mm/dd [h:m[:s]]` (`-start`) : Select start point of target time section.
* `-endtime [yy/]mm/dd [h:m[:s]]` (`-end`) : Select end point of target time section.
* `-past 5h` or `-past 8d` (`-p`) : Select target time section from now back to given duration.
* `-today` : Select target time section from current day 00:00:00 to 23:59:59.
* `-yesterday` : Select target time section from yesterday day 00:00:00 to 23:59:59.
* `-raidreset` : Select target time section to current RAID reset.
* `-dailyreset` : Select target time section to current Daily reset.
* `-week` : Select target time section from current week Monday 00:00:00 to next Sunday 23:59:59.
* `-alltime` : Ignore time limit.

### Miscellaneous
* `-longest` : Only upload the longest log in each boss after filtered by other arguments, can't be used with `-last`.
* `-longerthan 5m[6s]` : Select the logs that fight time longer than given time.
* `-shorterthan 5m[6s]` : Select the logs that fight time shorter than given time.
* `-with name1 name2...` : Select the logs that contain given player name(can be either character name or display name).
* `-win` and `-fail`: Select encounter result to be upload, the tool will upload both if not selected. 
  * Note that above command will let the tool entirely parse every log which in selected boss and time section, **this will significantly increase the time cost**.
* `-last` : Only upload the last log in each boss after filtered by other arguments, can't be used with `-longest`.
* `-sort type` : Sort output result by given type, type can be `name`, `time` or `encounter`.
* `-reverse` (`-r`) : Reverse the sort result if `-sort` arguments is given.
* `-gen [rh] [ei] [raidar]` : Select upload target, default is all select.
  * `rh` is Raid Heroes host by dps.report
  * `ei` is Elite Insight host by dps.report
  * `raidar` or can be `rd` for short, is Gw2Raidar
* `-o filename` : Output result to given file name. Default is `output/output.txt` if not given.
* `-raidarlogin username password` : Retrieve account token from Gw2Raidar API. The token is needed for upload to Gw2Raidar.
* `-init username password` : Generate default config file and retrieve Gw2Raidar account token by given username and password.
* `-json` : Gererate json format output.
* `-embed title [description]` : Generate discord embed format output, you can use `EmbedHelper.exe` in this repository to print embed to your discord server.  
![](https://i.imgur.com/8I4NB5D.png)

## Example

#### Upload today's fotm log
`DpsLogUploader.exe -b fotms -past 1d -win`

#### Upload all success raid log in August and sort result with fight time
`DpsLogUploader.exe -b raids -start 2018/8/1 -end 2018/8/31 -win -sort time`

#### Upload all raid wing 4 log to Gw2Raidar and Raid Heroes
`DpsLogUploader.exe -b W4 -alltime -gen rd rh`

## Explation of BossList.json
You can customer boss alias by edit this file:
```json
{
  "Bosses": [
    {
      "Name": "The exactly Boss name in arcdps log folder, the tool will use this name to open log. This name can be used in -boss argument",
      "Aliases": [
        "Any aliases you want, any name defined here can be used in -boss arguments"
      ],
      "Gw2RaidarAcceptable": true,
      "This is comment for Gw2RaidarAcceptable": "If the boss can't be analyzed by Gw2Raidar, Gw2RaidarAcceptable field should set to false. Or the upload tool will try to find this boss in Gw2Raidar encounter list after upload complete."
    }
  ],
  "Groups": [
    {
      "Name": "Any name you want, this name is used to refer group in -boss arguments",
      "Bosses": [
        "Name field of boss you want to add into this group. Don't use alias here"
      ]
    }
  ]
}
```

# Embed Helper

A very very simple discord bot only used to print custome embed structure to discord.

## Initialize

Open `Config.json` generate by `DpsLogUploader.exe -init username password` or make it by your self. The only one requirement is `DiscordBotToken` field in this file.  
If you haven't  created a discord bot ↓↓↓  
1. Login [discord developer page](https://discordapp.com/developers/applications/)
2. Create your own application.
3. Create a bot in application manage page.
4. Copy bot token in bot tab into `DiscordBotToken` field in `Config.json`.
5. Invite your bot in your server by OAuth2 URL generated by OAuth2 tab in application manage page.

## Usage
Activate bot by command `EmbedHelper.exe`  
In discord channel, send `!embed ` followed by entire json embed code.  
![](https://i.imgur.com/sBiGXOl.png)  
The bot will delete this message immediately then send a embed message.  
![](https://i.imgur.com/ttH0O3E.png)  

If your embed code is too big to send to discord, you can send file name with command:  
`!embed_file filename`  
The bot will read file from its current folder, parse it as embed json code, then send embed message to the channel.

You can make your embed code at [Leovoel's Embed Visualizer](https://leovoel.github.io/embed-visualizer/).

P.S. If `author` field in embed code is not given, the bot will use the one who send `!embed` command's avatar and display name with author.