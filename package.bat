rmdir /s/q .\dist
rmdir /s/q .\build
rmdir /s/q .\Gw2DpsLogUploader
pyinstaller -F .\DpsLogUploader.py
pyinstaller -F .\EmbedHelper.py
mkdir .\Gw2DpsLogUploader
move .\dist.\DpsLogUploader.exe .\Gw2DpsLogUploader\DpsLogUploader.exe 
move .\dist.\EmbedHelper.exe .\Gw2DpsLogUploader\EmbedHelper.exe 
copy .\BossList.json .\Gw2DpsLogUploader\BossList.json 