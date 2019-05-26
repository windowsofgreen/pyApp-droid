#!/usr/bin/env python
from importlib import import_module
import os,time
from flask import Flask, render_template, Response
import argparse
from flask_socketio import SocketIO,emit

parser = argparse.ArgumentParser()
parser.add_argument('--dev', type=str, required=False,default='0')
                    #help='[usb|"url" of IP camera]input video device')
parser.add_argument('--httpport', type=int,
                    help='The port for http server')
parser.add_argument('--svr', type=str,
                    help='The ip for training server')
args = parser.parse_args()

print("Initialzing face recognition engine.")
if args.dev == 'usb':
    from camera_opencv import *
    print("Using onboard usb camera")
    Camera.set_video_source([0])
else:
    from camera_opencv import *
    video_source = []
    for url in args.dev.split(','):
        video_source.append(url)
    Camera.set_video_source(video_source)
    print("Using ip camera with url(s)", video_source)

if args.httpport != None:
    HTTP_PORT = args.httpport
else:
    HTTP_PORT = 5000

fdir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app)

@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index_web.html')

def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/png\r\n\r\n' + frame + b'\r\n')

@app.route('/videoel')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    if args.dev == 'laptop':
        return Response()
    else:
        print("video_feed")
        return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('request',namespace='/testnamespace')
def give_response(data):
    msg_type = data.get('type')
    msg_data = data.get('data')

    if (msg_type == "ADDPERSON_REQ"):
        print "TRAINSTART_REQ"
        Camera.add_person(str(msg_data))
    elif (msg_type == "DELPERSON_REQ"):
        print "DELPERSON_REQ"
        Camera.del_person(str(msg_data))
    elif (msg_type == "GETNAMES_REQ"):
        names = Camera.get_names()
        emit('response',{'code':'200','msg': ",".join(names)})

if __name__ == '__main__':
    #websocket.startWebSocketServer(serverip)
    #app.run(host='0.0.0.0', threaded=True)
    #app.run(host='0.0.0.0', port=HTTP_PORT, threaded=True, ssl_context=(tls_crt, tls_key))
    socketio.run(app,debug=True,host='0.0.0.0',port=5000)
