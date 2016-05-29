#import requests
#import json
from fb_albums import get_albums

def access_graph_api():
	token_file = open('API_KEYS.txt', 'r')
	token = token_file.read()
	api_url = "https://graph.facebook.com/v2.1/"
	get_albums.download(token)
	

if __name__ == '__main__':
	access_graph_api()



