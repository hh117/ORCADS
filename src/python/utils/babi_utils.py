import re,os,sys
import logging
import pandas as pd

entities_patt = re.compile('<(.+?)>')

#list of utterances used to reject what was offered to the user
reject_offer = ['no this does not work for me','no i don\'t like that','do you have something else']

def get_matched_slots(wrd,kb):

    slots = []
    for field in kb:
        if kb[field].dtype == int:
            continue
        rest_df = kb[kb[field] == wrd]
        if not rest_df.empty:
            slots.append(field)

    return list(set(slots))

def load_dialogues_from_csv(task_dir,subset,task_num):

    dialogues_df = pd.read_csv(os.path.join(task_dir, '{}_{}_exchanges.csv'.format(subset, task_num)))

    dialogues = []
    for dial in dialogues_df.dialogue.unique():
        dial_df = dialogues_df[dialogues_df.dialogue == dial]
        turns = []
        dialogue = {'id': dial}
        for turn, row in dial_df.iterrows():
            #if row['name'] != '':
            if pd.isnull(row['name']):
                turns.append({'S_proc': row['S_proc'], 'U_proc': row['U_proc'], 'S': row['S'], 'U': row['U']})
            else:
                api_dict = {'name': row['name']}
                for ent in dial_df:
                    if ent not in ['dialogue','ent','nan']:
                        if not pd.isnull(row[ent]):
                            api_dict[ent] = row[ent]
                turns.append(api_dict)

        dialogue['turns'] = turns
        dialogues.append(dialogue)

    return dialogues


def get_slots_from_utterance(turn,kb):

    matched_slots = []
    for wrd in turn.split():
        slots = get_matched_slots(wrd,kb)
        if slots != []:
            if len(slots) > 1:
                print(turn, wrd)
                exit()
            matched_slots.append(slots[0])
        else:
            matched_slots.append('')

    return matched_slots

def process_utt(utt,kb):
    slots = get_slots_from_utterance(utt,kb)
    wrds_turn = utt.split()
    action = []
    for s, slt in enumerate(slots):
        if slt == '':
            action.append(wrds_turn[s])
        else:
            action.append('<{}>'.format(slt))

    return ' '.join(action)


def get_all_utterances(data_file):
    all_utterances = []

    for d in data_file:
        for t in data_file[d]:
            if 'U_proc' not in t:
                continue
            if t['U_proc'] not in all_utterances:
                all_utterances.append(t['U_proc'])
            if t['S_proc'] not in all_utterances:
                all_utterances.append(t['S_proc'])

    return all_utterances

def query_kb(value,field,kb):

    db_results = []
    for entry in kb:
        if entry[field] == value:
            db_results.append(entry)

    return db_results

def get_max_len_entities(subset):

    max_len_subset = 0
    entities = {'U': [], 'S': ['restaurants']}
    for dial in subset:
        n_turns = 0
        for turn in dial['turns']:
            if 'U_proc' not in turn:
                continue
            n_turns += 1 # only turns that have some sort of user content should be taken into account
            if re.findall(entities_patt,turn['U_proc']):
                ent = re.findall(entities_patt,turn['U_proc'])
                for e in ent:
                    if e not in entities['U'] and e.find('SILENCE') == -1:
                        entities['U'].append('{}'.format(e))

        if n_turns > max_len_subset:
            max_len_subset = n_turns

    # by default there is an entity called restaurants where all the query results are going to be placed
    return max_len_subset, entities

def get_restaurant(turn,entity_dict):

    for res in entity_dict['S']['restaurants']:
        if res['name'] == turn['name']:
            return res

    return {'name': turn['name']}

def sort_list_restaurants(list_rest):

    try:
        return sorted(list_rest,key=lambda k: k['R_rating'],reverse=True)
    except:
        return list_rest


def update_resturante_entry(rest,entity_dict):

    for r in entity_dict['S']['restaurants']:
        if r['name'] == rest['name']:
            r = dict(r,**rest)
            return sort_list_restaurants(entity_dict['S']['restaurants'])

    entity_dict['S']['restaurants'].append(rest)
    return sort_list_restaurants(entity_dict['S']['restaurants'])


def track_entities(turn, entity_dict):

    if turn['S'] == 'api_res':

        rest = get_restaurant(turn,entity_dict)

        for ent in turn:
            if ent not in ['S','S_proc','turn']:
                rest[ent] = turn[ent]

        entity_dict['S']['restaurants'] = update_resturante_entry(rest,entity_dict)

    else:
        turn_words = turn['U'].split()
        if turn['U'] in reject_offer and len(entity_dict['S']['restaurants']) > 0:
            # removes current top restaurant from list
            del entity_dict['S']['restaurants'][0]
        for w,word in enumerate(turn['U_proc'].split()):
            if re.search(entities_patt,word):
                ent = re.search(entities_patt,word).group(1)
                if ent not in entity_dict['U'] and ent != 'SILENCE':
                    logging.error('{} was not found in the original entity dictionary {}'.format(ent, entity_dict))
                    sys.exit()
                elif ent == 'SILENCE':
                    continue
                entity_dict['U'][ent] = turn_words[w]

    return entity_dict
