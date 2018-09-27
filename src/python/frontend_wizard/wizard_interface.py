import json

from flask import Flask, render_template, request
import pika,sys,logging
from threading import Thread
from flask_socketio import SocketIO, send, emit
import time
sys.path.append('/Users/jdlopes/multisensoryprocessing/src/python')
from farmi import FarmiUnit, farmi
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
FARMI_DIRECTORY_SERVICE_IP = '127.0.0.1'
pub = FarmiUnit('wizard', local_save=True, directory_service_ip=FARMI_DIRECTORY_SERVICE_IP)


silence_start = -1.0
silence_threshold = -1.0

@socketio.on("say")
def handle_say(json):
    if 'text' in json:
        if 'source' in json and json['source'] == 'typed':
            socketio.emit('message',{'msg':json['text'],'role':'wizard'})
        pub.send(({'text': json['text'],'state': json['state'], 'gesture': json['gesture'], 'sequence': json['sequence'], 'source': json['source']}, 'action.text'))
    else:
        print('Empty text string received from the wizard')
        return 'OK'

@socketio.on("activate_robot")
def activate_robot(json):
    pub.send((json,'activate.robot'))
    return 'ok'

@socketio.on("deactivate_robot")
def activate_robot(json):
    pub.send((json,'deactivate.robot'))
    return 'ok'

@app.route('/asr')
def display_asr():
    socketio.emit('message', {'msg': request.args['msg'], 'role': request.args['role']})
    return 'ok'

@app.route('/say')
def say():
    pub.send(({'text': request.args.get('text', '')}, 'action.say'))
    return 'OK'

@socketio.on('attend')
def attend(json):
    pub.send(({'text': json['text']}, 'action.attend'))
    return 'OK'

@socketio.on('restart')
def restart():
    pub.send(({'text': ''},'action.restart'))
    return 'OK'

@app.route("/emit")
def emit():
    socketio.emit('add_utterance_to_list',{'sentence':request.args['text'],'state':request.args['state'],
                                           'current_state': request.args['current_state'],'gestures': request.args['gestures'],
                                           'sequence': request.args['sequence']})
    return 'OK'

@app.route("/update_renv")
def update_renv():
    socketio.emit('update_robot_list',{'robot_name':request.args['robot_name'], 'robot_id':request.args['robot_id']})
    return 'OK'

@app.route("/activate_robot")
def activate_robot():
    socketio.emit('activate_robot',{'robot_name':request.args['robot_name'], 'robot_id':request.args['robot_id']})
    return 'OK'

@app.route("/")
def index():
    return render_template('index.html')

def run():

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    active_speakers = []

    @farmi(subscribe='agent', directory_service_ip=FARMI_DIRECTORY_SERVICE_IP)
    def update_wizard(subtopic, get_shifted_time, data):

        global socketio, silence_threshold

        tag = data[1]
        msg = data[0]

        if 'asr' in tag.split('.'):
            asr_output = json.loads(data[0])
            speaker = tag.split('.')[2]
            if 'transcript' in asr_output:
                requests.get('http://localhost:5000/asr?msg={}&role={}'.format(asr_output['transcript'], speaker))
        else:
            if tag == 'say':
                logging.debug(msg['text'])
            elif tag == 'furhat.say':
                for s,sentence in enumerate(msg['text']):
                    logging.debug(u'S: %s [%s]' % (sentence,msg['state'][s]))
                logging.debug(msg)
                requests.get('http://localhost:5000/emit?text=%s&state=%s&current_state=%s&gestures=%s&sequence=%s'%(
                    '|'.join(msg['text']),
                    '|'.join(msg['state']),
                    msg['current_state'],
                    '|'.join(msg['gestures']),
                    '|'.join(msg['sequence'])))
            elif tag == 'robots.env':
                requests.get('http://localhost:5000/update_renv?robot_name={}&robot_id={}'.format('|'.join(msg['robot_name']),'|'.join(msg['robot_id'])))
            elif tag == 'robot.active':
                requests.get(
                    'http://localhost:5000/activate_robot?robot_name={}&robot_id={}'.format('|'.join(msg['robot_name']),
                                                                                         '|'.join(msg['robot_id'])))

    print('[*] Waiting for agent\'s messages. To exit press CTRL+C')
    update_wizard()

if __name__ == "__main__":

    thread = Thread(target=run)
    thread.deamon = True
    thread.start()

    #socketio.run(app, host='0.0.0.0', debug=True, threading=True, async_mode='gevent')
    socketio.run(app, host='0.0.0.0')
    #app.run(threaded=True)
