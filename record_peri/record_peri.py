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
	'https://prod-video-us-east-1.pscp.tv/':'/live/us-east-1/playlist.m3u8',
	'https://prod-video-sa-east-1.pscp.tv/':'/live/sa-east-1/playlist.m3u8'
	}
broadcastdict = {}
deleteuser = []
p = {}
p1 = {}

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
	
def rec_ffmpeg(user, input, output):
	command = ['ffmpeg.exe','-i' , input,'-y','-acodec','mp3','-loglevel','0', output]
	p[user]=subprocess.Popen(command)
	broadcastdict[user]['recording'] = 1
	time.sleep(1)
	
def convert2mp4(input):
	output = input.replace('.mkv','.mp4')
	command = ['ffmpeg.exe','-i' , input,'-y','-loglevel','0', output]
	p1[user]=subprocess.Popen(command)

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
				if user not in broadcastdict:
					print ('New scope of user: ', usershort)
					broadcast_id = live_broadcast['id']
					HLS_URL_2 = live_broadcast['image_url'][live_broadcast['image_url'].find('.tv/')+ 4:]
					if 'chunk' in HLS_URL_2:
						HLS_URL_2 = HLS_URL_2[:HLS_URL_2.find('chunk') - 1]
					if 'orig.jpg' in HLS_URL_2:
						HLS_URL_2 = HLS_URL_2[:HLS_URL_2.find('orig.jpg') - 1]
					broadcastdict[user] = {}
					broadcastdict[user]['broadcast_id'] = broadcast_id
					broadcastdict[user]['HLS_URL2']= HLS_URL_2
					broadcastdict[user]['state']= 'RUNNING'
					broadcastdict[user]['time']= time.time()
					broadcastdict[user]['filename']= usershort + '_on_peri_' + str(broadcastdict[user]['time'])[:10] + '.mkv'
					broadcastdict[user]['filesize']= 0
					broadcastdict[user]['lastfilesize']= 0
					broadcastdict[user]['recording']= 0

					print ('Start recording for: ', usershort)
					for key in HLSURL1:
						URL = key + broadcastdict[user]['HLS_URL2'] + HLSURL1[key]
						rec_ffmpeg(user, URL, broadcastdict[user]['filename'] )
						time.sleep(1)
						if os.path.exists(broadcastdict[user]['filename']):
							print ('Recording started from: ', key)
							broadcastdict[user]['HLS_URL'] = URL
							break
						else:
							p[user].terminate()
					if not os.path.exists(broadcastdict[user]['filename']):
						print ('No recording file created for: ', usershort, 'file: ', broadcastdict[user]['filename'])
						deleteuserbroadcast.append(user)
	for user in broadcastdict:
		usershort = user[:-2]
		#check recording file
		if os.path.exists(broadcastdict[user]['filename']) and broadcastdict[user]['state'] == 'RUNNING':
			if broadcastdict[user]['filesize'] < file_size(broadcastdict[user]['filename']):
				broadcastdict[user]['filesize'] = file_size(broadcastdict[user]['filename'])
				print ('Running ',round(time.time()- broadcastdict[user]['time']), 'seconds: ', broadcastdict[user]['filename'])
			elif file_size(broadcastdict[user]['filename']) < 307200 or file_size(broadcastdict[user]['filename']) == broadcastdict[user]['lastfilesize']:
				#final stop recording when file < 300kB
				p[user].terminate()
				time.sleep(2)
				broadcastdict[user]['state'] = 'ENDED'
				deleteuserbroadcast.append(user)
				os.remove(broadcastdict[user]['filename'])
				print ('Delete: ', broadcastdict[user]['filename'])
			else:
				#ffmpeg is not recording anymore.
				broadcastdict[user]['lastfilesize'] = file_size(broadcastdict[user]['filename'])
				print ('Restart recording for: ', broadcastdict[user]['filename'] , ' :stream / record error')
				p[user].terminate()
				convert2mp4(broadcastdict[user]['filename'])
				#start new recording
				URL = broadcastdict[user]['HLS_URL']
				broadcastdict[user]['filename']= usershort + '_on_peri_' + str(time.time())[:10] + '.mkv'
				broadcastdict[user]['filesize']= 0
				broadcastdict[user]['time']= time.time()
				rec_ffmpeg(user, URL, broadcastdict[user]['filename'] )
	#end recording, delete entry in broadcastdict and convert mkv -> mp4
	for user in deleteuserbroadcast:
		p[user].terminate()
		print ('End recording for: ', user[:-2])
		if user in broadcastdict:
			convert2mp4(broadcastdict[user]['filename'])
			del broadcastdict[user]
	time.sleep(1)
