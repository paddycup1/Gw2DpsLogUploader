rmdir /s/q .\dist
rmdir /s/q .\build
pyinstaller .\DpsLogUploader.py
pyinstaller .\EmbedHelper.py
mkdir .\package
move .\dist.\DpsLogUploader\DpsLogUploader.exe .\package\DpsLogUploader.exe 
move .\dist.\EmbedHelper\EmbedHelper.exe .\package\EmbedHelper.exe 
move .\BossList.json .\package\BossList.json 