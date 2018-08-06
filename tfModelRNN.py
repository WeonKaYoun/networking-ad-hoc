import numpy as np
import librosa
import tensorflow as tf
import glob

from myAudio import Audio


CHUNK_SIZE = 8192
SR = 44100

batch_size = 2048
num_classes = 20            #분류할 사전의 크기 

learning_rate = 0.01
sequence_length = 16         

output_dim = 3
layers = 3 

def mfcc(raw, chunk_size=8192, sr=44100, n_mfcc=num_classes):
    mfcc = np.empty((num_classes, 0))
    for i in range(0, len(raw), chunk_size):
        mfcc_slice = librosa.feature.mfcc(raw[i:i+chunk_size], sr=sr, n_mfcc=n_mfcc)
        mfcc = np.hstack((mfcc, mfcc_slice))
    return mfcc
def makeHot(dataX, sequence_length):
    X_hot_list= []
    #Y_hot_tmp = dataY[sequence_length-1:]

    for i in range(0, dataX.shape[0] - sequence_length+1):
        _x = dataX[i:i + sequence_length]
        #if i<10:
            #print(_x, "->", Y_hot_tmp[i])
        X_hot_list.append(_x)

    X_hot = np.array(X_hot_list[:])
    #Y_hot= Y_hot_tmp.reshape((len(Y_hot_tmp),n_unique_labels))
    return X_hot[:]#, Y_hot[:]
def extractFeature(raw):
    dataX = mfcc(raw).T
    X_hot = makeHot(dataX,sequence_length = sequence_length)
    return X_hot[:]

###########################################   Model   #########################################
X = tf.placeholder(tf.float32, [None, sequence_length,num_classes], name="X")
Y = tf.placeholder(tf.float32, [None, output_dim], name="Y")

keep_prob = tf.placeholder(tf.float32)

cell = tf.contrib.rnn.BasicLSTMCell(num_units=num_classes, state_is_tuple=True)
#cell = tf.contrib.rnn.DropoutWrapper(cell, output_keep_prob=keep_prob)
cell = tf.contrib.rnn.MultiRNNCell([cell]*2, state_is_tuple= True)

BatchSize = tf.placeholder(tf.int32, [], name='BatchSize')
initial_state = cell.zero_state(BatchSize, tf.float32)
outputs, _states = tf.nn.dynamic_rnn(cell, X,initial_state=initial_state,dtype=tf.float32)

dense1 = tf.layers.dense(inputs=outputs[:,-1], units=sequence_length*output_dim, activation=tf.nn.relu)

dense2 = tf.layers.dense(inputs=dense1, units=sequence_length*output_dim, activation=tf.nn.relu)
dropout2 = tf.nn.dropout(dense1, keep_prob=keep_prob)

dense3 = tf.layers.dense(inputs=dense2, units=output_dim, activation=tf.nn.relu)

Y_pred= tf.layers.dense(inputs=dense3, units=output_dim)
cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=Y_pred, labels=Y))
lr = tf.placeholder(tf.float32,shape=(), name='learning_rate')
train = tf.train.AdamOptimizer(lr).minimize(cost)

##################################################################################################
sess = tf.Session()
saver = tf.train.Saver()

saver.restore(sess, './RNN/my_RNN_model_test')

def getDetectionResult(sound):
    #raw = Audio.getStream(sample_rate = 44100, chunk_size = 8192,chunk_num = 3, isWrite=True)
    dataX = extractFeature(sound)
    y_pred = sess.run(tf.argmax(Y_pred,1), feed_dict={X:dataX, BatchSize: len(dataX), keep_prob:1.0 })
    return y_pred
