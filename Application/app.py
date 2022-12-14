from tkinter import *
from tkinter import ttk
from tkinter import filedialog
from PIL import Image, ImageTk
from scipy.io import loadmat
from keras.models import model_from_json
from math import factorial
import numpy as np
import os
import cv2
import time
import threading
import numpy.matlib
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use('TkAgg')

def load_model(json_path):
    global model
    model = model_from_json(open(json_path).read())
    return model


def load_weights(model, weight_path):
    dict2 = loadmat(weight_path)
    dict = conv_dict(dict2)
    i = 0
    for layer in model.layers:
        weights = dict[str(i)]
        layer.set_weights(weights)
        i += 1
    return model


def conv_dict(dict2): 
    dict = {}
    for i in range(len(dict2)):
        if str(i) in dict2:
            if dict2[str(i)].shape == (0, 0):
                dict[str(i)] = dict2[str(i)]
            else:
                weights = dict2[str(i)][0]
                weights2 = []
                for weight in weights:
                    if weight.shape in [(1, x) for x in range(0, 5000)]:
                        weights2.append(weight[0])
                    else:
                        weights2.append(weight)
                dict[str(i)] = weights2
    return dict


def savitzky_golay(y, window_size, order, deriv=0, rate=1):

    window_size = np.abs(np.int(window_size))
    order = np.abs(np.int(order))

    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")

    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")

    order_range = range(order + 1)

    half_window = (window_size - 1) // 2
    b = np.mat([[k ** i for i in order_range] for k in range(-half_window, half_window + 1)])
    m = np.linalg.pinv(b).A[deriv] * rate ** deriv * factorial(deriv)
    firstvals = y[0] - np.abs(y[1:half_window + 1][::-1] - y[0])
    lastvals = y[-1] + np.abs(y[-half_window - 1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve(m[::-1], y, mode='valid')


def load_dataset_One_Video_Features(Test_Video_Path):
    VideoPath = Test_Video_Path
    f = open(VideoPath, "r")
    words = f.read().split()
    num_feat = len(words) / 4096

    count = -1
    VideoFeatues = []
    for feat in range(0, int(num_feat)):
        feat_row1 = np.float32(words[feat * 4096:feat * 4096 + 4096])
        count = count + 1
        if count == 0:
            VideoFeatues = feat_row1
        if count > 0:
            VideoFeatues = np.vstack((VideoFeatues, feat_row1))
    AllFeatures = VideoFeatues

    return AllFeatures


def SingleBrowse(path):
    global data
    video_path = () + (path,)
    cap = cv2.VideoCapture(video_path[0])

    Total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    total_segments = np.linspace(1, Total_frames, num=33)
    total_segments = total_segments.round()
    FeaturePath = (video_path[0])
    print(video_path[0])
    FeaturePath = FeaturePath[0:-4]
    FeaturePath = FeaturePath + '.txt'
    inputs = load_dataset_One_Video_Features(FeaturePath)

    predictions = model.predict_on_batch(inputs)

    Frames_Score = []
    count = -1
    for iv in range(0, 32):
        F_Score = np.matlib.repmat(predictions[iv], 1, (int(total_segments[iv + 1]) - int(total_segments[iv])))
        count = count + 1
        if count == 0:
            Frames_Score = F_Score
        if count > 0:
            Frames_Score = np.hstack((Frames_Score, F_Score))

    cap = cv2.VideoCapture((video_path[0]))
    while not cap.isOpened():
        cap = cv2.VideoCapture((video_path))
        cv2.waitKey(1000)
        print("Wait for the header")

    pos_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
    Total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("Anomaly Prediction")
    x = np.linspace(1, Total_frames, Total_frames)
    scores = Frames_Score
    scores1 = scores.reshape((scores.shape[1],))
    scores1 = savitzky_golay(scores1, 101, 3)
    plt.close()
    break_pt = min(scores1.shape[0], x.shape[0])

    if (1 < len(ax.lines)):
        del ax.lines[1:]
    ax.axis([0, Total_frames, 0, 1])
    i = 0
    print("Graph Plot Started")

    while True:
        flag, frame = cap.read()
        if flag:
            i = i + 1
            jj = i % 10
            if jj == 1:

                cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
                img = Image.fromarray(cv2.resize(cv2image, (520, 390)))
                img2 = ImageTk.PhotoImage(image=img)
                label.configure(image=img2)
                label.image = img2
                
                data = ax.plot(x[:i], scores1[:i], color='r', linewidth=3)
                canvas.draw()
                canvas.get_tk_widget().pack()

            pos_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos_frame - 1)
            print("frame is not ready")
            cv2.waitKey(1000)

        if cv2.waitKey(10) == 27:
            break
        if cap.get(cv2.CAP_PROP_POS_FRAMES) == break_pt:
            break

    print("Graph Plot Ended")
    root.mainloop()

def btnHandler():
    path = filedialog.askopenfilename(title="Select a Video", filetypes=[("Video", "*.mp4")])
    SingleBrowse(path)


Model_dir = "model/"
weights_path = Model_dir + 'weights.mat'
model_path = Model_dir + "model.json"

model = load_model(model_path)
load_weights(model, weights_path)

root = Tk()
root.title("Criminal Anomaly Detection")
root.geometry("1360x720")

tabControl = ttk.Notebook(root)
tabControl.pack(fill="both", expand=1)


tab3 = Frame(tabControl)
tab3.configure(bg='white')
tab3.pack(fill="both", expand=1)

tabControl.add(tab3, text='    Upload Video   ')


uploadBtn = Button(tab3, text="Browse", padx=10, pady=5, command=btnHandler)
uploadBtn.pack(side=TOP, pady=20)

img = ImageTk.PhotoImage(Image.open("media/img/white_vid.jpg"))
label = Label(tab3, image=img, width=520, height=390, bg='white', borderwidth=2, relief="solid")
label.pack(side=LEFT, fill=BOTH, expand=True, padx=20, pady=20)

fig = plt.figure(figsize=(7, 7), dpi=80)
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
ax.axhline(y=0.6)
canvas = FigureCanvasTkAgg(fig, tab3)
canvas.get_tk_widget().pack(side=LEFT, expand=True, fill=BOTH, padx=20, pady=20)


def on_closing():
    root.destroy()
    os._exit(1)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()