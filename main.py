from __future__ import print_function

import os

import youtube_dl

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from multiprocessing import Process, Queue
import multiprocessing as mp
import random
import time
import librosa
import math
import numpy as np
import matplotlib.pyplot as plt
import csv
import re

executable_path = os.path.dirname(os.path.abspath(__file__)) + "/geckodriver"
driver = webdriver.Firefox(executable_path= executable_path)

## get top 100 tracks

url = "https://tunebat.com/Search?q=a"

songs = []

def search():
	start = len(songs)

	for ele in driver.find_elements_by_class_name('search-track-name'):
		songs.append({"name": ele.get_attribute('innerHTML')})

	i = start
	for ele in driver.find_elements_by_class_name('search-artist-name'):
		songs[i]["band"] = ele.get_attribute('innerHTML')
		i += 1

	i = start
	s = 0
	for ele in driver.find_elements_by_class_name('search-attribute-value'):
		val = ele.get_attribute('innerHTML')
		if ("???" in val and s % 3 == 0):
			songs.pop(i)
			s += 1
		elif ("Major" in val or "Minor" in val):
			songs[i]["key"] = val
			i += 1

for i range(1,10):
	driver.get(url + "&page=" + i)
	search()



## get youtube video urls

i = 0
while i < len(songs):
	try:
		song = songs[i]
		driver.get("https://www.youtube.com/results?search_query=" + song["name"] +  " lyrics")
		for ele in driver.find_elements_by_id('video-title'):
			url = ele.get_attribute("href")
			if url is not None:
				song["url"] = ele.get_attribute("href")
				print(song["url"])
				break
		i += 1
	except:
		print("error on song: " + song["name"])

## download urls

ydl_opts = {
	'format': 'bestaudio/best',
	'outtmpl' : ''
}

i = 0
for song in songs:
	ydl_opts['outtmpl'] = str(i) + ".mp3"
	with youtube_dl.YoutubeDL(ydl_opts) as ydl:	
		ydl.download([song["url"]])
	i += 1

## convert songs

def splitArray(array,when_to_split):
    beginning = 0
    split_array = []
    for i in range(1,len(array)):
        if i % when_to_split == 0 or i == len(array) - 1:
            temp_split = tuple(array[beginning:i])
            split_array.append(temp_split)
            beginning = i

    return split_array


keys = {
	"A Minor": 0,
	"E Minor": 1,
	"B Minor": 2,
	"F# Minor": 3,
	"G♭ Minor": 3,
	"C# Minor": 4,
	"D♭ Minor": 4,
	"G# Minor": 5,
	"A♭ Minor": 5,
	"D# Minor": 6,
	"E♭ Minor": 6,
	"B♭ Minor": 7,
	"A# Minor": 7,
	"F Minor": 8,
	"C Minor": 9,
	"G Minor": 10,
	"D Minor": 11,
	
	"C Major": 0,
	"G Major": 1,
	"D Major": 2,
	"A Major": 3,
	"E Major": 4,
	"B Major": 5,
	"C♭ Major": 5,
	"F# Major": 6,
	"G♭ Major": 6,
	"D♭ Major": 7,
	"C# Major": 7,
	"A♭ Major": 8,
	"G# Major": 8,
	"E♭ Major": 9,
	"D# Major": 9,
	"B♭ Major": 10,
	"A# Major": 10,
	"F Major": 11
}

with open("csvfile.csv", "wb") as file:
	writer = csv.writer(file, delimiter=',')


	file_path = os.path.dirname(os.path.abspath(__file__))
	ext = ".wav"

	fft_arrays = []
	fileNum = 1

	for file in os.listdir(file_path):
		if(file.endswith(ext) or file.endswith(".mp3")):
			file = os.path.join(file_path, file)
			y, sr = librosa.load(file)
			midArrayVal = int(len(y) / 2)
			l_bound = midArrayVal - 330000
			r_bound = midArrayVal + 330000
			sampled_song = y[l_bound:r_bound]
			sampled_song = librosa.to_mono(sampled_song)
			yt, index = librosa.effects.trim(sampled_song)

			#sample_time = math.ceil(len(sampled_song) / 22050)

			tempo, beats = librosa.beat.beat_track(y=sampled_song, sr=sr) 
			tempo = int(tempo)
			#print(beats)

			fft_whole_array = abs(np.fft.fft(sampled_song))
			fft_first = fft_whole_array[0:int(len(fft_whole_array)/15)]
			
			average = []
			for i in range(0,len(fft_first)-1,100):
				tempsection = fft_first[i:i+100]
				average.append(np.average(tempsection))
			
			## my code ##
			song = songs[ int(re.search(r'([0-9]+).mp3', file).group(1)) ]
			print(song)
			
			key = song["key"]
			num = keys[key]
			average.append( num )
			## my code ##

			fft_arrays.append(average)

	np.savetxt("biggest.csv", fft_arrays, delimiter=",")
