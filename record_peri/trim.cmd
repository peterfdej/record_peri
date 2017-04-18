:: Windows script. Examples cuts first 5 minutes and part after 10 minutes from file.
ffmpeg -i input.mp4 -ss 00:05:00 -to 00:10:00 -async 1 output.mp4