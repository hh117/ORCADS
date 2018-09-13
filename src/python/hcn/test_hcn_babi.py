import argparse,logging
import json
import re,os
import sys
import numpy as np
import pickle
from numpy import random
from sklearn.metrics import accuracy_score

from sptd_utils import configure_model, get_feature_size_from_data, get_nclases, load_data
from babi_utils import *

def place_entities(prompt,entity_dict):

    entity_regex = re.compile('<(.+?)>')

    post_processed_prompt = prompt

    for ent in re.findall(entity_regex,prompt):
        if prompt.find('api_call') > -1:
            post_processed_prompt = re.sub('<{}>'.format(ent),entity_dict['U'][ent],post_processed_prompt)
        else:
            try:
                top_rest = entity_dict['S']['restaurants'][0]
                post_processed_prompt = re.sub('<{}>'.format(ent),top_rest[ent],post_processed_prompt)
            except:
                #print(prompt,json.dumps(entity_dict,indent=2))
                continue

    return post_processed_prompt

def get_next_valid_turn(t_index,dialogue,entity_dict):

    for t in range(t_index+1,len(dialogue)):
        if 'U_proc' in dialogue[t]:
            return t,entity_dict
        else:
            entity_dict = track_entities(dialogue[t], entity_dict)

    return len(dialogue),entity_dict

def get_dialogue_turns(file_id,dialogues):

    file_name = file_id.split(os.sep)[-1]
    dial_id = file_name.split('.')[0]

    for d in dialogues:
        if str(d['id']) == dial_id:
            return d['turns']

    return {}

def compute_scores():

    test = np.argmax(y_test,axis=-1)
    pred = np.argmax(y_pred,axis=-1)

    correct_prediction = []
    dialogue_success = []

    actions_test = []
    actions_pred = []

    # loop over dialogues
    for d in range(test.shape[0]):
        dialogue_turns = get_dialogue_turns(tst_files[d],test_dialogues)
        current_dialogue = []
        t_index = -1
        entity_dict = {'U': {ent: '' for ent in entities['U']}}
        entity_dict['S'] = {ent: [] for ent in entities['S']}
        # loop over turns
        for t in range(test.shape[1]):
            if not np.all(x_test[d, t, :] == 1):
                if 'actions' in args.features:
                    print(pred[d,t],np.argmax(action_mask_test[d,t]*y_pred[d,t]))
                    sys.exit()
                t_index, entity_dict = get_next_valid_turn(t_index,dialogue_turns,entity_dict)
                entity_dict = track_entities(dialogue_turns[t_index], entity_dict)
                if dialogue_turns[t_index]['S'] == place_entities(system_actions[pred[d,t]],entity_dict):
                    current_dialogue.append(1)
                else:
                    current_dialogue.append(0)
                actions_test.append(test[d,t])
                actions_pred.append(pred[d,t])

        # if all the predictions were correct
        if sum(current_dialogue) == len(current_dialogue):
            dialogue_success.append(1)
        else:
            dialogue_success.append(0)

        correct_prediction += current_dialogue

    return accuracy_score(actions_test,actions_pred),sum(correct_prediction)/len(correct_prediction),sum(dialogue_success)/len(dialogue_success)

parser = argparse.ArgumentParser()
parser.add_argument('--datadir','-d',type=str,help='Home directory of the data',required=True)
parser.add_argument('--test_data','-t',type=str,help='directory with test data',required=True)
parser.add_argument('--features','-f',type=str,nargs='+',help='features used in the training',default=['bow','wrd_emb','context','actions',
                                                                                          'previous_action','api'])

random.seed(42)

args = parser.parse_args()

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

test_data_path = os.path.join(args.datadir,'_'.join(args.features),args.test_data)
task_num,subset = args.test_data.split('_')
test_dialogues = load_dialogues_from_csv(args.datadir,subset,task_num)
set_max_len, entities = get_max_len_entities(test_dialogues)

action_set_file = os.path.join(args.datadir, 'babi_{}_action_set.txt'.format(task_num))
with open(action_set_file, 'rb') as lfp:
    system_actions = pickle.load(lfp)

model_path = os.path.join(args.datadir,'_'.join(args.features),'models')

if not os.path.isdir(model_path):
    logging.error('No models created with the feature set {}'.format('_'.join(args.features)))
    sys.exit()

model_pattern = re.compile('LSTM(\d+)_epochs(\d+)')

models_dict = []

for file_name in os.listdir(model_path):
    if re.match(model_pattern,file_name):
        layer_sizes, epochs = re.match(model_pattern,file_name).groups()
        layer_sizes = [int(l) for l in layer_sizes.split('_')]
        models_dict.append({'path': os.path.join(model_path,file_name), 'layer_sizes': layer_sizes})
    else:
        logging.info('{} not in the model format LSTM<layers>_epochs<num_epochs>'.format(file_name))

tst_files = [os.path.join(test_data_path,file) for file in os.listdir(test_data_path) if file.endswith('hdf5')]

if tst_files != []:
    if 'actions' in args.features:
        max_dial_len, feat_size, action_mask_size = get_feature_size_from_data(tst_files[0],True)
    else:
        max_dial_len, feat_size = get_feature_size_from_data(tst_files[0])
    n_classes = get_nclases(tst_files,max_dial_len)
else:
    logging.error('Couldn\'t find any file in the testing dir')

if 'actions' in args.features:
    x_test, y_test, action_mask_test = load_data(os.path.join(test_data_path),max_dial_len,feat_size,
                                                 n_classes,action_set_size=action_mask_size, mode='action_mask')
else:
    x_test, y_test = load_data(os.path.join(test_data_path), max_dial_len, feat_size, n_classes)


for model_entry in models_dict:
    model = configure_model(feat_size, n_classes, model_entry['layer_sizes'])
    model.load_weights(model_entry['path'])

    y_pred = model.predict(x_test)

    acc_no_ent, acc_ent, dial_succ = compute_scores()
    print('Acc (without entitity repalcement) [{}]: {:.4f}'.format(model_entry['path'].split(os.sep)[-1],acc_no_ent))
    print('Acc (entitity repalcement) [{}]: {:.4f}'.format(model_entry['path'].split(os.sep)[-1], acc_ent))
    print('Acc (dialogue level) [{}]: {:.4f}'.format(model_entry['path'].split(os.sep)[-1],dial_succ))


