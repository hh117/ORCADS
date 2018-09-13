import argparse,logging
import json
import re
import os
import sys
import numpy as np
import pickle
import pandas as pd
from babi_utils import process_utt
from feature_extraction import get_utterance_embedding
from sptd_utils import *
from babi_utils import *

def load_knowledge_base(kb_file):

    kb = []

    with open(kb_file,'r') as kbf:
        rest_dict = {}
        curr_rest_name = ''
        cnt = 0
        for line in kbf:
            # reading from line
            id,rest_name,field,value = line.split()
            # if the cycle is starting
            if curr_rest_name == '':
                curr_rest_name = rest_name
            # if data from a new restaurant appears save data from current a start an empty dict
            if rest_name != curr_rest_name:
                kb.append(rest_dict)
                cnt += 1
                rest_dict = {}
                curr_rest_name = rest_name
            if 'name' not in rest_dict:
                rest_dict['name'] = rest_name
            rest_dict[field] = value
            rest_dict['id'] = cnt

    logging.info('{} restaurants found in the db'.format(cnt))

    # for the last restaurant
    kb.append(rest_dict)

    return pd.DataFrame(kb)



def get_different_system_utterances(all_dialogues_set,kb):

    action_set = []

    for subs in all_dialogues_set:
        for d, dial in all_dialogues_set[subs].items():
            logging.info('Analysing data in subset {} dialogue {}'.format(subs,d))
            for turn in dial:
                sys_action = process_utt(turn['S'],kb)
                if sys_action not in action_set:
                    action_set.append(sys_action)

    return action_set

def parse_dialogue_file(dialogues_file):

    dialogues = {}
    set_data_frame = []
    num_dialogues = 0
    prev_turn = -20
    with open(dialogues_file,'r') as f:
        turns = []
        for line in f:
            line_split = line.strip().split()
            if len(line_split) == 4:
                # api call result
                set_data_frame.append({'dialogue': num_dialogues, 'turn': int(line_split[0]),'S': 'api_res', 'U': '',
                                       'S_proc': 'api_res', 'U_proc': '',
                                       'name': line_split[1], line_split[2]: line_split[3]})
                turns.append({'name': line_split[1], line_split[2]: line_split[3]})
            else:
                try:
                    num_user, sys_utt = line.split('\t')
                    num, user = num_user.split(None,1)
                except:
                    continue

                if int(num) < prev_turn:
                    dialogues[num_dialogues] = turns
                    turns = []
                    num_dialogues += 1
                    logging.info('Parsing dialogue {}'.format(num_dialogues))

                turns.append({'S': sys_utt.strip(), 'U': user.strip()})
                set_data_frame.append({'dialogue': num_dialogues, 'turn': int(num), 'S': sys_utt.strip(), 'U': user.strip(),
                                       'S_proc': process_utt(sys_utt.strip(),kb), 'U_proc': process_utt(user.strip(),kb),
                                       'name': '', 'ent': ''})
                prev_turn = int(num)

    pd.DataFrame(set_data_frame).to_csv(os.path.join(args.task_dir,'{}_{}_exchanges.csv'.format(set_def,args.task_num)),index=False)
    return dialogues

def get_context_features(entity_dict):

    context_feat_vec = -1*np.ones((len(entities['U']),))

    for e,ent in enumerate(entity_dict['U']):
        if entity_dict['U'][ent] != '':
            context_feat_vec[e] = cnt_feat_values[ent][entity_dict['U'][ent]]

    return context_feat_vec

def get_action_mask(entity_dict,api_call):

    action_mask = np.ones((features_sizes['actions'],))

    available_entities = [ent for ent in entity_dict['S'] if entity_dict['S'][ent] != []]
    available_entities += [ent for ent in entity_dict['U'] if entity_dict['U'][ent] != '']

    for a, act in enumerate(system_utterances):
        if act.find('api_call') > -1:
            action_mask[a] = 0
        if act.find('ok let me look') > -1:
            action_mask[a] = 0
        if act.find('name') > -1 and 'restaurants' not in available_entities:
            action_mask[a] = 0
        if act.find('R_address') > -1 and 'restaurants' not in available_entities:
            action_mask[a] = 0
        if act.find('R_phone') > -1 and 'restaurants' not in available_entities:
            action_mask[a] = 0

    if not api_call:
        for a,act in enumerate(system_utterances):
            if act.find('update') > -1:
                action_mask[a] = 1
            if act.find('another') > -1:
                action_mask[a] = 1

    return action_mask

def get_previous_action(dialogue,prev_turn_index):

    prev_action = np.zeros((len(system_utterances),))

    if prev_turn_index == -1:
        return prev_action

    prev_sys_action = dialogue[prev_turn_index]['S_proc']
    prev_action[system_utterances.index(prev_sys_action)] = 1

    return prev_action

def get_api_features(ent_dict):

    api_feat = np.zeros((features_sizes['api'],))

    ent_cnt = 0
    for r,rest in enumerate(ent_dict['S']['restaurants']):
        if r < 3:
            for ent in rest:
                if ent not in ['R_address','R_phone']:
                    if ent == 'name':
                        # getting restaurant id
                        rest_df = kb[kb.name == rest[ent]]
                        rest_df.reset_index()
                        api_feat[ent_cnt] = rest_df.iloc[0]['id']
                    else:
                        # api call features
                        if type(rest[ent]) == float:
                            api_feat[ent_cnt] = api_feat_values[ent][str(int(rest[ent]))]
                        else:
                            api_feat[ent_cnt] = api_feat_values[ent][rest[ent]]
                    ent_cnt += 1 # add counter for valid id entities


    return api_feat

def extract_features_subset(subset):

    for d,dial in enumerate(subset):
        # creating entities dict for current dialogue
        entity_dict = {'U':{ent: '' for ent in entities['U']}}
        entity_dict['S'] = {ent: [] for ent in entities['S']}
        dialog_data = np.ones((max_dial_len, total_feature_size))
        target_data = np.zeros((max_dial_len,1))
        if 'actions' in args.features:
            action_mask = np.zeros((max_dial_len,features_sizes['actions']))
        api_call = False # tracks if there was a previous api_call
        t_index = 0
        t_last_act_index = -1 # if one wants to use the previous turn action in the feature vector
        for t,turn in enumerate(dial['turns']):
            entity_dict = track_entities(turn, entity_dict)
            if 'U_proc' not in turn:
                continue
            target_data[t_index] = system_utterances.index(process_utt(turn['S_proc'], kb))
            feat_values = {}
            feat_vec = []

            if 'wrd_emb' in args.features:
                feat_values['wrd_emb'] = get_utterance_embedding(glove_model,turn['U'],glove_dim)
            if 'bow' in args.features:
                feat_values['bow'] = bow.transform([turn['U_proc']]).toarray().reshape((features_sizes['bow'],))
            if 'context' in args.features:
                feat_values['context'] = get_context_features(entity_dict)
            if 'previous_action' in args.features:
                feat_values['previous_action'] = get_previous_action(dial['turns'],t_last_act_index)
            if 'api' in args.features:
                feat_values['api'] = get_api_features(entity_dict)
            if 'actions' in args.features:
                feat_values['actions'] = get_action_mask(entity_dict,api_call)
                action_mask[t_index,:] = feat_values['actions']

            for f in feat_values:
                feat_vec += feat_values[f].tolist()

            dialog_data[t_index,:] = np.array(feat_vec,dtype=float)
            t_last_act_index = t
            t_index += 1

        logging.info('Creating file {}.hdf5'.format(os.path.join(data_output_dir,str(d))))
        if 'actions' in args.features:
            data_to_h5(os.path.join(data_output_dir, '{}.hdf5'.format(d)), dialog_data, target_data, action_mask)
        else:
            data_to_h5(os.path.join(data_output_dir,'{}.hdf5'.format(d)),dialog_data,target_data)

def compute_feature_values(kb, entities):

    cnt_values = {ent: '' for ent in entities['U']}

    for ent in entities['U']:
        unique_values = kb[ent].unique()
        cnt_values[ent] = {val: v for v,val in enumerate(unique_values)}

    return cnt_values

def compute_api_feat_val(kb):

    api_values = {c: '' for c in kb.columns if c not in ['id','name','R_address','R_phone']}

    for ent in kb.columns:
        if ent not in ['id','name','R_address','R_phone']:
            api_values[ent] = {val: v for v,val in enumerate(kb[ent].unique())}

    return api_values

parser = argparse.ArgumentParser(description='Dialogue Manager for HCN with the babi task datasets')
parser.add_argument('--embeddings_file','-e',type=str,help='File with embeddings')
parser.add_argument('--task_dir','-td',type=str,help='Folder with the dialogue tasks',required=True)
parser.add_argument('--task_num','-tn',type=str,help='Number of the task used',required=True)
parser.add_argument('--features','-f',type=str,nargs='+',help='features extract',default=['bow','wrd_emb','context','actions',
                                                                                          'previous_action','api'])

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

args = parser.parse_args()

babi_file_pattern = re.compile('dialog-babi-task{}-(.+?).txt'.format(args.task_num))

all_dialogues_set = {}
api_calls_set = {}

for txtfile in os.listdir(args.task_dir):
    if re.match(babi_file_pattern, txtfile):
        data_part = re.match(babi_file_pattern, txtfile).groups()
        task, set_def = data_part[0].rsplit('-', 1)
        if not os.path.isfile(os.path.join(args.task_dir,'{}_{}_exchanges.csv'.format(set_def,args.task_num))):
            logging.info('Parsing {}'.format(set_def))
            all_dialogues_set[set_def] = parse_dialogue_file(os.path.join(args.task_dir,txtfile))
        else:
            logging.info('Loading from {}'.format(set_def,args.task_num))
            all_dialogues_set[set_def] = load_dialogues_from_csv(args.task_dir,set_def,args.task_num)

    if txtfile.find('kb') > - 1:
        if args.task_num == '6' and txtfile.endswith('kb.txt'):
            kb = load_knowledge_base(os.path.join(args.task_dir,txtfile))
        elif txtfile.endswith('all.txt') and args.task_num != '6':
            kb = load_knowledge_base(os.path.join(args.task_dir,txtfile))

features_sizes = {}

# find max dialogue length and entities
max_dial_len = 0
for subset in all_dialogues_set:
    set_max_len, entities = get_max_len_entities(all_dialogues_set[subset])
    logging.info('Subset {} has max num of turns {}'.format(subset,set_max_len))
    if set_max_len > max_dial_len:
        max_dial_len = set_max_len


# set of system actions
action_set_file = os.path.join(args.task_dir,'babi_{}_action_set.txt'.format(args.task_num))
if not os.path.isfile(action_set_file):
    system_utterances = get_different_system_utterances(all_dialogues_set)
    with open(action_set_file,'wb') as lfp:
        pickle.dump(system_utterances,lfp)
else:
    logging.info('Loading system actions')
    with open(action_set_file,'rb') as lfp:
        system_utterances = pickle.load(lfp)

if 'wrd_emb' in args.features:
    glove_model, glove_dim = load_glove_vectors(args.embeddings_file)
    # glove_dim = 300
    features_sizes['wrd_emb'] = glove_dim

if 'bow' in args.features:
    bow, bow.size = load_bow(all_dialogues_set)
    features_sizes['bow'] = bow.size

if 'context' in args.features:
    features_sizes['context'] = len(entities['U'])
    cnt_feat_values = compute_feature_values(kb,entities)

if 'actions' in args.features:
    features_sizes['actions'] = len(system_utterances)

if 'previous_action' in args.features:
    features_sizes['previous_action'] = len(system_utterances)

if 'api' in args.features:
    api_feat_values = compute_api_feat_val(kb)
    features_sizes['api'] = 3*(len(api_feat_values) + 1) #uses features from the first three restaurants

print(features_sizes)

total_feature_size = sum(features_sizes.values())

logging.info('Complete feature size {}'.format(total_feature_size))

# extract features
for subset in all_dialogues_set:
    data_output_dir = os.path.join(args.task_dir, '_'.join(args.features), '{}_{}'.format(args.task_num, subset))
    if not os.path.isdir(data_output_dir):
        os.makedirs(data_output_dir)

    extract_features_subset(all_dialogues_set[subset])




