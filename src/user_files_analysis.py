import json
from pathlib import Path
from ai_analysis import predict_audio
import os

PARAMS_PATH = Path('model/model_params.json')
USER_DATA_PATH = Path('saved_audio')

with open(PARAMS_PATH, 'r') as f:
    params = json.load(f)

MEAN = params['mean']
STD = params['std']

def analyse_user_data():
    cavity_probs = []
    full_probs = []
    for file in USER_DATA_PATH.iterdir():
        cls, conf, _ = predict_audio(
            file,
            normalize=True,
            mean=MEAN,
            std=STD,
        )

        if cls == 'cavity':
            cavity_probs.append(conf)
        else:
            full_probs.append(conf)

    for file in USER_DATA_PATH.iterdir():
        os.remove(file)

    if len(cavity_probs) == len(full_probs):
        if sum(cavity_probs) > sum(full_probs):
            return -1
        elif sum(cavity_probs) < sum(full_probs):
            return 1
        else:
            return 0
    else:
        if len(cavity_probs) > len(full_probs):
            return -1
        else:
            return 1


if __name__ == '__main__':
    print(analyse_user_data())
