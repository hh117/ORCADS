import json

from flask import Flask, render_template, request
import sys,logging
from threading import Thread
from flask_socketio import SocketIO,emit
sys.path.append('..')
from farmi import FarmiUnit,farmi
import requests

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# example publisher
FARMI_DIRECTORY_SERVICE_IP = '127.0.0.1'
pub = FarmiUnit('interface', local_save=True, directory_service_ip=FARMI_DIRECTORY_SERVICE_IP)

test_pic_path = '/static/img/camera_image_uav1_2018-09-18_11-05-03_682253.jpeg'

@socketio.on('text')
def chat(json_chat):
    socketio.emit('message',{'msg':json_chat['msg'],'role':'operator'})
    socketio.emit('img', {'path': test_pic_path, 'role': 'orca_ds'})
    #requests.get('http://localhost:5000/img?path={}&role={}'.format(test_pic_path,'orca_ds'))
    #socketio.emit('message',{'msg':'I don\'t know','role':'orca_ds'})
    return 'ok'

@socketio.on('restart')
def restart():
    pub.send(({'text': ''},'action.restart'))
    return 'OK'


@app.route('/')
def index():
    return render_template('index.html',role='user')

@app.route('/asr')
def display_asr():
    socketio.emit('message', {'msg': request.args['msg'], 'role': request.args['role']})
    return 'ok'

@app.route('/img')
def send_img():
    socketio.emit('img',{'path':requests.args['path'],'role': requests.args['role']})
    return 'ok'

def run():
    logging.info('Interface is up')

    @farmi(subscribe='pre-processor', directory_service_ip=FARMI_DIRECTORY_SERVICE_IP)
    def send_to_interface(subtopic,time,data):

        data_sender = data[1]

        if 'asr' in data_sender.split('.'):

            speaker = data_sender.split('.')[2]
            asr_output = json.loads(data[0])
            if 'transcript' in asr_output:
                print(asr_output['transcript'])
                requests.get('http://localhost:5000/asr?msg={}&role={}'.format(asr_output['transcript'],speaker))
                #socketio.emit('message', {'msg': request.args['transcript'], 'role': request.args['role']})

            else:
                logging.warning('No transcription in message')
                print(json.dumps(asr_output,indent=2))

    print('[*] Waiting for pre-processors. To exit press CTRL+C')
    send_to_interface()

    #@farmi(subscribe='orca_ds',directory_service_ip=FARMI_DIRECTORY_SERVICE_IP)
    #def process_dm_answer(subtopic,time,data):

    #    action = data[1]
    #    msg = data[0]

    #if action == 'respond':
    #        request.get('http://localhost:5000/emit?text={}'.format(msg['text']))

    #print('[*] Waiting for agent\'s messages. To exit press CTRL+C')
    #process_dm_answer()

if __name__ == "__main__":
    thread = Thread(target=run)
    thread.deamon = True
    thread.start()
    socketio.run(app, host='0.0.0.0')
