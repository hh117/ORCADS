import yaml


class DialogueConfig():

    def __init__(self,dialogue_config_file):

        config_file = yaml.safe_load(open(dialogue_config_file).read())
        self.furhat_ip = config_file['furhat']['ip']
        self.farmi_dir = config_file['farmi_dir']
        self.pre_defined_utt = []
        for utt in config_file['predefined']:
            self.pre_defined_utt.append(utt)
        if 'emergency_location' in config_file:
            self.emergency_location = config_file['emergency_location']
        else:
            self.emergency_location = 'safe'

