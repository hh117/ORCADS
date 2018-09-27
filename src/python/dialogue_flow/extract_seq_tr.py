import argparse
import json
import os,re

import sys
import yaml

def clean_utt(utt):

    cln_utt = re.sub('\.','',utt)
    cln_utt = re.sub('\?','',cln_utt)
    cln_utt = re.sub('\s+',' ',cln_utt)

    return cln_utt.strip()

def process_removable_words(utt):

    variants = []
    for w in utt.split():
        if w.startswith('*'):
            variants.append(re.sub('\s+', ' ', re.sub('\*{}'.format(w), '', utt)).strip())
            variants.append(re.sub('_',' ',re.sub('\*', '', utt)).strip())

    return variants

def extract_utt_for_acts(yaml_filename):
    '''
    Builds the set of utterance for each dialogue act based on the yaml file definition
    :return:
    '''

    da_dict = yaml.safe_load(open(yaml_filename, 'r').read())
    dact_utt = []
    for head_act in da_dict:
        for act in da_dict[head_act]:
            utterances = []
            if type(da_dict[head_act]) == type([]):
                dact_utt.append({'{}'.format(head_act):da_dict[head_act]})
                continue
            for utts in da_dict[head_act][act]:
                if type(utts) == type(''):
                    if utts.find('*') > -1:
                        utterances += process_removable_words(clean_utt(utts))
                    else:
                        utterances.append(clean_utt(utts))
                else:
                    for utt_sub in utts:
                        if utt_sub == 'add_on':
                            add_on_utt = []
                            for utt in utterances:
                                for add_utt in utts[utt_sub]:
                                    if add_utt.find('*') > -1:
                                        for utt_a in process_removable_words(clean_utt('{}, {}'.format(utt,add_utt))):
                                            add_on_utt.append(utt_a)
                                    else:
                                        add_on_utt.append('{}, {}'.format(clean_utt(utt),clean_utt(add_utt)))
                            utterances += add_on_utt
                        elif utt_sub == 'intro':
                            intro_utts = []
                            for utt in utterances:
                                for iu in utts[utt_sub]:
                                    if iu.find('*') > -1:
                                        for utt_c in process_removable_words(clean_utt('{} {}').format(iu,utt)):
                                            intro_utts.append(utt_c)
                                    else:
                                        intro_utts.append('{} {}'.format(clean_utt(iu),clean_utt(utt)))
                            utterances += intro_utts
                        else:
                            sub_utt_set = []
                            for u in utts[utt_sub]:
                                if u.find('*') > -1:
                                    sub_utt_set += process_removable_words(clean_utt(u))
                                else:
                                    sub_utt_set.append(clean_utt(u))
                            dact_utt.append({'{}({},{})'.format(head_act,act,utt_sub):sub_utt_set})

            if len(utterances) > 0:
                dact_utt.append({'{}({})'.format(head_act, act): utterances})

    return dact_utt

def find_dialogue_act(utt):

    for subject in dialogue_acts:
        for da in dialogue_acts[subject]:
            for act in da:
                for act_name in act:
                    if clean_utt(utt) in act[act_name]:
                        return act_name
                    else:
                        for sub_act in act[act_name]:
                            if type(sub_act) == type({}) and 'sequence' in sub_act:
                                if clean_utt(utt) in sub_act['sequence']:
                                    return act_name



    if 'db' in utt.split('_'):
        return utt
    print('No pattern found for utterance: {}'.format(clean_utt(utt)))
    sys.exit()

def get_dialogue_acts(raw_utterance):

    utt_da_list = []
    for utt_act in re.split('\. |\!',raw_utterance):
        utt_da_list.append(find_dialogue_act(utt_act))

    return utt_da_list

def create_dialogue_act_sequence(dialogue):

    da_list = []
    print('Creating dialogue act sequence for {}'.format(dialogue))
    for line in open(dialogue,'r'):
        subject, utterance = line.strip().split(':',1)
        if utterance.strip() == ' ':
            break
        for da in get_dialogue_acts(utterance.strip().lower()):
            if subject == args.participant or args.participant == 'all':
                da_list.append(('{}_{}'.format(subject,da)))

    return da_list


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Extract sequences, transitions and nlu from dialogues')
    parser.add_argument('--dialogue_dir', '-d', type=str, help='directory where the dialogues are stored')
    parser.add_argument('--dialogue_acts', '-da',type=str, help='directory with the dialogue acts definition')
    parser.add_argument('--participant','-p',type=str, help='filter acts by participant', default='all')

    args = parser.parse_args()


    for root,dir,files in os.walk(args.dialogue_acts):
        if root == args.dialogue_acts:
            dialogue_acts = {x:[] for x in dir}
        for file in files:
            if file.endswith('yaml'):
                dialogue_acts[root.split(os.sep)[-1]].append(extract_utt_for_acts(os.path.join(root, file)))

    print(json.dumps(dialogue_acts,indent=2))
    dialogues = {}
    for dialogue_file in os.listdir(args.dialogue_dir):
        if dialogue_file.endswith('txt'):
            dialogues[dialogue_file.split('.')[0]] = create_dialogue_act_sequence(os.path.join(args.dialogue_dir,dialogue_file))

    transitions = {}
    for d in dialogues:
        for t,turn in enumerate(dialogues[d]):
            if turn not in transitions:
                transitions[turn] = []
            if t < len(dialogues[d]) - 1:
                if dialogues[d][t+1] not in transitions[turn]:
                    transitions[turn].append(dialogues[d][t+1])

    if not os.path.isfile(os.path.join(args.dialogue_dir,'transitions.json')):
        with open(os.path.join(args.dialogue_dir,'transitions.json'),'w') as f:
            f.write(json.dumps(transitions,indent=2))
