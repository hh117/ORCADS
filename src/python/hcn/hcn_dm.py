import argparse,logging
import re

import yaml

from feature_extraction import *
from sptd_utils import *

def parse_action_yaml(yaml_dict):

    action_list = []

    for item in yaml_dict:
        if item != 'name':
            for elem in yaml_dict[item]:
                action_list.append('{}_{}'.format(item,elem))

    return action_list

def check_robot_name(name):

    for type in robots:
        for robot_name in robots[type]:
            if robot_name == name:
                return type

    return False

def pre_process_utterance(utt):

    robot_name_pattern = re.compile('(\D+)(\d+)')
    anonymised_utt = utt

    for wrd in utt.split():
        if re.match(robot_name_pattern,wrd):
            robot_name, robot_id = re.match(robot_name_pattern,wrd).groups()
            if check_robot_name(robot_name):
                 anonymised_utt = re.sub(wrd,'<{}>'.format(check_robot_name(robot_name)),anonymised_utt)

    return anonymised_utt


parser = argparse.ArgumentParser(description='Dialogue Manager for HCN')
parser.add_argument('--embeddings_file','-e',type=str,help='File with embeddings',required=True)
parser.add_argument('--action_file','-a',type=str,help='File with the action outputs from the system',required=True)
parser.add_argument('--robots_list','-r',type=str,help='File with the list of robots in the scenario',required=True)
parser.add_argument('--dialogue_acts','-da',type=str,help='File with definitions of dialogues',required=True)

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

args = parser.parse_args()

actions = parse_action_yaml(yaml.safe_load(open(args.action_file,'r').read()))

robots = yaml.safe_load(open(args.robots_list,'r').read())
dialogue_states = yaml.safe_load(open(args.dialogue_acts,'r').read())

print(dialogue_states)

#glove_model,model_dim = load_glove_vectors(args.embeddings_file)

utt_in = input('U:')
utt_in = utt_in.lower()
print(pre_process_utterance(utt_in))

sys.exit()
utt_emb = get_utterance_embedding(glove_model,utt_in,model_dim)
