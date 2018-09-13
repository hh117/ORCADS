import argparse,os,logging
import pickle

import sys
from keras.callbacks import ModelCheckpoint
from numpy import random
sys.path.append('../utils')
from sptd_utils import *

def train_model():

    models_dir = os.path.join(args.datadir,'models','_'.join(feature_set))

    if not os.path.isdir(models_dir):
        os.makedirs(models_dir)

    print(os.path.join(models_dir,'{}.h5df'.format(model_config)))

    checkpoint = ModelCheckpoint(os.path.join(models_dir,'{}.h5df'.format(model_config)),monitor='val_acc',verbose=0,save_best_only=True,save_weights_only=False,period=1)

    x_train, y_train = load_data(os.path.join(args.datadir,'{}_trn'.format(args.task_number)),max_dial_len,feat_size,n_classes)
    x_val, y_val = load_data(os.path.join(args.datadir,'{}_dev'.format(args.task_number)),max_dial_len,feat_size,n_classes)

    model = configure_model(feat_size,n_classes,args.layer_sizes,optimizer='adadelta')

    model.fit(x_train,y_train,epochs=args.epochs,batch_size=x_train.shape[1],validation_data=(x_val,y_val),callbacks=[checkpoint])


parser = argparse.ArgumentParser(description='Trains LSTM for an Hybrid Code Network')
parser.add_argument('--datadir','-d',type=str,help='Folder where the data is stored',required=True)
parser.add_argument('--task_number','-tn',type=str,help='Task from the babi dataset that is going to be used',required=True)
parser.add_argument('--epochs','-e',type=int,help='Number of epochs used',default=12)
parser.add_argument('--layer_sizes','-l',type=int,nargs='+',help='Units per layer',default=[128])
parser.add_argument('--action_set','-as',type=str,help='File with the action set for the task',required=True)

random.seed(42)

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

args = parser.parse_args()

model_config = 'LSTM{}_epochs{}'.format('_'.join(str(l) for l in args.layer_sizes),args.epochs)

feature_set = args.datadir.split(os.sep)[-1].split('_')

subsets_file_lists = {}
for item in os.listdir(args.datadir):
    if item.startswith(args.task_number):
        task, subset = item.split('_')
        subsets_file_lists[subset] = [os.path.join(args.datadir,item,feature_file) for feature_file in os.listdir(os.path.join(args.datadir,item))]

max_dial_len = 0
for subs in subsets_file_lists:
    if len(subsets_file_lists[subs]) == 0:
        logging.warning('No feature file found for {} subset'.format(subs))
        continue
    max_dial_len, feat_size = get_feature_size_from_data(subsets_file_lists[subs][0])

if max_dial_len == 0:
    logging.error('No dialogue found')
    sys.exit()

with open(args.action_set,'rb') as lfp:
    available_actions = pickle.load(lfp)

n_classes = len(available_actions)
train_model()


