#!/usr/bin/env python
"""
File: get_albums.py
-------------------
Assignment 4: PhotoScraper
Course: CS 41
Name: Christina Gilbert
SUNet: christyg

This code was taken from the following github repo:
https://github.com/mhowsden/get_albums.py

and converted into a module for use in my project; I also
converted it from python2 to python3 and modified the 
mechanism for loading the access token
"""

import requests, re, os, shutil, json

def download(my_token):

    data_path = os.path.join(os.getcwd(), 'data')
    albums_path = os.path.join(os.getcwd(), 'albums')

    # creating data and album directories if they don't exist
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    if not os.path.exists(albums_path):
        os.makedirs(albums_path)

    json_filename = os.path.join(data_path, "album_list.json")

    if not os.path.exists(json_filename):
        # getting all album details for the token's user
        r = requests.get("https://graph.facebook.com/me/albums?access_token=%s" % my_token)

        # dropping out if we get a bad http response
        if r.status_code != 200:
            print ("\nFailed to properly connect to the Facebook API.")
            print ("HTTP Status Code: %s\n" % r.status_code)
            exit()

        # saving JSON response for the album list
        json_file = open(json_filename, "w")
        json_file.write(json.dumps(r.json(), sort_keys=True,
                                   indent=4, separators=(',', ': ')))
        json_file.close()

        # a dict representation of albums data
        albums = r.json()['data']
    else:
        json_file = open(json_filename, "r")
        albums = json.load(json_file)["data"]
        json_file.close()


    # for stripping non-alphanumeric
    pattern = re.compile('[\W]+')

    for album in albums:
        print ('Processing album "%s" with id %s.' % (album['name'], album['id']))

        album_dir_name = pattern.sub('', album['name'].replace(' ','_'))
        album_path = os.path.join(albums_path, album_dir_name)

        if not os.path.exists(album_path):
            os.makedirs(album_path)

        json_filename = os.path.join(data_path, "%s.json" % album_dir_name)

        if not os.path.exists(json_filename):
            r2 = requests.get("https://graph.facebook.com/%s/photos?access_token=%s"
                              % (album['id'], my_token))
            # saving JSON response for the image list
            json_file = open(json_filename, "w")
            json_file.write(json.dumps(r2.json(), sort_keys=True,
                                       indent=4, separators=(',', ': ')))
            json_file.close()

            images = r2.json()["data"]
        else:
            json_file = open(json_filename, "r")
            images = json.load(json_file)["data"]
            json_file.close()

        for counter, image in enumerate(images):
            counter += 1

            image_filename = os.path.join(album_path, "%s.jpg" % counter)

            if not os.path.exists(image_filename):
                print("Downloading image %s of album %s." % (counter, album['name']))
                r3 = requests.get(image["source"], stream=True)
                image_file = open(image_filename, "wb")
                shutil.copyfileobj(r3.raw, image_file)
                image_file.close()
            else:
                print ("Already retreived image %s of album %s." % (counter, album['name']))

            if 'name' in image:
                print (image["name"])
