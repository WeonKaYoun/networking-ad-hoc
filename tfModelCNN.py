import numpy as np
import librosa
import tensorflow as tf
import glob
from myAudio import Audio

n_mfcc = 16
n_frame = 16
n_classes = 3
n_channels = 1
learning_rate = 0.0002

#### MFCC4 Model ###
def mfcc4(raw, chunk_size=8192, window_size=4096, sr=44100, n_mfcc=16, n_frame=16):
    mfcc = np.empty((0, n_mfcc, n_frame))
    y = []
    for i in range(0, len(raw), chunk_size//2):
        mfcc_slice = librosa.feature.mfcc(raw[i:i+chunk_size], sr=sr, n_mfcc=n_mfcc) #n_mfcc,17
        if mfcc_slice.shape[1] < 17:
            print("small end:", mfcc_slice.shape)
            continue
        mfcc_slice = mfcc_slice[:,:-1]
        mfcc_slice = mfcc_slice.reshape((1, mfcc_slice.shape[0], mfcc_slice.shape[1]))
        mfcc = np.vstack((mfcc, mfcc_slice))
    y = np.array(y)
    return mfcc

def extraction(raw):
    soundData = mfcc4(raw)
    dataX = np.reshape(soundData, (soundData.shape[0],soundData.shape[1],soundData.shape[2], 1))
    print("X: ", dataX.shape)
    print("Extract feature is finished")
    return dataX

###########################################   CNN Model   #########################################
X = tf.placeholder(tf.float32, shape=[None,n_mfcc*n_frame*n_channels])
X = tf.reshape(X, [-1, n_mfcc, n_frame, n_channels])
Y = tf.placeholder(tf.float32, shape=[None,n_classes])

# Layer 1
conv1 = tf.layers.conv2d(inputs=X, filters=1, kernel_size=[3, 3],
                         padding="SAME", activation=tf.nn.relu)
pool1 = tf.layers.max_pooling2d(inputs=conv1, pool_size=[2, 2],
                                padding="SAME", strides=1)
# Layer 2
conv2 = tf.layers.conv2d(inputs=pool1, filters=1, kernel_size=[3, 3],
                         padding="SAME", activation=tf.nn.relu)
pool2 = tf.layers.max_pooling2d(inputs=conv2, pool_size=[2, 2],
                                padding="SAME", strides=1)

flat = tf.reshape(pool2, [-1, 16*16*1])
dense2 = tf.layers.dense(inputs=flat, units=625, activation=tf.nn.relu)
logits = tf.layers.dense(inputs=dense2, units=3)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits, labels=Y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
###################################################################################################

### Model loading part ###
sess = tf.Session()
saver = tf.train.Saver()
saver.restore(sess, './CNN/cnnmodel')

def getDetectionResult(sound):
    #raw = Audio.getStream(sample_rate = 44100, chunk_size = 8192, chunk_num = 1, isWrite=True)
    dataX = extraction(sound)
    y_pred = sess.run(tf.argmax(logits,1),feed_dict={X: dataX, keep_prob: 1})
    counts = np.bincount(y_pred)
    result = np.argmax(counts)

    if result == 0:
        rs = 0
        print(' 드론-Unload-', result)
    elif result == 1:
        rs = 1
        print(' 드론-Load-', result)
    else:
        rs = 0
        print(' None-', result)
    return rs
