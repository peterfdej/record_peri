:: Windows script. All mkv files in folder will be converted to mp4
for %%A in (*.mkv) do ffmpeg.exe -i %%A -y  %%~nA.mp4
