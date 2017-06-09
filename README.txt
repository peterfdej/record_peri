RECORD_PERI

Record_peri.py is a simple Python scipt for recording Periscope live broadcasts of users stored in a csv.
Requirements:
- Python 3
	https://www.python.org/
- ffmpeg
	https://ffmpeg.org/

For users in the csv you need the Periscope or Twiter account name.
e.g. @abc123 is user abc123:p.
p = Periscope account name
t = Twitter account name

Because ffmpeg can't stop decent with a script, the mkv isn't closed correctly.
At the end the mkv is converted to a good working mp4 file (parm).
Usage: 	python record_peri.py (non converting to mp4)
	python record_peri.py -c (Recordings will be converted to mp4 after ending broadcast)
