#import requests
#import json
from fb_albums import get_albums
from facial_recognition import face_detect
from os import listdir

PHOTOS_PATH = 'albums2'

def download_photos():
	token_file = open('API_KEYS.txt', 'r')
	token = token_file.read()
	api_url = "https://graph.facebook.com/v2.1/"
	get_albums.download(token, PHOTOS_PATH)

def load_photos():
	folders = listdir(PHOTOS_PATH)
	for folder in folders:
		photos = listdir(PHOTOS_PATH + "/" + folder)
		for photo in photos:
			process_photo(PHOTOS_PATH + "/" + folder + "/" + photo)

def process_photo(filename):
	print filename
	face_detect.get_faces(filename)

if __name__ == '__main__':
	download_photos()
	load_photos()



