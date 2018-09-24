from copy import copy
import random
import logging
import yaml
import sys

sys.path.append('..')
from utils import SituatedDialogueUtils

class FlowState():

    def __init__(self,state_settings_file,dialogue_config):

        state_settings = yaml.safe_load(open(state_settings_file).read())
        self.name = state_settings['name']
        self.utterances = []
        self.transitions = []
        self.dialogue_config = dialogue_config

        # adding stuff common to all personalities
        if 'formulations' in state_settings:
            if type(state_settings['formulations']) == type([]):
                self.add_utterances(state_settings['formulations'])
            else:
                for i in state_settings['formulations']:
                    self.add_utterances(state_settings['formulations'][i])
        else:
            logging.info('No prompts found in state {}'.format(self.name))

        if 'transition_states' in state_settings:
            self.transitions.append(state_settings['name'])
            for state in state_settings['transition_states']:
                self.transitions.append(state)
        else:
            logging.warning('No transitions in state {}'.format(self.name))

        if self.utterances == []:
            logging.error('No utterances found in state {}'.format(self.name))

        if self.transitions == []:
            logging.warning('No transitions found in state {}'.format(self.name))

        self.sequence = False
        self.sequence_used = False

    def add_utterances(self,utterance_list):

        for f in utterance_list:
            self.utterances.append(f)

    def get_transitions(self):

        # otherwise it only allows further transitions
        return self.transitions

    def get_utterances(self):

        return self.utterances