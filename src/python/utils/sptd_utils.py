import json
import re,os,sys
import xml.etree.ElementTree as ET
import logging

import h5py
from keras.utils import np_utils
from keras.layers import Bidirectional
from keras.layers.core import Dense, Dropout,Masking
from keras.layers.recurrent import LSTM
from keras.layers.wrappers import TimeDistributed
from keras.optimizers import Adagrad
from keras import Sequential
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

import picdef
import numpy as np

from babi_utils import get_all_utterances


class SceneObject(object):
    def __init__(self, node):
        super(SceneObject, self).__init__()
        self.picId = node.id
        self.num = node.num
        self.visible = node.visible
        self.group = node.group
        self.differs = node.differs
        self.color = node.attributes.color
        self.name = node.attributes.name
        self.propertyOf = node.attributes.property_of
        self.prep = node.attributes.property_of.prep
        self.x = int(node.attributes.x)
        self.y = int(node.attributes.y)
        self.radius = int(node.attributes.radius)
        self.property = node.attributes.property_
        self.clicked = False
        self.childrenObjects = []
        self.parentObject = ''
        self.clickDistance = 10000.0
        if self.group:
            for childObj in node.object:
                self.childrenObjects.append(SceneObject(childObj))

class SceneObjectGroup(SceneObject):
    def __init__(self, node):
        SceneObject.__init__(self, node)
        self.groupMembers = []
        if self.group:
            for grpObj in node.object:
                self.groupMembers.append(SceneObject(grpObj))


def clean_recurr(match):
    '''
    :param match: performed match function
    :return: pattern within the match cleaned
    '''

    cleanString = match.group(1)
    if cleanString.find('%') > -1:
        cleanString = re.sub('%', '', cleanString)
    if cleanString.find('=') > -1:
        cleanString = re.sub('=', '', cleanString)
    if cleanString.find('-') > -1:
        cleanString = re.sub('-', '', cleanString)
    if cleanString.find('+') > -1:
        cleanString = re.sub('\\+', '', cleanString)

    return cleanString

def clean_transcription(transcription):
    '''

    :param transcription: transcription with disfluency content information
    :return: clean transcription without disfluency content
    '''

    repetitionPattern = re.compile('<+(.+?)>+')
    transClean = transcription
    while re.search(repetitionPattern, transClean):
        transClean, numSubs = repetitionPattern.subn(clean_recurr, transClean)
    # hack to remove whatever hasn't been removed in the previous step
    transClean = re.sub('<', '', transClean)
    transClean = re.sub('>', '', transClean)
    disflPattern = re.compile(r'\((.+?)\)')
    transClean = disflPattern.sub(clean_recurr, transClean)
    transClean.replace(r"\(.*\)", "")
    transClean = re.sub('\\+', ' ', transClean)
    transClean = re.sub('\\-', ' ', transClean)
    transClean = re.sub('\\*', ' ', transClean)
    transClean = re.sub('\(', ' ', transClean)
    transClean = re.sub('\%hesitation', ' ', transClean)
    transClean = re.sub('=\)', ' ', transClean)
    transClean = re.sub('\%', ' ', transClean)
    transClean = re.sub('\~', ' ', transClean)
    transClean = re.sub('\?', ' ', transClean)
    transClean = re.sub('\.', ' ', transClean)
    transClean = re.sub('\*', ' ', transClean)
    transClean = re.sub(' +', ' ', transClean)  # remove multiple spaces

    return transClean.strip().lower()


def _getChildrenObjects(sObject,flatList):

    for cObj in sObject.childrenObjects:
        cObj.parentObject = sObject.picId
        flatList.append(cObj)
        if cObj.group:
            _getChildrenObjects(cObj,flatList)

def get_flat_object_list(listOfObjects):

    flatObjectList = []
    for sObj in listOfObjects:
        flatObjectList.append(sObj)
        if sObj.group:
            _getChildrenObjects(sObj,flatObjectList)

    return flatObjectList

def get_obj_list(scene):

    #tree = ET.parse(scene_file)
    #root = tree.getroot()

    #print(root)
    listOfObjectsInPicture = []

    for objectP in scene.object:
        if objectP.group:
            listOfObjectsInPicture.append(SceneObjectGroup(objectP))
        else:
            listOfObjectsInPicture.append(SceneObject(objectP))

    return listOfObjectsInPicture


def load_scenes_def(scenes_dir):

    scene_def_dict = {}

    scene_xml_pattern = re.compile('(\w+)(\d).xml')

    for root, dir, files in os.walk(scenes_dir):
        for file in files:
            if re.match(scene_xml_pattern,file):
                scene_name, id = re.match(scene_xml_pattern,file).groups()
                if not scene_name in scene_def_dict:
                    scene_def_dict[scene_name] = {}
                scene = picdef.CreateFromDocument(open(os.path.join(root,file)).read())
                usr_role = 'if' if int(id) == 1 else 'ig'
                scene_def_dict[scene_name][usr_role] = get_flat_object_list(get_obj_list(scene))

    return scene_def_dict

def load_glove_vectors(glove_file_location):
    if not os.path.isfile(glove_file_location):
        logging.error('Couldn\'t find file {}'.format(glove_file_location))
        sys.exit()
    logging.info('Loading Glove Vector')
    f = open(glove_file_location,'r')
    model = {}
    for line in f:
        splitline = line.split()
        word = splitline[0]
        emmbedding = np.array([float(val) for val in splitline[1:]])
        model[word] = emmbedding
        dim = model[word].shape[0]
    model['<EOS>'] = 2 * np.random.random((dim,)) - 1 #randomly assigning a value to the end of sentence
    model['OOV'] = 2 * np.random.random((dim,)) - 1 #randomly assigning a value to OOV words
    model['<SILENCE>'] = 2 * np.random.random((dim,)) - 1 #randomly assigning the same value for <SILENCE>
    logging.info('{} words load'.format(len(model)))
    return model,dim

def get_scene_max_utt_len(scene_json):

    scene_dict = json.load(open(scene_json,'r'))

    max_utt_len = 0
    for turn in scene_dict['turns']:
        turn_len = len(turn['utterance'].split())
        if turn_len > max_utt_len:
            max_utt_len = turn_len

    return max_utt_len

def get_max_utt_length(datadir,spdt_def):

    max_utt_length = 0

    for session in spdt_def['sessions']:
        session_dict = json.load(open(os.path.join(datadir,session['dialogue_id'],session['session_json_file']),'r'))
        if 'scenes' in session_dict:
            for scene in session_dict['scenes']:
                scene_json_file = os.path.join(datadir, session['dialogue_id'],
                                               session_dict['scenes'][scene]['scene_file'])
                print(scene_json_file)
                if os.path.isfile(scene_json_file):
                    session_max_utt = get_scene_max_utt_len(scene_json_file)
                    if session_max_utt > max_utt_length:
                        max_utt_length = session_max_utt
        break

    return max_utt_length

def get_feature_size_from_data(file_name,action_mask=False):

    if not os.path.isfile(file_name):
        logging.error('File {} doesn\'t exist'.format(file_name))

    logging.info('Loading from {}'.format(file_name))
    data = h5py.File(file_name,'r')
    if action_mask:
        return data['features'].shape[0],data['features'].shape[1],data['action'].shape[1]
    else:
        return data['features'].shape

def get_nclases(h5py_file_list,max_utt_len):

    classes = []

    for f in h5py_file_list:
        data = h5py.File(f)
        try:
            target_values = np.empty((max_utt_len,1))
            target_values[:,:] = data['target']
        except:
            logging.warning('{} has no targets'.format(f))
            continue
        for un in np.unique(target_values):
            if un not in classes:
                classes.append(un)

    return len(classes)

def load_data(data_dir, max_tensor_len, feat_size, num_classes, action_set_size='', mode='', extension='hdf5'):
    data_files_list = [os.path.join(data_dir, dialogue_file) for dialogue_file in os.listdir(data_dir) if
                       dialogue_file.endswith(extension)]

    if mode == 'la':
        return load_data_la(data_files_list, max_tensor_len, feat_size, num_classes)
    elif mode == 'action_mask':
        return load_data_action_mask(data_files_list, max_tensor_len, feat_size, num_classes, action_set_size)
    else:
        return load_data_reg(data_files_list, max_tensor_len, feat_size, num_classes)


def load_data_reg(data_files_list, max_tensor_len, feat_size, n_classes):

    data_matrix = np.empty((len(data_files_list), max_tensor_len, feat_size))
    target_matrix = np.empty((len(data_files_list), max_tensor_len, n_classes))
    for f,file in enumerate(data_files_list):
        data = h5py.File(file)
        data_matrix[f] = data['features']
        target_matrix[f] = np_utils.to_categorical(data['target'],num_classes=n_classes)

    return data_matrix,target_matrix

def load_data_action_mask(data_files_list, max_tensor_len, feat_size, num_classes, action_set_size):

    print(len(data_files_list), max_tensor_len, action_set_size)

    data_matrix = np.empty((len(data_files_list), max_tensor_len, feat_size))
    target_matrix = np.empty((len(data_files_list), max_tensor_len, num_classes))
    action_mask_matrix = np.empty((len(data_files_list), max_tensor_len, action_set_size))

    for f,file in enumerate(data_files_list):
        data = h5py.File(file)
        data_matrix[f] = data['features']
        target_matrix[f] = np_utils.to_categorical(data['target'],num_classes=num_classes)
        action_mask_matrix[f] = data['action']

    return data_matrix,target_matrix,action_mask_matrix

def load_data_la(data_files_list, max_tensor_len, feat_size, n_classes):

    data_matrix = np.empty((len(data_files_list), max_tensor_len, 3 * feat_size))
    target_matrix = np.empty((len(data_files_list), max_tensor_len, n_classes))

    for f, file in enumerate(data_files_list):
        data = h5py.File(file)
        target_matrix[f] =  np_utils.to_categorical(data['target'],num_classes=n_classes)
        sentence_matrix = np.empty((max_tensor_len, feat_size))
        sentence_matrix[:][:] = data['features']
        for w in range(sentence_matrix.shape[0]):
            # looking into the previous word
            if w == 0:
                previous_word = np.ones((feat_size,))
            else:
                previous_word = sentence_matrix[w-1][:]

            # looking into the next word
            if w == sentence_matrix.shape[0] - 1:
                next_word = np.ones((feat_size))
            else:
                next_word = sentence_matrix[w+1][:]

            data_matrix[f][w][:] = np.hstack((previous_word,sentence_matrix[w][:],next_word))

    return data_matrix,target_matrix

def data_to_h5(outputfile,input_data,target_data=[],action_mask=[]):

    if os.path.isfile(outputfile):
        logging.warning('{} already exists'.format(outputfile))
    else:
        data_f = h5py.File(outputfile,'w')
        data_f.create_dataset('features',data=input_data)
        if target_data.size:
            data_f.create_dataset('target',data=target_data)
        if not type(action_mask) == type([]):
            data_f.create_dataset('action',data=action_mask)
        data_f.close()

def configure_model(input_size, n_classes, layers, lstm_type='', optimizer = Adagrad()):

    model = Sequential()
    model.add(Masking(mask_value=1., input_shape=(None, input_size)))

    for l, layer in enumerate(layers):
        if l == 0:
            if lstm_type == 'b':
                logging.info('Using bidirectional LSTM')
                model.add(Bidirectional(LSTM(layer, input_shape=(None, input_size), dropout=0.1, return_sequences=True, recurrent_dropout=0.1)))
            else:
                model.add(LSTM(layer, input_shape=(None, input_size), dropout=0.1, recurrent_dropout=0.1, return_sequences=True))
        else:
            model.add(TimeDistributed(Dense(layer,activation='relu')))
            model.add(Dropout(0.1))

        model.add(TimeDistributed(Dense(n_classes,activation='softmax')))

        model.compile(loss='categorical_crossentropy',optimizer=optimizer,metrics=['accuracy'])

    return model


def load_bow(data_files_dict):

    all_utterances = []
    for subs in data_files_dict:
        all_utterances += get_all_utterances(data_files_dict[subs])
    corpus_vect = CountVectorizer(binary=True)
    corpus_counts = corpus_vect.fit_transform(all_utterances)
    corpus_tfidf = TfidfTransformer(use_idf=False).fit(corpus_counts)
    return corpus_vect, corpus_counts.shape[1]