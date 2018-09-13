import argparse,re,os

from keras.layers import Masking, Bidirectional, LSTM, TimeDistributed, Dense, Dropout
from keras.optimizers import Adagrad
from sklearn.metrics import f1_score, accuracy_score

from sptd_utils import *
from keras import Sequential


def compute_scores():

    test = np.argmax(y_test, axis=2)
    pred = np.argmax(y_pred, axis=2)

    all_tags_test = []
    all_tags_pred = []

    all_topic_test = []
    all_topic_pred = []

    for s in range(test.shape[0]):
        for w in range(test.shape[1]):
            if test[s,w] < n_classes:
                all_tags_test.append(test[s,w])
                all_tags_pred.append(pred[s,w])
                # only for topic. if end of utterance is reached
                if w < test.shape[1]-1 and test[s,w+1] == n_classes-1:
                    all_topic_test.append(test[s,w])
                    all_topic_pred.append(pred[s,w])
                    break
                if w == test.shape[1]-1:
                    all_topic_test.append(test[s,w])
                    all_topic_pred.append(pred[s,w])

    print('F-score (all tags): {}'.format(f1_score(all_tags_test,all_tags_pred,average='macro')))
    print('F-score (topic): {}'.format(f1_score(all_topic_test,all_topic_pred,average='macro')))

    print('Acc (all_tags): {}'.format(accuracy_score(all_tags_test,all_tags_pred)))
    print('Acc (topic): {}'.format(accuracy_score(all_topic_test,all_topic_pred)))


def load_model(feat_size):

    if model_config.find('LSTM') > -1:

        model = Sequential()

        model.add(Masking(mask_value=1.,input_shape=(None,feat_size)))

        for l, layer in enumerate(n_layers.split('_')):
            if l == 0:
                if model_config.startswith('b'):
                    logging.info('Using bidirectional LSTM')
                    print(layer,l,feat_size)
                    model.add(Bidirectional(LSTM(int(layer),input_shape=(None,feat_size),dropout=0.1,return_sequences=True,recurrent_dropout=0.1)))
                else:
                    print(layer,l,feat_size)
                    model.add(LSTM(int(layer),input_shape=(None,feat_size),dropout=0.1, recurrent_dropout=0.1, return_sequences=True))
            else:
                model.add(TimeDistributed(Dense(int(layer),activation='relu')))
                model.add(Dropout(0.1))

            #model.add(TimeDistributed(Dense(n_classes,activation='softmax')))
            model.add(TimeDistributed(Dense(n_classes-1, activation='softmax')))

    adagrad = Adagrad()
    model.compile(optimizer=adagrad,loss='categorical_crossentropy',metrics=['accuracy'])

    return model

parser = argparse.ArgumentParser(description='tests models trained for slu')
parser.add_argument('--datadir','-d',type=str,help='Home dir of the data')
parser.add_argument('--modeldir','-md',type=str,help='Folder with the different slu models')

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

args = parser.parse_args()

model_name_pattern = re.compile('batch(\d+)_(\D+)(\d+)_epochs(\d+).hdf5')

feature_files_list = [os.path.join(args.datadir,'test',feature_file) for feature_file in os.listdir(os.path.join(args.datadir,'test')) if feature_file.endswith('hdf5')]

max_utt_len,feature_size = get_feature_size_from_data(feature_files_list[0])
n_classes = get_nclases(feature_files_list,max_utt_len)

for file_name in os.listdir(args.modeldir):
    if re.match(model_name_pattern,file_name):
        batch_size, model_config, n_layers, n_epochs = re.match(model_name_pattern,file_name).groups()
        if model_config.find('LA') > -1:
            model = load_model(3*feature_size)
        else:
            model = load_model(feature_size)
        model.load_weights(os.path.join(args.modeldir,file_name))
        print(model.summary())
        logging.info('Loaded {} for testing'.format(os.path.join(args.modeldir,file_name)))
        if model_config.find('LA') > -1:
            x_test, y_test = load_data(os.path.join(args.datadir, 'test'),max_utt_len,feature_size,n_classes,'la')
        else:
            x_test, y_test = load_data(os.path.join(args.datadir, 'test'),max_utt_len,feature_size, n_classes)
        y_pred = model.predict(x_test)

        compute_scores()





