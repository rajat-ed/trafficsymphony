# 🎹 Traffic Symphony

**Turn traffic, movement, and chaos into music.**

**Traffic Symphony** is a Python-based computer vision application that transforms video feeds into a playable piano interface. By scanning the bottom portion of a video (or live webcam), it detects motion across 12 distinct segments. When a car, pedestrian, or object moves through a segment, it triggers a mathematically generated piano note.

> **Designed by Rajat**

---

## ✨ Features

*   **Dual Input Modes:** Works with **Live Webcams** or **Pre-recorded Video Files** (MP4, AVI, MOV).
*   **Dynamic Segmentation:** Use the slider to split the screen into **4 to 12 notes** (simple detection vs. full octave).
*   **Procedural Audio:** No external MP3s required. All audio is synthesized mathematically in real-time using NumPy (Sine waves with exponential decay).
*   **Recording & Export:** Record your session and export a synchronized `.mp4` video with the generated audio track overlaid.
*   **Modern UI:** Built with `CustomTkinter` for a clean, dark-mode interface.
*   **Robust Failsafes:** Includes auto-save protection and forced video closing to prevent system freezes.

---

## 🛠️ System Requirements

Before running the application, ensure your system meets the following criteria:

*   **Operating System:** Windows 10/11 (Recommended), macOS, or Linux.
*   **Python:** Python 3.8 or higher.
*   **Hardware:**
    *   Webcam (for live mode).
    *   Standard Audio Output (Speakers/Headphones).

---

## 📦 Installation Guide

Follow these steps to get the project running on your PC.

### 1. Clone the Repository
Open your terminal or command prompt and run:
```bash
git clone https://github.com/rajat-ed/trafficsymphony.git
cd trafficsymphony
```

### 2. Set up a Virtual Environment (Optional but Recommended)
Prevents conflicts with other Python projects.
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
We need several libraries for computer vision, GUI, and audio processing. Create a text file named `requirements.txt` with the list below, or install them manually.

**requirements.txt content:**
```text
opencv-python
numpy
pygame
customtkinter
pillow
scipy
moviepy
```

**Install command:**
```bash
pip install -r requirements.txt
```
*Alternatively, run this single command:*
```bash
pip install opencv-python numpy pygame customtkinter pillow scipy moviepy
```

---

## 🚀 How to Use

1.  **Run the Application:**
    ```bash
    python tfs4.py
    ```

2.  **The Menu:**
    *   **Slider:** Adjust how many piano keys you want (4 = broad detection, 12 = precise notes).
    *   **Record Checkbox:** Check this if you want to save the result as a video file.
    *   **Start Webcam:** Uses your default camera.
    *   **Load Video:** Opens a file explorer to select a video file.

3.  **The Interface:**
    *   A window will pop up showing the video feed.
    *   The bottom 1/4th of the screen is the "Piano Zone".
    *   Green blocks indicate triggered notes.
    *   **To Stop:** Click on the video window and press **`Q`** on your keyboard.

4.  **Exporting (If Recording):**
    *   When you press `Q`, wait a few moments.
    *   The terminal will show "Synthesizing Audio..." and "Merging...".
    *   The video will automatically be saved to your **Desktop** or the project folder.
    *   The folder containing the video will open automatically.

---

## ⚙️ How It Works (Under the Hood)

1.  **ROI (Region of Interest):** The code isolates the bottom 25% of the video frame.
2.  **Frame Differencing:** It compares the current frame with the previous frame. It converts the images to grayscale and applies a Gaussian Blur to remove noise.
3.  **Thresholding:** Any pixel that changes significantly turns white (motion), while static pixels remain black.
4.  **Trigger Logic:** The width of the screen is divided by `N` segments. If the number of white pixels in a segment exceeds the `MOTION_THRESHOLD`, the corresponding note plays.
5.  **Audio Synthesis:**
    *   It does *not* play MP3 files.
    *   It calculates a 44.1kHz audio array: `sin(2 * pi * freq * time)`.
    *   It applies a decay formula `exp(-3 * t)` so the sound fades out like a real piano string.

---

## 🔧 Troubleshooting

**1. "Broken Pipe" or "FFmpeg Error" during export**
*   This usually happens if the file is locked or the path is incorrect.
*   **Fix:** The code is designed to save to the script folder first, then move to Desktop. Check the project folder if the file isn't on your Desktop.

**2. Audio is out of sync in the exported video**
*   **Fix:** The code uses frame-time synchronization rather than real-time synchronization. Ensure your computer is fast enough to process the video. If the video is very high resolution (4K), try resizing it or using a 720p/1080p video.

**3. "ModuleNotFoundError: No module named moviepy.editor"**
*   **Fix:** MoviePy recently updated to version 2.0. The code in this repo contains a robust fallback to handle both MoviePy v1.0 and v2.0 automatically. Ensure you ran `pip install moviepy`.

---

## 📝 License

This project is open-source and available under the **MIT License**.

---

