import json
import os
import os.path
import sys
import time

import numpy as np
from imagenet_utils import decode_predictions
from imagenet_utils import preprocess_input
from keras.preprocessing import image
from resnet50 import ResNet50


# read the tasking file into a list
def readTasking(fname):
    af = open(fname, 'r')
    data = list()
    for d in af:
        d = d.strip()
        data.append(json.loads(d))
    return data


# search tasking for interesting tags
def proc(taskFile, rootDir, atOnce=10000):
    good = list()
    bad = list()
    ugly = list()
    interesting = set()

    count = 0
    im = 0

    model = ResNet50(weights='imagenet')

    for x in ['car', 'pickup', 'suv', 'truck', 'crossover', 'van', 'minivan',
              'sports_car', 'cab', 'racer', 'convertible', 'jeep', 'ambulance']:

        interesting.add(x)

    data = readTasking(taskFile)

    startTime = time.time()
    for d in data:

        img_path = '{0}/{1}'.format(rootDir, d['filename'])

        flag = True

        try:
            img = image.load_img(img_path, target_size=(224, 224))

        except:
            # ugly this is not a decodable image
            ugly.append(d)
            flag = False

        if flag:

            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)
            preds = model.predict(x)
            predictions = decode_predictions(preds)[0][:4]

            found = False

            for prediction in predictions:
                i, t, score = prediction
                if t in interesting:
                    # image was interesting
                    good.append((d, t))
                    found = True
                    break
            if not found:
                # image was not interesting
                bad.append((d, predictions[0][1]))

        if count == atOnce:
            count = 0
            endTime = time.time() - startTime
            im = im + 1
            print('processed:', im * atOnce, 'Images', 'good',
                  len(good), 'bad', len(bad), 'file', len(file), endTime)
            startTime = time.time()
        count = count + 1

    return (good, bad, ugly)


# json encode each line of a list to a file
def writeList(l, fname):
    fn = open(fname, 'w')
    for item in l:
        fn.write(json.dumps(item) + '\n')
    fn.close()


def main():
    # argv[1] should be the tasking file to use
    # argv[2] should be the root prefix of the directory with the
    # images not ending in a /
    good, bad, ugly = proc(sys.argv[1], sys.argv[2])

    writeList(good, sys.argv[1] + '.good')
    writeList(bad, sys.argv[1] + '.bad')
    writeList(ugly, sys.argv[1] + '.ugly')

if __name__ == '__main__':
    os.environ['THEANO_FLAGS'] = 'mode=FAST_RUN,device=gpu,floatX=float32'
    main()
