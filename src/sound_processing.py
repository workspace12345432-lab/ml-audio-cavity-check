import numpy as np
import librosa
from pathlib import Path, PosixPath
import matplotlib.pyplot as plt

MAIN_DIR = Path('/home/monoton/PycharmProjects/ml-audio-cavity-check')
INPUT_DIR = MAIN_DIR / 'data'
EXPORT_DIR = MAIN_DIR / 'export'
SR = 22050
N_FFT = 2048
HOP_LENGTH = 200
N_MELS = 64
FMIN = 3000
FMAX = 3400
N_TIME = 64
DURATION = 1
TARGET_SAMPLES = int(SR * DURATION)


def audio_to_spec(input_path: PosixPath):
    y, sr = librosa.load(input_path, sr=SR)
    y_fixed = y

    mel_spec = librosa.feature.melspectrogram(
        y=y_fixed,
        sr=SR,
        n_fft=N_FFT,
        hop_length=HOP_LENGTH,
        n_mels=N_MELS,
        fmin=FMIN,
        fmax=FMAX,
    )

    energy_per_frame = np.sum(mel_spec, axis=0)
    peak_idx = np.argmax(energy_per_frame)
    target_center = N_TIME // 2
    centered_mel = np.zeros((N_MELS, N_TIME))
    shift = target_center - peak_idx - 20

    for i in range(mel_spec.shape[1]):
        j = i + shift
        if 0 <= j < N_TIME:
            centered_mel[:, j] = mel_spec[:, i]

    mel_spec_db = librosa.power_to_db(centered_mel, ref=np.max)
    return mel_spec_db


# Перевод спектрограммы в .npy
def spec_to_npy(spec: np.ndarray, export_path: PosixPath):
    np.save(export_path, spec)
    return 0


# Вывод спектрограммы
def show_spec(spec: np.ndarray, name='Спектрограмма'):
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(
        data=spec,
        sr=SR,
        x_axis='time',
        y_axis='mel',
    )
    plt.colorbar()
    plt.tight_layout()
    plt.title(name)
    plt.show()
    return 0


if __name__ == '__main__':
    # Вывести все спектрограммы
    for i in INPUT_DIR.iterdir():
        spec = audio_to_spec(i)
        show_spec(spec, i.name[:-4])

    # Перевести все спектрограммы в .npy
    for i in INPUT_DIR.iterdir():
        spec = audio_to_spec(i)
        spec_to_npy(spec, export_path=EXPORT_DIR / i.name.replace('mp3', 'npy'))
        print(f'{i.name[:-4]} completed')
