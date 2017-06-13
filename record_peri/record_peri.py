#The MIT License (MIT)
#
#Copyright (c) 2017 Peterfdej
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in
#all copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#THE SOFTWARE.

# Record_peri.py is a simple Python script for recording live Periscope scopes of users stored in a csv file.
# Put record_peri.py and the cvs file in the same directory. Recordings will also be stored in that directory.
# Advice: max 10 users in csv.
# You can run record-peri.py multiple times, when you create multiple directories, each with his own
# record_peri.py and csv file.
# It is possible te edit the csv file while record_peri.py is running.
# Use Notepad++ for editing.
# Format csv: abc123:p,johndoe:p,xyzxx:t
# p = Periscope account name (user uses Pericope to stream)
# t = Twitter account name (user uses Twitter to stream)
#
# Requirements:	- Python 3
#				- ffmpeg
#
# Usage: 	python record_peri.py (non converting to mp4)
#			python record_peri.py -c (Recordings will be converted to mp4 after ending broadcast)

from bs4 import BeautifulSoup
import sys, time, os, getopt, csv
import os.path
import subprocess
import json
import urllib.request, urllib.error

PERISCOPE_URL = 'https://www.pscp.tv/'
TWITTER_URL = 'https://twitter.com/'
HLSURL1 = {
	'https://prod-video-eu-central-1.pscp.tv/':'/live/eu-central-1/playlist.m3u8',
	'https://prod-video-eu-west-1.pscp.tv/':'/live/eu-west-1/playlist.m3u8',
	'https://prod-video-ap-northeast-1.pscp.tv/':'/live/ap-northeast-1/playlist.m3u8',
	'https://prod-video-ap-southeast-1.pscp.tv/':'/live/ap-southeast-1/playlist.m3u8',
	'https://prod-video-us-west-1.pscp.tv/':'/live/us-west-1/playlist.m3u8',
	'https://prod-video-us-east-1.pscp.tv/':'/live/us-east-1/hlsproducer.m3u8',
	'https://prod-video-us-east-1.pscp.tv/':'/live/us-east-1/playlist.m3u8',
	'https://prod-video-sa-east-1.pscp.tv/':'/live/sa-east-1/playlist.m3u8',
	'https://prod-video-eu-central-2.pscp.tv/':'/live/eu-central-2/playlist.m3u8',
	'https://prod-video-eu-west-2.pscp.tv/':'/live/eu-west-2/playlist.m3u8',
	'https://prod-video-ap-northeast-2.pscp.tv/':'/live/ap-northeast-2/playlist.m3u8',
	'https://prod-video-ap-southeast-2.pscp.tv/':'/live/ap-southeast-2/playlist.m3u8',
	'https://prod-video-us-west-2.pscp.tv/':'/live/us-west-2/playlist.m3u8',
	'https://prod-video-us-east-2.pscp.tv/':'/live/us-east-2/playlist.m3u8',
	'https://prod-video-sa-east-2.pscp.tv/':'/live/sa-east-2/playlist.m3u8'
	}
broadcastdict = {}
deleteuser = []
p = {}
p1 = {}
convertmp4 = 0

args = sys.argv[1:]
if len(args):
	CW = args[0]
	if CW == '-c':
		convertmp4 = 1
		print ("Recordings will be converted to mp4 after ending broadcast.")

if os.name == 'nt':
	FFMPEG = 'ffmpeg.exe'
else:
	FFMPEG = 'ffmpeg'
	
def file_size(fname):
        statinfo = os.stat(fname)
        return statinfo.st_size

def get_live_broadcast(user, usertype):
	req = urllib.request.Request(PERISCOPE_URL + user)
	try:
		response = urllib.request.urlopen(req)
		r = response.read()
		soup = BeautifulSoup(r, 'html.parser')
		page_container = soup.find(id='page-container')
		data_store = json.loads(page_container['data-store'])
		broadcasts = data_store['BroadcastCache']['broadcasts']
		if not broadcasts:
			live_broadcast = {}
		else:
			for key in broadcasts:
				broadcast = broadcasts[key]
				if broadcast['broadcast']['state']== 'RUNNING':
					live_broadcast = broadcast['broadcast']['data']
					break
				else:
					live_broadcast = {}	
	except urllib.error.URLError as e:
		res = e.reason
		if res == 'Not Found' and usertype == 'p':
			live_broadcast = {'user_id': ['unknown']}
		elif res == 'Not Found' and usertype == 't':
			live_broadcast = {}
		else:
			#unknown error
			print('URLError: ',e.reason)
			live_broadcast = {'user_id': ['skip']}
	return live_broadcast
	
def get_twitter_streamURL(user):
	req = urllib.request.Request(TWITTER_URL + user)
	try:
		response = urllib.request.urlopen(req)
		r = response.read()
		soup = BeautifulSoup(r, 'html.parser')
		stream_container = str(soup.find(id="stream-items-id"))
		if not stream_container.find('https://www.pscp.tv/w/') == -1:
			streamURL = (stream_container[stream_container.find('https://www.pscp.tv/w/')+20:])
			streamURL = (streamURL[:streamURL.find('" ')])
		else:
			#no streams or recorded streams
			streamURL = 'nothing'
	except urllib.error.URLError as e:
		print('URLError: ',e.reason)
		res = e.reason
		if res == 'Not Found':
			streamURL = 'unknown'
		else:
			#unknown error
			streamURL = 'nothing'
	return streamURL
	
def rec_ffmpeg(broadcast_id, input, output):
	command = [FFMPEG,'-i' , input,'-y','-acodec','mp3','-loglevel','0', output]
	p[broadcast_id]=subprocess.Popen(command)
	broadcastdict[broadcast_id]['recording'] = 1
	time.sleep(1)
	
def convert2mp4(broadcast_id, input):
	if convertmp4 == 1:
		output = input.replace('.mkv','.mp4')
		command = [FFMPEG,'-i' , input,'-y','-loglevel','0', output]
		p1[broadcast_id]=subprocess.Popen(command)
	
while True:
	#read users.csv into list every loop, so you can edit csv file during run.
	print ('*--------------------------------------------------------------*')
	with open('users.csv', 'r') as readfile:
		reader = csv.reader(readfile, delimiter=',')
		usernames2 = list(reader)
	usernames = usernames2[0]
	deleteuserbroadcast = []
	for user in usernames:
		usershort = user[:-2]
		usertype = user[-1:]
		#Peri or Twitter user
		if usertype == 't':
			streamURL = get_twitter_streamURL(usershort)
			print ((time.strftime("%H:%M:%S")),' Polling Twitter account:', usershort)
			if streamURL == 'unknown':
				#user does not exists
				live_broadcast = {'user_id': ['unknown']}
			elif streamURL == 'nothing':
				live_broadcast = {}
			else:
				live_broadcast = get_live_broadcast(streamURL, usertype)
		else:
			print ((time.strftime("%H:%M:%S")),' Polling Peri account   :', usershort)
			live_broadcast = get_live_broadcast(usershort, usertype)
		if live_broadcast:
			if live_broadcast['user_id'] == ['unknown']:
				# user does not exists anymore
				# extra loop to be sure
				if user in deleteuser:
					usernames.remove(user)
					deleteuser.remove(user)
					print ('Delete user: ', usershort)
					with open('users.csv', 'w') as outfile:
						writer = csv.writer(outfile, delimiter=',',quoting=csv.QUOTE_ALL)
						writer.writerow(usernames)
				else:
					deleteuser.append(user)
					print ('Loop delete user: ', usershort)
			elif live_broadcast['user_id'] == ['skip']:
				#skip user loop
				print ('HTTP request error. Skip user: ', usershort)
			else:
				broadcast_id = live_broadcast['id']
				if broadcast_id not in broadcastdict :
					print ('New scope of user: ', usershort)
					HLS_URL_2 = live_broadcast['image_url'][live_broadcast['image_url'].find('.tv/')+ 4:]
					if 'chunk' in HLS_URL_2:
						HLS_URL_2 = HLS_URL_2[:HLS_URL_2.find('chunk') - 1]
					if 'orig.jpg' in HLS_URL_2:
						HLS_URL_2 = HLS_URL_2[:HLS_URL_2.find('orig.jpg') - 1]
					broadcastdict[broadcast_id] = {}
					broadcastdict[broadcast_id]['user'] = usershort
					broadcastdict[broadcast_id]['HLS_URL2']= HLS_URL_2
					broadcastdict[broadcast_id]['state']= 'RUNNING'
					broadcastdict[broadcast_id]['time']= time.time()
					broadcastdict[broadcast_id]['filename']= usershort + '_on_peri_' + str(broadcastdict[broadcast_id]['time'])[:10] + '.mkv'
					broadcastdict[broadcast_id]['filesize']= 0
					broadcastdict[broadcast_id]['lastfilesize']= 0
					broadcastdict[broadcast_id]['recording']= 0

					print ('Start recording for: ', usershort)
					breaker = False
					for counter in range(1,2):
						for key in HLSURL1:
							URL = key + broadcastdict[broadcast_id]['HLS_URL2'] + HLSURL1[key]
							rec_ffmpeg(broadcast_id, URL, broadcastdict[broadcast_id]['filename'] )
							time.sleep(1)
							if os.path.exists(broadcastdict[broadcast_id]['filename']):
								print ('Recording started from: ', key, '-', broadcast_id)
								broadcastdict[broadcast_id]['HLS_URL'] = URL
								breaker = True
								break
							else:
								p[broadcast_id].terminate()
						if breaker:
							break
						time.sleep(5)
					if not os.path.exists(broadcastdict[broadcast_id]['filename']):
						print ('No recording file created for: ', usershort, 'file: ', broadcastdict[broadcast_id]['filename'])
						deleteuserbroadcast.append(broadcast_id)
	for broadcast_id in broadcastdict:
		#check recording file
		if os.path.exists(broadcastdict[broadcast_id]['filename']) and broadcastdict[broadcast_id]['state'] == 'RUNNING':
			if broadcastdict[broadcast_id]['filesize'] < file_size(broadcastdict[broadcast_id]['filename']):
				broadcastdict[broadcast_id]['filesize'] = file_size(broadcastdict[broadcast_id]['filename'])
				print ('Running ',round(time.time()- broadcastdict[broadcast_id]['time']), 'seconds: ', broadcastdict[broadcast_id]['filename'])
			elif file_size(broadcastdict[broadcast_id]['filename']) < 307200 or file_size(broadcastdict[broadcast_id]['filename']) == broadcastdict[broadcast_id]['lastfilesize']:
				#final stop recording when file < 300kB
				p[broadcast_id].terminate()
				time.sleep(2)
				broadcastdict[broadcast_id]['state'] = 'ENDED'
				deleteuserbroadcast.append(broadcast_id)
				os.remove(broadcastdict[broadcast_id]['filename'])
				print ('Delete: ', broadcastdict[broadcast_id]['filename'])
			else:
				#ffmpeg is not recording anymore.
				broadcastdict[broadcast_id]['lastfilesize'] = file_size(broadcastdict[broadcast_id]['filename'])
				print ('Restart recording for: ', broadcastdict[broadcast_id]['filename'] , ' :stream / record error')
				p[broadcast_id].terminate()
				convert2mp4(broadcast_id, broadcastdict[broadcast_id]['filename'])
				#start new recording
				URL = broadcastdict[broadcast_id]['HLS_URL']
				broadcastdict[broadcast_id]['filename']= broadcastdict[broadcast_id]['user'] + '_on_peri_' + str(time.time())[:10] + '.mkv'
				broadcastdict[broadcast_id]['filesize']= 0
				broadcastdict[broadcast_id]['time']= time.time()
				rec_ffmpeg(broadcast_id, URL, broadcastdict[broadcast_id]['filename'] )
	#end recording, delete entry in broadcastdict and convert mkv -> mp4
	for broadcast_id in deleteuserbroadcast:
		p[broadcast_id].terminate()
		print ('End recording for: ', broadcastdict[broadcast_id]['user'])
		if broadcast_id in broadcastdict:
			convert2mp4(broadcast_id, broadcastdict[broadcast_id]['filename'])
			del broadcastdict[broadcast_id]
	time.sleep(1)
