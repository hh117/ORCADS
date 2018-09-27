import re

def preProcess(utt,situation_kb,state):
    '''
    Removes gesture tags from the sentences before sending them to the wizard interface
    and replaces fields with values from the situation knowledge base
    :param utt:
    :return:
    '''

    gesture = []

    da,context = state.split('_',1)

    gesture_regex = r'<(.+?)>'
    for gesture_match in re.finditer(gesture_regex,utt):
        for g in range(len(gesture_match.groups())):
            # remove pattern for the utterance
            utt = re.sub(gesture_match.group(g),'',utt)
            gesture.append(gesture_match.group(g)[1:-1])

    curly_braces_regex = r"\{(.*?)\}"
    matches = re.finditer(curly_braces_regex,utt)
    for match in matches:
        for p in range(len(match.groups())):
            matched_field = match.group(p)
            field = matched_field[1:-1]
            # there is no field to fill in that space in the knowledge base
            if field not in situation_kb:
                return None,''
            # checks input parameters
            if context in situation_kb[field]:
                cntx_filed = situation_kb[field][context]
            else:
                print(situation_kb[field])
            utt = re.sub(matched_field, cntx_filed['name'], utt)

    return utt.strip(),';'.join(gesture)
