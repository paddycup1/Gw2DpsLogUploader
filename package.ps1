rm .\dist -r -fo
rm .\build -r -fo
rm .\Gw2DpsLogUploader -r -fo
pyinstaller -F .\DpsLogUploader.py
pyinstaller -F .\EmbedHelper.py
pyinstaller -F .\EvtcParser.py
mkdir .\Gw2DpsLogUploader
mv .\dist\DpsLogUploader.exe .\Gw2DpsLogUploader\DpsLogUploader.exe 
mv .\dist\EmbedHelper.exe .\Gw2DpsLogUploader\EmbedHelper.exe 
mv .\dist\EvtcParser.exe .\Gw2DpsLogUploader\EvtcParser.exe 
copy .\BossList.json .\Gw2DpsLogUploader\BossList.json 
Compress-Archive .\Gw2DpsLogUploader Gw2DpsLogUploader.zip -Force
mv .\Gw2DpsLogUploader.zip .\Gw2DpsLogUploader