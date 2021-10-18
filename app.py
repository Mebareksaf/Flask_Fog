from cv2 import data
from flask import Flask, render_template, Response, redirect, url_for, make_response,flash
import cv2
from flask.globals import request
from cameras_config import camera_links

from pymongo import MongoClient
import gridfs
from bson.objectid import ObjectId

import numpy as np
import os
import json

app = Flask(__name__, static_folder='static')

# list of camera accesses
cameras = camera_links

client = MongoClient("mongodb://mongodb:27017")
database = client.database

fs = gridfs.GridFS(database)

global images
images = {}

def get_image(img_id, fs, imges):
    img_id = ObjectId(img_id)

    imgId = [ imges[str(i)]['imageID']  for i in range(len(imges)) if imges[str(i)]['imageID'] == img_id ]
    imgShape = [ imges[str(i)]['shape'] for i in range(len(imges)) if imges[str(i)]['imageID'] == img_id ]

    imageID = imgId[0]
    shape = imgShape[0]
    #get img from gridfs by imageID
    image = fs.get(imageID) 
    # convert bytes to nparray
    img = np.frombuffer(image.read(), dtype=np.uint8)
    img = np.reshape(img, shape)
    ret, buffer = cv2.imencode('.jpg', img)
    frame = buffer.tobytes()
    yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def gen_susImages(db,fs,imgs):
    collections = db.list_collection_names()
    images_dict = {}
    count = 0
    for collection in collections:
        if collection.startswith("Pi"):
            images_dict[collection] = list(db[collection].find({}))
            for c in images_dict[collection]:
                imgs.update({str(count):c})
                count+=1
    
    images.update(imgs)

def find_camera(list_id):
    return cameras[int(list_id)]


def gen_frames(camera_id):
    cam = find_camera(camera_id) #return the camera access link with credentials

    cap = cv2.VideoCapture(cam)  # capture the video from the live feed
    while True:

        #Capture frame-by-frame & Returns boolean(True=frame read correctly)
        success, frame = cap.read()  #Read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/video_feed/<string:list_id>/', methods=["GET"])
def video_feed(list_id):
    return Response(gen_frames(list_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/', methods=["GET","POST"])
def index():
    action = ''
    if request.method == "GET":
        action = ''
    elif request.method == "POST":
        #data = json.loads(request.data())
        #return redirect('Alert.html')
        action = 'suspect'
    return render_template('index.html', camera_list=len(cameras), camera=cameras,action=action)

@app.route('/<string:list_id>/', methods=["GET"])
def oneCam(list_id):
    return render_template('oneCam.html', camera=list_id)

@app.route('/record')
def record():
    path = 'fog_streaming/static'
    listCam = os.listdir(path)
    camVideos = [len(os.listdir(path+'/'+cam))for cam in listCam]
    print(camVideos)
    return render_template('Record.html', Cams = listCam, lenvideos = camVideos)

@app.route('/suspicious')
def sus():
    gen_susImages(database,fs,images)
    list_imgs = len(images)
    return render_template('Susp.html', list_imgs = list_imgs, images=images)

@app.route('/suspicious/<string:img_id>/')
def get_suspimg(img_id):

    return Response(get_image(img_id,fs, images),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/suspect', methods=["POST"])
def alert():
    return "<script>  alert('Alert!'); </script>"
 #   if request.method == "POST":
   #     #t=time.time()
         #yield "suspicous Action!!!!!"
         #return app.response_class(generate(), mimetype='text/plain')
#def alert():
    #flash(u'Alert', 'Susp')
    #msg = "SUSPICIOUS"
    #"""if request.method == "POST":
        #flash('There is a suspicious action!!!!')
        #return redirect('index.html')
 #   return render_template('Alert.html') 


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0")
