:: Windows script. Concat all mp4 file in folder (aalphabetic order) into 1 new file
(for %%i in (*.mp4) do @echo file '%%i') > list.txt
ffmpeg -f concat -i list.txt -c copy output.mp4
del list.txt