import argparse,sys,os,re
import json
import logging
import random
import yaml

sys.path.append('..')
from utils import preProcess,DialogueConfig
#from DialogueConfig import DialogueConfig

sys.path.append('/Users/jdlopes/multisensoryprocessing/src/python')
from farmi import FarmiUnit, farmi
from FlowState import FlowState as FS
from furhat import connect_to_iristk

FURHAT_AGENT_NAME = 'system'
FURHAT_IP = '130.237.67.91'

pre_recorded_path = 'c:/prerec'

FARMI_DIRECTORY_SERVICE_IP = '127.0.0.1'

pub = FarmiUnit('agent', local_save=True, directory_service_ip=FARMI_DIRECTORY_SERVICE_IP)

def furhat_say(utterance):


    with connect_to_iristk(dialogue_config.furhat_ip) as furhat_client:
        if utterance.lower() == "mm":
            # backchannels
            furhat_client.say(FURHAT_AGENT_NAME,utterance,audio_file=os.path.join(pre_recorded_path,'mm_continuer.wav'))
        elif utterance.lower() == "mhm":
            # backchannels
            furhat_client.say(FURHAT_AGENT_NAME,utterance,audio_file=os.path.join(pre_recorded_path,'mhm_continuer.wav'))
        else:
            furhat_client.say(FURHAT_AGENT_NAME,utterance)

def furhat_gesture(gesture_name):

    with connect_to_iristk(dialogue_config.furhat_ip) as furhat_client:
        furhat_client.gesture(FURHAT_AGENT_NAME,gesture_name)


def changeAttendee(direction):

    global attend

    with connect_to_iristk(dialogue_config.furhat_ip) as furhat_client:
        if direction == 'all':
            furhat_client.gaze(FURHAT_AGENT_NAME, location={'x': 0, 'y': 0, 'z': 2})
            attend = 'all'
        elif direction == 'left':
            #furhat_client.attend_user(FURHAT_AGENT_NAME,'left')
            furhat_client.gaze(FURHAT_AGENT_NAME,location={'x':0.7,'y':0,'z':2})
            attend = 'left'
        elif direction == 'right':
            furhat_client.gaze(FURHAT_AGENT_NAME,location={'x':-0.7,'y':0,'z':2})
            attend = 'right'
        elif direction == 'other':
            if attend == 'right':
                changeAttendee('left')
            elif attend == 'left':
                changeAttendee('right')
            elif attend == 'all':
                changeAttendee(random.choice(['left', 'right']))


def getCurrentState(utterance):

    for state in states_dict:
        if states_dict[state].check_utterance(utterance):
            state_history.append(state)
            return

    state_history.append('unknown')

def getAction(_mq, get_shifted_time, routing_key, body):

    if routing_key == 'action.text':
        if body['text'] == 'repeat':
            # retrieving last utterance
            getNextState(utterance_history[-1],body['state'],body['gesture'].split(';'),body['sequence'])
        elif (body['text'] not in dialogue_config.pre_defined_utt or body['text'] != 'repeat') and body['state'] != 'start' :
            getNextState(body['text'],body['state'],body['gesture'].split(';'),body['sequence'])
        else:
            logging.warning('Predefined utterance cannot be used in state {}'.format(body['state']))
    elif routing_key == 'action.attend' and args.furhat:
        changeAttendee(body['text'])
    elif routing_key == 'action.restart':
        state_history.clear()
        getNextState('start')
        if args.furhat:
            changeAttendee('all')

def getNextState(utterance,current_state='start',gesture='',sequence='False'):

    global state_history
    utteranceList = [] # list with the utterances allowed for each state
    stateList = [] # list of the states corresponding to the utterances
    gestureList = []
    sequenceList = []

    if utterance != 'start':
        state_history.append(current_state)
        utterance_history.append(utterance)
        logging.debug('U: {} {}'.format(utterance,gesture))
        # keep mode activated if utterance was among the predefined utterances
        if utterance.lower() in dialogue_config.pre_defined_utt:
            if not states_dict[current_state].sequence:
                logging.debug('Reactivating the sequence mode for state {}'.format(current_state))
                states_dict[current_state].sequence = True
        if sequence == 'True':
            states_dict[current_state].remove_sequence_utterances(utterance,dialogue_config)
        if states_dict[current_state].check_sequence():
            states_dict[current_state].sequence = True
    else:
        # hack that loads the intro sentences when the wizard interface is reloaded
        state_history.append('start')
        intro_state = list((set(states_dict['start'].get_transitions()) - set(['start'])))[0]
        for utt in states_dict[intro_state].get_utterances():
            utt, gesture = preProcess(utt,dialogue_config)
            if utt != None:
                utteranceList.append(
                    {'utterance': utt, 'state': intro_state, 'gestures': gesture, 'sequence': 'True'})
        if args.wizard:
            sendNBestUttWizard(utteranceList,current_state)
            return
        else:
            return utteranceList


    if args.furhat:
        for g in gesture:
             if g.startswith('attend'):
                target = g.split('.')[1]
                if target == 'other':
                    if attend == 'right':
                        changeAttendee('left')
                    elif attend == 'left':
                        changeAttendee('right')
                    elif attend == 'all':
                        changeAttendee(random.choice(['left','right']))
                else:
                    changeAttendee(target)
             if g.startswith('gesture'):
                 furhat_gesture(g.split('.')[1])
        furhat_say(utterance)

    #allowed_transitions = set(states_dict[current_state].get_transitions())
    allowed_transitions = set(states_dict[current_state].transitions)
    if len(allowed_transitions) > 2:
        available_states = list(allowed_transitions.difference(state_history))
    else:
        available_states = list(allowed_transitions)
        for state in available_states:
            states_dict[state].sequence = False
            states_dict[state].sequence_used = False
            states_dict[state].rebuild_sequence()

    logging.debug('Available states {}, current state {}'.format(available_states,current_state))

    # get utterances for the subsequent states
    if states_dict[current_state].sequence and not states_dict[current_state].sequence_used:
        sequence_utterances = []
        for utt in states_dict[current_state].get_utterances():
            utt, gesture = preProcess(utt,dialogue_config)
            if utt != None:
                sequence_utterances.append({'utterance':utt, 'state':current_state, 'gestures': gesture, 'sequence': 'True'})
        random.shuffle(sequence_utterances) # randomizing utterances for sequence questions to the same state
        utteranceList += sequence_utterances

    transition_utterances = []
    # get utterances for next states
    for state in available_states:
        # checks if the state is defined
        if state in states_dict:
            for utt in states_dict[state].get_utterances():
                utt, gesture = preProcess(utt,dialogue_config)
                if utt != None:
                    transition_utterances.append(
                        {'utterance': utt, 'state': state, 'gestures': gesture, 'sequence': 'True'})
        else:
            logging.error('State {} is not defined'.format(state))
    random.shuffle(transition_utterances) # randomizing utterances corresponding to state transitions
    utteranceList += transition_utterances

    if args.wizard:
        sendNBestUttWizard(utteranceList,current_state)
    else:
        return utteranceList

def addRandomUtterance(state,curr_state):
    utt, gest = preProcess(random.choice(states_dict[state].get_utterances()),dialogue_config)
    return {'utterance': utt, 'state': curr_state, 'gestures': gest, 'sequence': 'True'}

def addSequenceUtterances(state,curr_state):
    uttList = []
    for uttDef in states_dict[state].get_utterances():
        utt, gest = preProcess(uttDef,dialogue_config)
        uttList.append({'utterance': utt, 'state': curr_state, 'gestures': gest, 'sequence': 'True'})
    return uttList


def sendNBestUttWizard(utteranceList,current_state):

    if len(utteranceList) < 2 and len(state_history) > 1:
        utteranceList.append(addRandomUtterance('change_topic','change_topic'))
        utteranceList.append(addRandomUtterance('end','end'))

    # the interface allows no more than 9 utterance to be chosen from
    if len(utteranceList) > 6:
        if len(state_history) > 30:
            utteranceList = utteranceList[:5]
            utteranceList.append(addRandomUtterance('end','end'))
            logging.debug('inserted end of dialogue utterance')
        else:
            utteranceList = utteranceList[:6]
        # add change topic a randomly chosen utterance
        if state_history[-1] not in ['change_topic','start','intro']:
            if states_dict['change_topic'].sequence:
                utteranceList += addSequenceUtterances('change_topic', 'change_topic')
            else:
                utteranceList.append(addRandomUtterance('change_topic','change_topic'))
        utteranceData = {'action': 'say', 'text': [d['utterance'] for d in utteranceList], 'state': [d['state'] for d in utteranceList],
                         'current_state': current_state, 'gestures': [d['gestures'] for d in utteranceList], 'sequence': [d['sequence'] for d in utteranceList]}
    else:
        # add change topic a randomly chosen utterance
        if len(state_history) > 30:
            if len(utteranceList) == 6:
                utteranceList = utteranceList[:5]
            utteranceList.append(addRandomUtterance('end','end'))
        if state_history[-1] not in ['change_topic', 'start', 'intro']:
            if states_dict['change_topic'].sequence:
                utteranceList += addSequenceUtterances('change_topic', 'change_topic')
            else:
                utteranceList.append(addRandomUtterance('change_topic','change_topic'))
        utteranceData = {'action': 'say', 'text': [d['utterance'] for d in utteranceList], 'state': [d['state'] for d in utteranceList],
                         'current_state': current_state, 'gestures': [d['gestures'] for d in utteranceList], 'sequence': [d['sequence'] for d in utteranceList]}

    #print(utteranceData)

    pub.send((utteranceData,'furhat.say'))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Generates dialogues form a set of rules specified in a flow chart')
    parser.add_argument('--wizard', '-w', action='store_true',help='wizard interface')
    parser.add_argument('--states','-s',type=str,help='home dir with the states configuration',required=True)
    parser.add_argument('--furhat','-f',action='store_true',default=False,help='a furhat is connected')
    parser.add_argument('--config','-c',type=str,help='file with user data and personality config',required=True)

    args = parser.parse_args()

    dialogue_config = DialogueConfig(os.path.join(args.config))

    SETTINGS_FILE = os.path.join(dialogue_config.farmi_dir,'settings.yaml')
    settings = yaml.safe_load(open(SETTINGS_FILE, 'r').read())

    session_name = '{}.{}'.format(settings['mission']['name'].lower(),pub.timestamp)

    log_path = os.path.join(settings['logging']['log_path'], session_name)

    if not os.path.isdir(log_path):
        os.makedirs(log_path)

    logfile_name = os.path.join(log_path,'dialogue_flow.log')

    if os.path.isfile(logfile_name):
        os.remove(logfile_name)

    #logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO, filename=logfile_name)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    states_dict = {}
    for root,dir,files in os.walk(args.states):
        for file in files:
            if file.endswith('yaml'):
                logging.info('Loading state information form file {}'.format(file))
                state_name = file.split('.')[0]
                states_dict[state_name] = FS(os.path.join(root,file),dialogue_config)

    utterance = ''
    state_history = []
    utterance_history = []

    attend = 'all'

    if args.wizard:
        @farmi(subscribe='wizard',directory_service_ip=FARMI_DIRECTORY_SERVICE_IP)
        def getAction(sub_topic, time, data):

            body = data[0]
            routing_key = data[1]

            if routing_key == 'action.text':
                if body['text'] == 'repeat':
                    # retrieving last utterance
                    getNextState(utterance_history[-1], body['state'], body['gesture'].split(';'), body['sequence'])
                elif (body['text'] not in dialogue_config.pre_defined_utt or body['text'] != 'repeat') and body[
                    'state'] != 'start':
                    getNextState(body['text'], body['state'], body['gesture'].split(';'), body['sequence'])
                else:
                    logging.warning('Predefined utterance cannot be used in state {}'.format(body['state']))
            elif routing_key == 'action.attend' and args.furhat:
                changeAttendee(body['text'])
            elif routing_key == 'action.restart':
                state_history.clear()
                getNextState('start')
                if args.furhat:
                    changeAttendee('all')
        #mq.bind_queue(exchange="wizard",routing_key="*.*",callback=getNextState(current_state,states_dict))
        getAction()
    else:
        predefined_utterances = ['Yes','Maybe','No','Mm','Mhm','I don\'t know']
        try:
            prompts = getNextState('start')
        except:
            logging.error('please define start state')
            sys.exit()

        while states_dict[state_history[-1]].name != 'end':
            for p,prompt in enumerate(prompts):
                logging.debug(u'%d: %s\n' % (p,prompt['utterance']))
            utterance = int(input('you:'))
            if utterance > len(prompts)-1:
                continue
            else:

                if prompts[utterance] not in predefined_utterances:
                    current_state = prompts[utterance]['state']
                    prompts = getNextState(prompts[utterance]['utterance'],current_state=prompts[utterance]['state'],
                                                                sequence=prompts[utterance]['sequence'])
                    if state_history[-1] not in ['change_topic', 'start', 'intro']:
                        if states_dict['change_topic'].sequence:
                            prompts += addSequenceUtterances('change_topic', 'change_topic')
                        else:
                            prompts.append(addRandomUtterance('change_topic', 'change_topic'))

                    for pu in predefined_utterances:
                        prompts.append({'utterance':pu,'state':current_state,'sequence':'False'})

                else:
                    logging.debug('Predefined utterance used, same state holds for another turn')
