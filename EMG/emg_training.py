import numpy as np
import pandas as pd
from sklearn import svm
from sklearn.metrics import accuracy_score
import math
import pickle
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# MUST ADJUST OFFSET!!! http://www.sfu.ca/~dmackey/Chap%203-4%20EMG.pdf

# features from https://link.springer.com/article/10.1007/s11517-019-02073-z

def detrend(signal):
    detrended = []
    signal = np.array(signal)
    for k in range(7, len(signal)):
        detrended.append((signal[k] - (sum(signal[k-7:k])/8)))
    return detrended


data = pd.read_csv("../EMG_Training_E.csv")
data2 = pd.read_csv("../EMG_Training_H.csv")
data3 = pd.read_csv("../EMG_Training_S.csv")

training_data_pure1 = np.array(data["input"][0:99])
training_data_overlapped1 = np.array(data["input"][99:])

training_labels_pure1 = np.array(data["label"][0:99])
training_labels_overlapped1 = np.array(data["label"][99:])

training_data_pure2 = np.array(data2["input"][0:99])
training_data_overlapped2 = np.array(data2["input"][99:])

training_labels_pure2 = np.array(data2["label"][0:99])
training_labels_overlapped2 = np.array(data2["label"][99:])

training_data_pure3 = np.array(data3["input"][0:49])
training_data_overlapped3 = np.array(data3["input"][49:])

training_labels_pure3 = np.array(data3["label"][0:49])
training_labels_overlapped3 = np.array(data3["label"][49:])

training_data_pure = np.concatenate((training_data_pure1, training_data_pure2, training_data_pure3))
training_data_overlapped = np.concatenate((training_data_overlapped1, training_data_overlapped2, training_data_overlapped3))

training_labels_pure = np.concatenate((training_labels_pure1, training_labels_pure2, training_labels_pure3))
training_labels_overlapped = np.concatenate((training_labels_overlapped1, training_labels_overlapped2, training_labels_overlapped3))

training_labels = np.concatenate((training_labels_pure, training_labels_overlapped))

# remove first 200 samples because of gesture delay
processed_training_data_pure = []
processed_training_data_overlapped = []

for val in training_data_pure:
    # process string and read it as integers
    val = val[1:len(val)-1]
    processed_training_data_pure.append(np.array([float(x.strip()) for x in val.split(",")[200:]]))

for val in training_data_overlapped:
    # process string and read it as integers
    val = val[1:len(val) - 1]
    processed_training_data_overlapped.append(np.array([float(x.strip()) for x in val.split(",")[200:]]))

processed_training_data = []
processed_training_data.extend(processed_training_data_pure)
processed_training_data.extend(processed_training_data_overlapped)

# detrend and recenter around 0
training_data_recentered = []

for arr in processed_training_data:
    offset = np.median(arr)
    recentered = [(x - offset) for x in arr]
    detrended = detrend(recentered)
    training_data_recentered.append(detrended)

# apply highpass filter to avoid aliasing effects
filtered_data = []

for arr in training_data_recentered:
    fft = np.fft.rfft(arr)
    sr = (len(arr) + 200)/3
    freqs = np.fft.rfftfreq(len(fft), 1/sr)
    index = np.searchsorted(freqs, sr/2)

    lowpass = fft[:]
    lowpass[index:] = 0
    filtered_data.append(np.fft.irfft(lowpass))


rectified_training = []

for rest in filtered_data:
    rectified_training.append(np.abs(rest))


# since we have a low sample rate, take these for the entire window
iav_training = []

for rest in rectified_training:
    iav_training.append(np.sum(rest))

mav_training = []

for rest in rectified_training:
    mav_training.append(np.sum(rest)/len(rest))


rms_training = []

for rest in rectified_training:
    rms_training.append(math.sqrt(np.sum(rest ** 2)/len(rest)))


std_training = []

for rest in filtered_data:
    std_training.append(np.std(rest))

var_training = []

for rest in filtered_data:
    var_training.append(np.var(rest))

wl_training = []

for rest in filtered_data:
    count = 0
    for i in range(1, len(rest)):
        count = count + abs(rest[i] - rest[i-1])
    wl_training.append(count)


all_features_training = np.array([iav_training, mav_training, rms_training, std_training, var_training, wl_training])
all_features_training = np.transpose(all_features_training)


# training_labels1 = np.array(data["label"])
# training_labels2 = np.array(data2["label"])
# training_labels3 = np.array(data3["label"])
#
# training_labels = np.concatenate((training_labels1, training_labels2, training_labels3))


####### TRAINING ########

X_training = all_features_training
y_training = training_labels

scaler = StandardScaler()
scaler.fit(X_training)
X_training = scaler.transform(X_training)

clf = svm.SVC(C=100, kernel="rbf")
clf.fit(X_training, y_training)


######## Validation on exact windows #########

testing_data = pd.read_csv("../EMG_training_E_Day2.csv")
testing_array_strings = np.array(testing_data["input"])

testing_array = []
for val in testing_array_strings:
    val = val[1:len(val) - 1]
    testing_array.append(np.array([float(x.strip()) for x in val.split(",")[200:]]))

recentered_testing = []
for arr in testing_array:
    offset = np.median(arr)
    recentered = [(x - offset) for x in arr]
    result = detrend(recentered)
    recentered_testing.append(result)

final_testing_data = []
for arr in recentered_testing:
    fft = np.fft.rfft(arr)
    sr = (len(arr) + 200)/3
    freqs = np.fft.rfftfreq(len(fft), 1/sr)
    index = np.searchsorted(freqs, sr/2)

    lowpass = fft[:]
    lowpass[index:] = 0
    final_testing_data.append(np.fft.irfft(lowpass))

rectified_testing = []
for val in final_testing_data:
    rectified_testing.append(np.abs(val))


iav_testing = []
mav_testing = []
rms_testing = []
for val in rectified_testing:
    iav_testing.append(np.sum(val))
    mav_testing.append(np.sum(val)/len(val))
    rms_testing.append(math.sqrt(np.sum(val ** 2) / len(val)))

std_testing = []
var_testing = []
wl_testing = []
for val in final_testing_data:
    std_testing.append(np.std(val))
    var_testing.append(np.var(val))
    count = 0
    for i in range(1, len(val)):
        count = count + abs(val[i] - val[i - 1])
    wl_testing.append(count)

all_features_testing = np.array([iav_testing, mav_testing, rms_testing, std_testing, var_testing, wl_testing])
all_features_testing = np.transpose(all_features_testing)

all_features_testing = scaler.transform(all_features_testing)


testing_labels = np.array(testing_data["label"])


result = clf.predict(all_features_testing)
print("exact gesture accuracy: ", accuracy_score(testing_labels, result))


###### Validation on 1s gesture overlap windows ######

testing_array = []
for val in testing_array_strings:
    val = val[1:len(val) - 1]
    testing_array.append(np.array([float(x.strip()) for x in val.split(",")[200:400]]))
    testing_array.append(np.array([float(x.strip()) for x in val.split(",")[400:]]))

recentered_testing = []
for arr in testing_array:
    offset = np.median(arr)
    recentered = [(x - offset) for x in arr]
    result = detrend(recentered)
    recentered_testing.append(result)

final_testing_data = []
for arr in recentered_testing:
    fft = np.fft.rfft(arr)
    sr = (len(arr))
    freqs = np.fft.rfftfreq(len(fft), 1/sr)
    index = np.searchsorted(freqs, sr/2)

    lowpass = fft[:]
    lowpass[index:] = 0
    final_testing_data.append(np.fft.irfft(lowpass))

rectified_testing = []
for val in final_testing_data:
    rectified_testing.append(np.abs(val))


iav_testing = []
mav_testing = []
rms_testing = []
for val in rectified_testing:
    iav_testing.append(np.sum(val))
    mav_testing.append(np.sum(val)/len(val))
    rms_testing.append(math.sqrt(np.sum(val ** 2) / len(val)))

std_testing = []
var_testing = []
wl_testing = []
for val in final_testing_data:
    std_testing.append(np.std(val))
    var_testing.append(np.var(val))
    count = 0
    for i in range(1, len(val)):
        count = count + abs(val[i] - val[i - 1])
    wl_testing.append(count)

all_features_testing = np.array([iav_testing, mav_testing, rms_testing, std_testing, var_testing, wl_testing])
all_features_testing = np.transpose(all_features_testing)

all_features_testing = scaler.transform(all_features_testing)


testing_labels = []

for label in np.array(testing_data["label"]):
    testing_labels.append(label)
    testing_labels.append(label)

testing_labels = np.array(testing_labels)


result = clf.predict(all_features_testing)
print("1s windows gesture accuracy: ", accuracy_score(testing_labels, result))


###### Validation on overlap windows ######
testing_array = []
for val in testing_array_strings:
    val = val[1:len(val) - 1]
    testing_array.append(np.array([float(x.strip()) for x in val.split(",")]))

recentered_testing = []
for arr in testing_array:
    offset = np.median(arr)
    recentered = [(x - offset) for x in arr]
    result = detrend(recentered)
    recentered_testing.append(result)

final_testing_data = []
for arr in recentered_testing:
    fft = np.fft.rfft(arr)
    sr = (len(arr) + 200)/3
    freqs = np.fft.rfftfreq(len(fft), 1/sr)
    index = np.searchsorted(freqs, sr/2)

    lowpass = fft[:]
    lowpass[index:] = 0
    final_testing_data.append(np.fft.irfft(lowpass))

rectified_testing = []
for val in final_testing_data:
    rectified_testing.append(np.abs(val))


iav_testing = []
mav_testing = []
rms_testing = []
for val in rectified_testing:
    iav_testing.append(np.sum(val))
    mav_testing.append(np.sum(val)/len(val))
    rms_testing.append(math.sqrt(np.sum(val ** 2) / len(val)))

std_testing = []
var_testing = []
wl_testing = []
for val in final_testing_data:
    std_testing.append(np.std(val))
    var_testing.append(np.var(val))
    count = 0
    for i in range(1, len(val)):
        count = count + abs(val[i] - val[i - 1])
    wl_testing.append(count)

all_features_testing = np.array([iav_testing, mav_testing, rms_testing, std_testing, var_testing, wl_testing])
all_features_testing = np.transpose(all_features_testing)

all_features_testing = scaler.transform(all_features_testing)

testing_labels = np.array(testing_data["label"])


result = clf.predict(all_features_testing)
print("inexact gesture accuracy: ", accuracy_score(testing_labels, result))


# # Save Model to File
# filename = 'finalized_model.sav'
# pickle.dump(clf, open(filename, 'wb'))

# filename2 = 'model_scaler.sav'
# pickle.dump(scaler, open(filename2, 'wb'))


