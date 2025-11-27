import cv2
import numpy as np
import pygame
import customtkinter as ctk
import time
import os
import sys
import shutil
import subprocess
from scipy.io.wavfile import write as write_wav

# --- Robust Import for MoviePy (Supports v1.0 and v2.0) ---
MOVIEPY_V2 = False
try:
    # Try MoviePy v2.0+ structure
    from moviepy import VideoFileClip, AudioFileClip
    MOVIEPY_V2 = True
except ImportError:
    # Fallback to MoviePy v1.0 structure
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
    except ImportError:
        print("CRITICAL ERROR: MoviePy library not found. Please run: pip install moviepy")

# --- Configuration ---
WIDTH = 800
HEIGHT = 600
MOTION_THRESHOLD = 500
COOLDOWN_DURATION = 0.3 
SAMPLE_RATE = 44100
FPS = 30.0

# --- Audio Synthesizer ---
class PianoSynthesizer:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
        except pygame.error:
            print("Audio device issue. Audio might be disabled.")
        
        self.raw_waves = [] 
        self.pygame_sounds = []
        self.generate_scale()

    def generate_scale(self):
        # Full Octave Frequencies (C4 to B4)
        frequencies = [
            261.63, 277.18, 293.66, 311.13, 329.63, 349.23,
            369.99, 392.00, 415.30, 440.00, 466.16, 493.88
        ]
        
        for freq in frequencies:
            waveform = self._make_waveform(freq)
            self.raw_waves.append(waveform)
            
            pcm_wave = (waveform * 32767).astype(np.int16)
            stereo_wave = np.column_stack((pcm_wave, pcm_wave))
            self.pygame_sounds.append(pygame.sndarray.make_sound(stereo_wave))

    def _make_waveform(self, frequency, duration=1.0):
        n_samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n_samples, False)
        waveform = np.sin(2 * np.pi * frequency * t)
        decay = np.exp(-3 * t) 
        waveform = waveform * decay * 0.5 
        return waveform

    def play_live(self, index):
        idx = index % len(self.pygame_sounds)
        self.pygame_sounds[idx].play()

    def get_raw_wave(self, index):
        idx = index % len(self.raw_waves)
        return self.raw_waves[idx]

# --- Video & Logic Processor ---
class VideoProcessor:
    def __init__(self, source, synthesizer, num_segments, record=False):
        self.cap = cv2.VideoCapture(source)
        self.synth = synthesizer
        self.num_segments = num_segments
        self.record = record
        self.last_played = [0] * num_segments
        
        self.recorded_events = [] 
        self.video_writer = None
        self.frame_count = 0
        
        if self.record:
            # Save temp file in current directory to avoid permission issues
            self.temp_video_path = os.path.join(os.getcwd(), 'temp_video.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self.video_writer = cv2.VideoWriter(self.temp_video_path, fourcc, FPS, (WIDTH, HEIGHT))

    def run(self):
        ret, frame1 = self.cap.read()
        if not ret: return

        frame1 = cv2.resize(frame1, (WIDTH, HEIGHT))
        roi_h = HEIGHT // 4
        roi_y = HEIGHT - roi_h
        
        gray1 = cv2.cvtColor(frame1[roi_y:HEIGHT, 0:WIDTH], cv2.COLOR_BGR2GRAY)
        gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)

        print(f"--- Started Processing with {self.num_segments} Segments ---")
        
        while True:
            ret, frame2 = self.cap.read()
            if not ret: break

            frame2 = cv2.resize(frame2, (WIDTH, HEIGHT))
            roi_curr = frame2[roi_y:HEIGHT, 0:WIDTH]
            gray2 = cv2.cvtColor(roi_curr, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)

            delta_frame = cv2.absdiff(gray1, gray2)
            thresh = cv2.threshold(delta_frame, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)

            overlay = frame2.copy()
            cv2.line(overlay, (0, roi_y), (WIDTH, roi_y), (0, 255, 255), 2)
            seg_w = WIDTH // self.num_segments
            
            current_live_time = time.time()
            current_video_time = self.frame_count / FPS 

            # Branding
            font = cv2.FONT_HERSHEY_SIMPLEX
            brand_text = "traffic symphony by rajat"
            (text_w, text_h), _ = cv2.getTextSize(brand_text, font, 0.7, 2)
            cv2.putText(frame2, brand_text, (WIDTH - text_w - 10, 30), font, 0.7, (255, 255, 255), 2)

            for i in range(self.num_segments):
                x_s = i * seg_w
                x_e = (i + 1) * seg_w
                
                mask = thresh[:, x_s:x_e]
                if cv2.countNonZero(mask) > MOTION_THRESHOLD:
                    if current_live_time - self.last_played[i] > COOLDOWN_DURATION:
                        self.synth.play_live(i)
                        self.last_played[i] = current_live_time
                        
                        if self.record:
                            self.recorded_events.append((i, current_video_time))
                            
                        cv2.rectangle(overlay, (x_s, roi_y), (x_e, HEIGHT), (0, 255, 0), -1)
                    elif current_live_time - self.last_played[i] < 0.2:
                        cv2.rectangle(overlay, (x_s, roi_y), (x_e, HEIGHT), (0, 255, 0), -1)

                cv2.line(overlay, (x_s, roi_y), (x_s, HEIGHT), (100, 100, 100), 1)

            frame_final = cv2.addWeighted(overlay, 0.4, frame2, 0.6, 0)
            cv2.putText(frame_final, "Press 'q' to Finish", (10, HEIGHT - 10), font, 0.5, (255,255,255), 1)

            cv2.imshow("Traffic Symphony", frame_final)
            
            if self.record and self.video_writer:
                self.video_writer.write(frame_final)
                self.frame_count += 1

            gray1 = gray2.copy()
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        self.cap.release()
        if self.video_writer:
            self.video_writer.release()
            print("Video writer released. Waiting for file lock...")
            time.sleep(2.0) # Safety pause to prevent broken pipe
            
        cv2.destroyAllWindows()

        if self.record:
            self.export_final_video()

    def get_desktop_path(self):
        # Robust Desktop Finder
        user_profile = os.path.expanduser("~")
        
        # Check Standard
        path = os.path.join(user_profile, "Desktop")
        if os.path.exists(path): return path
        
        # Check OneDrive
        path = os.path.join(user_profile, "OneDrive", "Desktop")
        if os.path.exists(path): return path
        
        # Fallback to Current Folder
        return os.getcwd()

    def export_final_video(self):
        print("Preparing Export...")
        
        temp_audio_path = os.path.join(os.getcwd(), 'temp_audio.wav')
        
        try:
            # 1. Load Video Clip
            video_clip = VideoFileClip(self.temp_video_path)
            video_duration = video_clip.duration
            print(f"Video Duration: {video_duration} seconds")

            # 2. Generate Audio
            total_samples = int((video_duration + 2.0) * SAMPLE_RATE)
            master_audio = np.zeros(total_samples)
            
            print("Synthesizing Audio...")
            for note_idx, start_time in self.recorded_events:
                start_sample = int(start_time * SAMPLE_RATE)
                raw_wave = self.synth.get_raw_wave(note_idx)
                end_sample = start_sample + len(raw_wave)
                if end_sample < total_samples:
                    master_audio[start_sample:end_sample] += raw_wave
            
            max_val = np.max(np.abs(master_audio))
            if max_val > 0: master_audio = master_audio / max_val
                
            write_wav(temp_audio_path, SAMPLE_RATE, master_audio.astype(np.float32))
            
            # 3. Merge
            print("Merging Audio and Video...")
            audio_clip = AudioFileClip(temp_audio_path)
            
            # Generate Output Filename in Current Directory first (Safe)
            filename = f"TrafficSymphony_Export_{int(time.time())}.mp4"
            output_path = os.path.join(os.getcwd(), filename)

            if MOVIEPY_V2:
                audio_clip = audio_clip.with_duration(video_duration) 
                final_clip = video_clip.with_audio(audio_clip)
            else:
                audio_clip = audio_clip.set_duration(video_duration)
                final_clip = video_clip.set_audio(audio_clip)
            
            # Write to current folder first
            final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
            
            print(f"Success! Video created at: {output_path}")
            
            # 4. Cleanup
            video_clip.close()
            audio_clip.close()
            time.sleep(0.5)
            if os.path.exists(self.temp_video_path): os.remove(self.temp_video_path)
            if os.path.exists(temp_audio_path): os.remove(temp_audio_path)

            # 5. Move to Desktop if possible
            desktop = self.get_desktop_path()
            final_desktop_path = os.path.join(desktop, filename)
            
            try:
                if desktop != os.getcwd():
                    shutil.move(output_path, final_desktop_path)
                    print(f"Moved to Desktop: {final_desktop_path}")
                    output_path = final_desktop_path
            except Exception as e:
                print(f"Could not move to Desktop (kept in source folder): {e}")

            # 6. Open Folder
            if os.name == 'nt': os.startfile(os.path.dirname(output_path))
            elif sys.platform == 'darwin': subprocess.Popen(['open', os.path.dirname(output_path)])
            else: subprocess.Popen(['xdg-open', os.path.dirname(output_path)])
            
        except Exception as e:
            print(f"Export failed: {e}")
            import traceback
            traceback.print_exc()

# --- Main GUI ---
class TrafficSymphonyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Traffic Symphony - By Rajat")
        self.geometry("500x520")
        ctk.set_appearance_mode("Dark")
        
        self.synth = PianoSynthesizer()
        
        self.lbl_title = ctk.CTkLabel(self, text="TRAFFIC SYMPHONY", font=("Impact", 24))
        self.lbl_title.pack(pady=(20, 5))
        
        self.lbl_sub = ctk.CTkLabel(self, text="Designed by Rajat", font=("Arial", 12))
        self.lbl_sub.pack(pady=(0, 15))

        self.slider_frame = ctk.CTkFrame(self)
        self.slider_frame.pack(pady=10, padx=20, fill="x")
        self.lbl_segments = ctk.CTkLabel(self.slider_frame, text="Number of Notes (Segments): 12")
        self.lbl_segments.pack(pady=5)
        self.slider = ctk.CTkSlider(self.slider_frame, from_=4, to=12, number_of_steps=8, command=self.update_slider_label)
        self.slider.set(12) 
        self.slider.pack(pady=10)

        self.record_var = ctk.BooleanVar(value=False)
        self.chk_record = ctk.CTkCheckBox(self, text="Record & Export Video", variable=self.record_var)
        self.chk_record.pack(pady=15)

        self.btn_cam = ctk.CTkButton(self, text="Start Webcam Feed", width=220, height=40,
                                     command=lambda: self.start_processing(0))
        self.btn_cam.pack(pady=10)

        self.btn_vid = ctk.CTkButton(self, text="Load Video File", width=220, height=40,
                                     command=self.load_video_file)
        self.btn_vid.pack(pady=10)

        self.lbl_info = ctk.CTkLabel(self, text="Press 'Q' to Stop/Export", text_color="gray")
        self.lbl_info.pack(pady=20)

    def update_slider_label(self, value):
        self.lbl_segments.configure(text=f"Number of Notes (Segments): {int(value)}")

    def load_video_file(self):
        path = ctk.filedialog.askopenfilename(filetypes=[("Video", "*.mp4;*.avi;*.mov")])
        if path:
            self.start_processing(path)

    def start_processing(self, source):
        self.withdraw()
        should_record = self.record_var.get()
        num_segs = int(self.slider.get())
        
        processor = VideoProcessor(source, self.synth, num_segments=num_segs, record=should_record)
        processor.run()
        self.deiconify()

if __name__ == "__main__":
    app = TrafficSymphonyApp()
    app.mainloop()