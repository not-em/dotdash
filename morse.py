"""
morse.py — ITU Morse code encoder/decoder + MP3 generation
"""

import numpy as np
import io
import subprocess
import tempfile
import os

# ITU Morse code table
MORSE_CODE = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
    ".": ".-.-.-",
    ",": "--..--",
    "?": "..--..",
    "'": ".----.",
    "!": "-.-.--",
    "/": "-..-.",
    "(": "-.--.",
    ")": "-.--.-",
    "&": ".-...",
    ":": "---...",
    ";": "-.-.-.",
    "=": "-...-",
    "+": ".-.-.",
    "-": "-....-",
    "_": "..--.-",
    '"': ".-..-.",
    "$": "...-..-",
    "@": ".--.-.",
}

REVERSE_MORSE = {v: k for k, v in MORSE_CODE.items()}

# Display characters
DOT_CHAR = "·"
DASH_CHAR = "—"


def encode(text: str) -> str:
    """Encode text to morse code string (dots and dashes)."""
    text = text.upper().strip()
    words = text.split(" ")
    morse_words = []
    for word in words:
        morse_chars = []
        for ch in word:
            if ch in MORSE_CODE:
                code = MORSE_CODE[ch].replace(".", DOT_CHAR).replace("-", DASH_CHAR)
                morse_chars.append(code)
            else:
                morse_chars.append("?")
        morse_words.append("  ".join(morse_chars))  # 2 spaces between letters
    return "    /    ".join(morse_words)  # slash between words


def encode_raw(text: str) -> str:
    """Encode text to raw morse (dots and dashes only, for audio generation)."""
    text = text.upper().strip()
    words = text.split(" ")
    morse_words = []
    for word in words:
        morse_chars = []
        for ch in word:
            if ch in MORSE_CODE:
                morse_chars.append(MORSE_CODE[ch])
        morse_words.append(" ".join(morse_chars))
    return "   ".join(morse_words)  # 3 spaces = word gap


def decode(morse: str) -> str:
    """Decode morse code string to text."""
    # Normalise display chars back to dots/dashes
    morse = morse.replace(DOT_CHAR, ".").replace(DASH_CHAR, "-")
    # Split on word separators
    words = morse.split("/")
    result = []
    for word in words:
        letters = word.strip().split()
        decoded_word = ""
        for code in letters:
            code = code.strip()
            if code in REVERSE_MORSE:
                decoded_word += REVERSE_MORSE[code]
            elif code:
                decoded_word += "?"
        result.append(decoded_word)
    return " ".join(result)


def generate_audio(text: str, wpm: int = 20) -> bytes:
    """
    Generate MP3 audio of morse code for given text.
    Returns MP3 bytes.
    """
    sample_rate = 44100
    frequency = 700  # Hz — classic morse tone

    # Paris standard timing
    dot_duration = 1.2 / wpm  # seconds
    dash_duration = 3 * dot_duration
    symbol_gap = dot_duration  # gap between symbols in a letter
    letter_gap = 3 * dot_duration
    word_gap = 7 * dot_duration

    def tone(duration: float) -> np.ndarray:
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        wave = np.sin(2 * np.pi * frequency * t)
        # Apply a tiny fade in/out to avoid clicks
        fade = int(sample_rate * 0.005)
        wave[:fade] *= np.linspace(0, 1, fade)
        wave[-fade:] *= np.linspace(1, 0, fade)
        return (wave * 32767).astype(np.int16)

    def silence(duration: float) -> np.ndarray:
        return np.zeros(int(sample_rate * duration), dtype=np.int16)

    morse_raw = encode_raw(text)
    samples = []

    i = 0
    while i < len(morse_raw):
        ch = morse_raw[i]
        if ch == ".":
            samples.append(tone(dot_duration))
            samples.append(silence(symbol_gap))
        elif ch == "-":
            samples.append(tone(dash_duration))
            samples.append(silence(symbol_gap))
        elif ch == " ":
            # Count consecutive spaces
            j = i
            while j < len(morse_raw) and morse_raw[j] == " ":
                j += 1
            spaces = j - i
            if spaces >= 3:
                samples.append(silence(word_gap - symbol_gap))
            else:
                samples.append(silence(letter_gap - symbol_gap))
            i = j
            continue
        i += 1

    if not samples:
        samples = [silence(0.5)]

    audio = np.concatenate(samples)

    # Write raw PCM to a temp WAV, convert to MP3 via ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_f:
        wav_path = wav_f.name
        # Write a minimal WAV header + PCM data
        import wave

        with wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio.tobytes())

    mp3_path = wav_path.replace(".wav", ".mp3")
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                wav_path,
                "-codec:a",
                "libmp3lame",
                "-q:a",
                "4",
                mp3_path,
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        with open(mp3_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(wav_path)
        if os.path.exists(mp3_path):
            os.unlink(mp3_path)
