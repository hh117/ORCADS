import re

def preProcess(utt,dialogue_config):
    '''
    Removes gestures from the sentences before sending them to the wizard interefaces
    :param utt:
    :return:
    '''

    gesture = []

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
            #if args.furhat:
            field = match.group(p)
            # checks input parameters
            input_parameters = [x for x in field.split('.')]
            # if the attendee is defined in the parameters set it
            #print(field)
            parameter = input_parameters[-1][:-1]
            if len(input_parameters) > 2:
                attend = input_parameters[1]
                utt = re.sub(field, dialogue_config.participants[attend][parameter], utt)
            elif len(input_parameters) == 2:
                attend = input_parameters[0][1:0]
                print(attend, parameter)
                utt = re.sub(field, dialogue_config.participants[attend][parameter], utt)

    return utt.strip(),';'.join(gesture)
