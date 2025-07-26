# voice_verification.py

import numpy as np
import hashlib
import librosa

def extract_voice_features(audio_path):
    y, sr = librosa.load(audio_path, sr=None)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mean_mfcc = np.mean(mfcc, axis=1)
    hash_digest = hashlib.sha256(mean_mfcc.tobytes()).hexdigest()
    return hash_digest

def compare_voice_signatures(saved_signature, current_audio_path):
    current_signature = extract_voice_features(current_audio_path)
    return saved_signature == current_signature
