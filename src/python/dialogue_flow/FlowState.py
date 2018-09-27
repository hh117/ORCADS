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
        self.utterances = {'default': []}
        self.transitions = []
        self.dialogue_config = dialogue_config

        # adding stuff common to all personalities
        if 'formulations' in state_settings:
            self.add_utterances(state_settings['formulations'])
        else:
            logging.info('No prompts found in state {}'.format(self.name))

        if 'transition_states' in state_settings:
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

        if type(utterance_list) == type({}):
            for s in utterance_list:
                self.utterances[s] = utterance_list[s]
        else:
            for f in utterance_list:
                if type(f) != type(''):
                    for t in f:
                        self.utterances[t] = []
                        for s in f:
                            self.utterances[s] += f[s]
                else:
                    self.utterances['default'].append(f)

    def get_transitions(self):

        if self.sequence:
            # if the state has a sequence it is allowed to stay in the state
            transitions = self.transitions
            #transitions.append(self.name)
            return transitions
        else:
            # otherwise it only allows further transitions
            return self.transitions

    def check_sequence(self):

        for utt in self.utterances:
            if type(utt) == type([]):
                return True

        return False

    def get_utterances(self):

        """

        :return: returns utterances for each state
        """

        if self.sequence:
            # if we are doing a follow up we load only the follow up utterances
            if self.utterances['sequence'] != []:
                return self.sequence_utterances
        else:
            # otherwise we check if the state has any follow up
            valid_utterances = []
            for t in self.utterances:
                if t != 'sequence':
                    valid_utterances += self.utterances[t]
            return valid_utterances


