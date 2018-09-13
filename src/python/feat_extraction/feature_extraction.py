import numpy as np
import logging

import sys


def get_utterance_embedding(emb,utterance,emb_size=0):

    if emb_size == 0:
        if type(emb) == type({}):
            emb_size = len(emb)
        elif type(emb) is np.ndarray:
            emb_size = emb.shape[1]
        else:
            logging.error('Type of embedding unknown')
            sys.exit()

    emb_matrix =  np.empty((len(utterance.split()),emb_size))

    for w,wrd in enumerate(utterance.split()):
        if wrd in emb:
            emb_matrix[w] = emb[wrd]
        elif wrd == 'let\'s':
            # exception for the case of let's
            emb_matrix[w] = (emb['let'] + emb['us']) / 2
        else:
            if 'OOV' in emb:
                emb_matrix[w] = emb['OOV']
            else:
                emb_matrix[w] = 2*np.random.random((emb.shape[1],))-1
            logging.info('{} not found in the glove model'.format(wrd))

    return np.mean(emb_matrix,axis=0)
