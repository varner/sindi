from flask import Flask, request, redirect
import twilio.twiml
import keras.models
from keras.models import Sequential
from keras.layers import Dense, Activation
from keras.layers import LSTM
from keras.optimizers import RMSprop
from keras.utils.data_utils import get_file
import numpy as np
import unicodedata
import random
import sys
import re
import os

# preload chars
chars = ['\t', '\n', ' ', '!', '"', '#', '$', '&', "'", '(', ')', '*', ',', '-', 
'.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '>', '?', 
'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 
'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '\x80', '\x93', '\x94', '\x97', 
'\x98', '\x99', '\x9c', '\x9d', '\x9f', '\xa2', '\xa6', '\xa7', '\xa8', '\xa9', 
'\xae', '\xaf', '\xb3', '\xc3', '\xe2']
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))

maxlen = 40
model = keras.models.load_model("model_20.h5")

def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)

app = Flask(__name__)

@app.route('/')
def hello():
    return "i hope this works"

@app.route('/sms', methods=['POST'])
def sms():
    message_body = request.form['Body']
 
    resp = twilio.twiml.Response()
    resp.message(generateResponse(unicodedata.normalize('NFKD', message_body).encode('ascii','ignore').lower()))
    return str(resp)

def generateResponse(initial_phrase):    
    # phrase and phrase preperation
    if len(initial_phrase) < 39   : initial_phrase = "%s%s " % (" " * (40 - len(initial_phrase) - 1), initial_phrase)
    elif len(initial_phrase) > 39 : initial_phrase = "%s " % (initial_phrase[-39:])
    
    # diversity picking
    diversities = [0.2, 0.3, 0.5]
    diversity   = diversities[random.randint(0, len(diversities) - 1)]
    
    # preparing generated and setence stuff
    generated = ''
    sentence = initial_phrase
    print sentence
    
    for i in range(80):
        x = np.zeros((1, maxlen, len(chars)))
        for t, char in enumerate(sentence):
            x[0, t, char_indices[char]] = 1.
        preds = model.predict(x, verbose=0)[0]
        next_index = sample(preds, diversity)
        next_char = indices_char[next_index]
        generated += next_char
        sentence = sentence[1:] + next_char
    
    #find shortest phrase based on "reliable" breakpoints (nothing can possibly go wrong!!!)
    comma  = and_ = period = generated
    commas = generated.find(",")
    if commas is not -1: comma = generated[:commas]
    ands = generated.find(' and ')
    if ands is not -1: and_ = generated[:ands]
    periods = generated.find('.')
    if periods is not -1: period = generated[:periods]
    
    #take the minimum of that
    return min([comma, and_, period, generated], key=len)

if __name__ == '__main__':
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
