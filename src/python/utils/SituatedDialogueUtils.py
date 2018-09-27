import logging
import re

def preProcess(utt,situation_kb,state):
    '''
    Removes gesture tags from the sentences before sending them to the wizard interface
    and replaces fields with values from the situation knowledge base
    :param utt:
    :return:
    '''

    gesture = []
    communicative_acts = []

    gesture_regex = r'<(.+?)>'
    for gesture_match in re.finditer(gesture_regex,utt):
        for g in range(len(gesture_match.groups())):
            # remove pattern for the utterance
            utt = re.sub(gesture_match.group(g),'',utt)
            gesture.append(gesture_match.group(g)[1:-1])

    curly_braces_regex = re.compile("\{(.*?)\}")
    matches = re.finditer(curly_braces_regex,utt)
    slots_to_replace = []
    if not curly_braces_regex.search(utt):
        logging.info('No field to replace')
        communicative_acts.append({'utterance': utt, 'gestures':';'.join(gesture)})
    else:
        for match in matches:
            for p in range(len(match.groups())):
                matched_field = match.group(p)
                slots_to_replace.append(matched_field[1:-1])

        if not set(slots_to_replace).issubset(set(situation_kb.keys())):
            logging.info('Not all slots {} were available in the situation kb to build {}'.format(','.join(slots_to_replace),utt))
            return []
        else:
            for slot in slots_to_replace:
                if len(situation_kb[slot]) == 0:
                    return []
                for item in situation_kb[slot]:
                    communicative_acts.append({'utterance':re.sub('{{{}}}'.format(slot), item['name'], utt).strip(),'gestures':';'.join(gesture)})

    return communicative_acts
