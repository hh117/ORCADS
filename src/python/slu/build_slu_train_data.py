import argparse
import json
import os,logging

import h5py
import pandas as pd
import sys

from sptd_utils import *

def tag_word(wrd,scene_xml):

    for obj in scene_xml:
        if wrd in obj.name:
            return 'B-object'
        if wrd in obj.color:
            return 'B-color'
        if wrd == obj.propertyOf._complexTypeDefinition__content:
            return 'B-landmark'

    return 'O'

def analyse_transcript(transcript, scene, speaker):

    scene_xml_dict = scns[scene][speaker]
    utterances_tags = []

    wrds_trns = transcript.split()

    for w in range(len(wrds_trns)):
        if len(utterances_tags) != w:
            continue
        if wrds_trns[w] == scene:
            utterances_tags.append('B-scene')
            continue

        if w < len(wrds_trns)-1:
            consec_words = '{} {}'.format(wrds_trns[w],wrds_trns[w+1])
            consec_words_tag = tag_word(consec_words,scene_xml_dict)
            if consec_words != wrds_trns[w]:
                if consec_words_tag != 'O':
                    utterances_tags.append(consec_words_tag)
                    utterances_tags.append(re.sub('B','I',consec_words_tag))
                    w += 1
                    continue

        utterances_tags.append(tag_word(wrds_trns[w],scene_xml_dict))

    if len(wrds_trns) != len(utterances_tags):
        logging.warning('Not all words were tagged')

    return utterances_tags

def parse_scene_file(scene_json,scene_name):

    scene_dict = json.load(open(scene_json,'r'))
    roles_dict = {scene_dict['instruction_giver']['id']: 'ig',scene_dict['instruction_follower']['id']: 'if'}

    scene_annotated_dict = []

    for turn in scene_dict['turns']:
        if turn == '':
            logging.info('Empty turn in {} {}'.format(scene_name,turn['turn-index']))
            continue
        trns_list = clean_transcription(turn['utterance']).split()
        trns_list.append('<EOS>')
        tag_list = analyse_transcript(clean_transcription(turn['utterance']),scene_name,roles_dict[turn['speaker']])
        tag_list.append('_'.join(turn['topic'].split()))
        scene_annotated_dict.append({'W': '|'.join(trns_list),
                                     'S': '|'.join(tag_list),
                                     'U': turn['speaker'],
                                     'scene': scene_name,
                                     })

    return pd.DataFrame(scene_annotated_dict)

def extract_features(train_df):

    for scene in train_df.scene.unique():
        scene_df = train_df[train_df.scene == scene]
        scene_df = scene_df.reset_index()
        for index, row in scene_df.iterrows():
            features_data = np.ones((max_utterance,model_dim))
            targets = np.ones((max_utterance,1))*len(list_possible_targets)
            target_values = row['S'].split('|')
            for w,wrd in enumerate(row['W'].split('|')):
                try:
                    features_data[w] = glove_model[wrd]
                except:
                    features_data[w] = glove_model['OOV']
                    logging.info('{} not found in the glove model'.format(wrd))

                targets[w] = list_possible_targets.index(target_values[w])

            if not os.path.isdir(row['subset']):
                os.makedirs(row['subset'])

            data_to_h5(os.path.join(row['subset'],'{}_{}_{}.hdf5'.format(row['U'],scene,index)),features_data,targets)

def parse_session_file(session_file):

    session_dict = json.load(open(session_file,'r'))

    slu_train_df = pd.DataFrame()

    if 'scenes' in session_dict:
        for scene in session_dict['scenes']:
            logging.info('Analysing {}'.format(scene))
            scene_json_file = os.path.join(args.datadir,session['dialogue_id'],session_dict['scenes'][scene]['scene_file'])
            if os.path.isfile(scene_json_file):
                slu_scene_df = parse_scene_file(scene_json_file,scene)
                slu_train_df = slu_train_df.append(slu_scene_df,ignore_index=True)
            else:
                logging.error('Scene file {} could not be found'.format(scene_json_file))

    return slu_train_df


def get_max_utt_df(train_df):

    train_df['length'] = train_df.W.apply(lambda x: len(x.split('|')))

    return train_df.length.max()

def get_targets(train_df):

    targets = []

    for index, row in train_df.iterrows():
        for tag in row['S'].split('|'):
            if tag not in targets:
                targets.append(tag)

    return targets

def set_partitions(train_df,dr=[0.7,0.2]):

    train_df = train_df.sample(frac=1).reset_index(drop=True)
    n_train = int(dr[0]*len(train_df))
    n_test = n_train + int(dr[1]*len(train_df))
    train_df['subset'] = train_df.index.to_series().apply(lambda x: 'train' if x < n_train else ( 'test' if x < n_test else 'val'))

    return train_df


parser = argparse.ArgumentParser(description='Builds dataset to train an slu for the sptd data')
parser.add_argument('--datadir','-d',type=str,help='directory where the data is located',required=True)
parser.add_argument('--datafile','-df',type=str,help='file with the dataset definition',required=True)
parser.add_argument('--scenes_dir','-sd',type=str,help='directory where the scenes xml defintion is stored')
parser.add_argument('--glove_file','-fg',type=str,help='file with the glove vectors',default='/Users/jdlopes/GloVe/glove.42B.300d.txt')

#adding logger
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

args = parser.parse_args()

scns = load_scenes_def(args.scenes_dir)

if os.path.isfile('train_slu.csv'):
    slu_train_df = pd.read_csv('train_slu.csv')
else:
    spdt_def = json.load(open(args.datafile, 'r'))
    slu_train_df = pd.DataFrame()
    for session in spdt_def['sessions']:
        logging.info('Analysing {}'.format(session['dialogue_id']))
        session_df = parse_session_file(
            os.path.join(args.datadir, session['dialogue_id'], session['session_json_file']))
        slu_train_df = slu_train_df.append(session_df,ignore_index=True)
    slu_train_df = set_partitions(slu_train_df)
    slu_train_df.to_csv('train_slu.csv',index=False)

max_utterance = get_max_utt_df(slu_train_df)
logging.info('Longest utterance found was {} words'.format(max_utterance))
list_possible_targets = get_targets(slu_train_df)

print(list_possible_targets,len(list_possible_targets))

glove_model,model_dim = load_glove_vectors(args.glove_file)

extract_features(slu_train_df)





