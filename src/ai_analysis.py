import numpy as np
import librosa
import json
from pathlib import Path, PosixPath
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torch.nn.functional as F
from sound_processing import audio_to_spec

MAIN_DIR = Path('/home/monoton/PycharmProjects/ml-audio-cavity-check')
INPUT_DIR = MAIN_DIR / 'data'
EXPORT_DIR = MAIN_DIR / 'export'
PARAMS_PATH = MAIN_DIR / 'model/model_params.json'
MODEL_DIR = MAIN_DIR / 'model/best_model.pth'
SR = 22050
N_FFT = 2048
HOP_LENGTH = 200
N_MELS = 64
FMIN = 3000
FMAX = 3400
N_TIME = 64
DURATION = 1
TARGET_SAMPLES = int(SR * DURATION)

with open(PARAMS_PATH, 'r') as f:
    params = json.load(f)

MEAN = params['mean']
STD = params['std']


class SimpleCNN(nn.Module):
    def __init__(self, input_height=32, num_classes=2):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 8, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(8, 16, kernel_size=3, padding=1)
        self.adaptive_pool = nn.AdaptiveAvgPool2d((4, 4))
        self.fc1 = nn.Linear(16 * 4 * 4, 32)
        self.fc2 = nn.Linear(32, num_classes)

    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = self.adaptive_pool(x)
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x


model = SimpleCNN(input_height=N_MELS, num_classes=2)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
state_dict = torch.load(MODEL_DIR, map_location=device)
model.load_state_dict(state_dict)
model.to(device)
model.eval()

def predict_audio(file_path, normalize=True, mean=None, std=None):
    spec_db = audio_to_spec(Path(file_path))
    spec_tensor = torch.from_numpy(spec_db).float().unsqueeze(0).unsqueeze(0)

    if normalize:
        if mean is not None and std is not None:
            spec_tensor = (spec_tensor - mean) / std
        else:
            print("Внимание: нормализация включена, но mean/std не заданы. Пропускаем.")

    spec_tensor = spec_tensor.to(device)
    with torch.no_grad():
        logits = model(spec_tensor)
        probs = F.softmax(logits, dim=1)

    pred_idx = torch.argmax(probs, dim=1).item()
    confidence = probs[0, pred_idx].item()

    class_names = ['full', 'cavity']
    predicted_class = class_names[pred_idx]

    return predicted_class, confidence, probs.cpu().numpy().flatten()


if __name__ == '__main__':
    test_file = ''
    cls, conf, all_probs = predict_audio(
        test_file,
        normalize=True,
        mean=MEAN,
        std=STD,
    )

    print(f'Класс: {cls}\nУверенность: {conf:.4f}\nВероятности: full={all_probs[0]:.4f}, cavity={all_probs[1]:.4f}')
