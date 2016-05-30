# PhotoScraper

This script pulls a user's posted photos from all photo albums, saves
them to the filesystem, and crops the photos to be 4x6 in such a way 
to minimize both the total area cropped from the photo and the area of
faced cropped from the photo.

Square photos are padded with black space to become 4x6 photos.

# Setup and Dependencies

This script uses python 2.7

Third-party packages:

numpy
Pillow
opencv

See requirements.txt for versions

In order to pull photos from Facebook, you'll need a Facebook Access Token go to https://developers.facebook.com/tools-and-support/ and click on Graph API Explorer to get an access token. You'll need to ask for access to photos. Put this string into a file called access_token 

echo "LONGACCESSTOKENFROMAPIEXPLORERGOESHERE" > access_token

# Usage

To run this script

python main.py

# Technical Writeup

This is a script that

1) Downloads photos you have posted to albums on facebook
2) Crops the photos into 4x6 photos.

I found a github repo with code to load the photos. The code is in fb_albums/get_albums.py. This saves all photos in folders by facebook album into folder 'albums'.

The algorithm used to crop photos attempts to minimize both the total area lost when cropping the photo, but also the area of the bounded boxes matching faces recognized in the photo. Faces are tagged using opencv.

The algorithm attempts 12 different crops of the photo. First, it holds the width of the photo constant and attempts crops for the two heights that would keep the photo a 4x6, but only if the height is less than the current height of the photo. Then it does the same for holding height constant. For each of these widths and heights, it attempts to to crop from one direction, then the other (eg top, bottom) and then half from each (1/2 top, 1/2 bottom).

Each attempted crop is assigned a score based on the total amount of area lost from the crop and the area within the bounded boxes for faces lost from the crop. The area lost within the bounded boxes is multiplied by a constant factor specified in the code to increase the value of not cropping out faces. Bounded boxees are created using opencv. The code for this is in facial_recognition/face_detect.py
