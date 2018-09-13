import argparse

import os,logging

import h5py
import pandas as pd
import numpy as np
import sys

from keras.callbacks import ModelCheckpoint
from keras.utils import np_utils

from sptd_utils import *

def train_model():

    checkpoint = ModelCheckpoint(os.path.join(args.datadir,'{}.hdf5'.format(model_config)),monitor='val_acc',verbose=0,save_best_only=True,save_weights_only=False,period=1)

    if args.model_type.find('LA') > -1:
        x_train, y_train = load_data(os.path.join(args.datadir, 'train'),max_utt_len,feature_size,n_classes,'la')
        x_val, y_val = load_data(os.path.join(args.datadir, 'val'),max_utt_len,feature_size,n_classes,'la')
    else:
        x_train, y_train = load_data(os.path.join(args.datadir,'train'),max_utt_len,feature_size,n_classes)
        x_val, y_val = load_data(os.path.join(args.datadir,'val'),max_utt_len,feature_size,n_classes)

    if args.model_type.find('LA') > -1:
        if args.model_type.startswith('b'):
            model = configure_model(3*feature_size,n_classes,args.layers,'b')
        else:
            model = configure_model(3*feature_size,n_classes,args.layers)

    else:
        if args.model_type.startswith('b'):
            model = configure_model(feature_size,n_classes,args.layers,'b')
        else:
            model = configure_model(feature_size,n_classes,args.layers)

    model.fit(x_train, y_train, epochs=args.epochs, batch_size=args.batch_size, validation_data=(x_val, y_val),callbacks=[checkpoint])


parser = argparse.ArgumentParser(description='Script which trains an slu model to detect word tags and topic')
parser.add_argument('--datadir','-d',type=str,help='Folder where the data is stored',required=True)
parser.add_argument('--batch_size','-b',type=int,help='Size of the batch used in training',default=10)
parser.add_argument('--model_type','-m',type=str,help='Configuration of the model used',default='LSTM')
parser.add_argument('--epochs','-e',type=int,help='Number of epochs using in training',default=100)
parser.add_argument('--layers','-l',type=int,nargs='+',help='Layers used in the model',default=[100])

args = parser.parse_args()

model_config = 'batch{}_{}{}_epochs{}'.format(str(args.batch_size),args.model_type,'_'.join(str(l) for l in args.layers),args.epochs)

val_files_list = [os.path.join(args.datadir,'val',feature_file) for feature_file in os.listdir(os.path.join(args.datadir,'val')) if feature_file.endswith('hdf5')]
train_files_list = [os.path.join(args.datadir,'train',feature_file) for feature_file in os.listdir(os.path.join(args.datadir,'train')) if feature_file.endswith('hdf5')]
test_files_list = [os.path.join(args.datadir,'test',feature_file) for feature_file in os.listdir(os.path.join(args.datadir,'test')) if feature_file.endswith('hdf5')]

max_utt_len,feature_size = get_feature_size_from_data(val_files_list[0])

all_files_list = val_files_list + train_files_list + test_files_list
n_classes = get_nclases(all_files_list,max_utt_len)

train_model()
