import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import time
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import customtkinter as ctk
import ctypes
import winsound

import matplotlib
matplotlib.use("TkAgg") 
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- High-Contrast Adaptive Palette (Light Mode Hex, Dark Mode Hex) ---
BG_COLOR = ("#F9FAFB", "#0D0D12")        
CARD_COLOR = ("#FFFFFF", "#1A1A24")      
ACCENT_COLOR = "#6366F1"                 
ACCENT_HOVER = "#4F46E5"
TEXT_PRIMARY = ("#111827", "#FFFFFF")    
TEXT_SECONDARY = ("#4B5563", "#A1A1AA")  
BORDER_COLOR = ("#E5E7EB", "#27272A")    

FONT_FAMILY = "Segoe UI"    

# --- System Appearance ---
ctk.set_appearance_mode("Dark")

def change_appearance_mode(new_mode):
    ctk.set_appearance_mode(new_mode)

# --- High-Quality Camera Font Setup (For Emojis) ---
try:
    DISPLAY_FONT = ImageFont.truetype("seguiemj.ttf", 36)
except:
    try:
        DISPLAY_FONT = ImageFont.truetype("arialbd.ttf", 36)
    except:
        DISPLAY_FONT = ImageFont.load_default()

# --- Mediapipe Setup ---
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=3, refine_landmarks=True)

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]

# --- Global Variables ---
paused = False
last_action_time = 0
running = False
cap = None
mini_mode_active = False

session_start_time = 0
total_distracted_time = 0
distraction_start_time = 0
distraction_count = 0
is_currently_distracted = False
blink_count = 0
is_blinking = False
history_timestamps = []
history_focus_scores = []
last_log_time = 0

last_work_start = 0
break_active = False
break_accumulated_time = 0  
break_look_away_start = 0   

# --- Core Logic Functions ---
def calculate_EAR(eye_points, landmarks, w, h):
    points = []
    for point in eye_points:
        x = int(landmarks[point].x * w)
        y = int(landmarks[point].y * h)
        points.append((x, y))
    A = np.linalg.norm(np.array(points[1]) - np.array(points[5]))
    B = np.linalg.norm(np.array(points[2]) - np.array(points[4]))
    C = np.linalg.norm(np.array(points[0]) - np.array(points[3]))
    return (A + B) / (2.0 * C)

def trigger_away_action():
    action = action_var.get()
    if action == "Play/Pause (Space)": pyautogui.press('space')
    elif action == "Mute Audio": pyautogui.press('volumemute')
    elif action == "Lock Windows": ctypes.windll.user32.LockWorkStation()

def trigger_focus_action():
    action = action_var.get()
    if action == "Play/Pause (Space)": pyautogui.press('space')
    elif action == "Mute Audio": pyautogui.press('volumemute')

def update_camera():
    global paused, last_action_time, cap, running
    global is_currently_distracted, distraction_count, distraction_start_time, total_distracted_time
    global blink_count, is_blinking, last_log_time
    global last_work_start, break_active, break_accumulated_time, break_look_away_start

    if not running: return

    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1) 
        h, w, _ = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)
        current_time = time.time()
        
        current_ear_threshold = ear_slider.get()
        current_head_threshold = head_slider.get()
        current_work_duration = work_slider.get() * 60  
        current_break_duration = break_slider.get()     
        current_delay = float(delay_var.get().split()[0]) # Reaction Time

        text = "👤 NO FACE"
        ctk_color = "#A1A1AA"
        is_looking_away = False

        if result.multi_face_landmarks:
            closest_face = None
            max_face_width = 0

            for face in result.multi_face_landmarks:
                left_edge = face.landmark[234].x
                right_edge = face.landmark[454].x
                face_width = abs(right_edge - left_edge)
                if face_width > max_face_width:
                    max_face_width = face_width
                    closest_face = face

            if closest_face:
                landmarks = closest_face.landmark
                nose = landmarks[1]
                difference = abs(int(nose.x * w) - (w // 2))

                if difference > current_head_threshold:
                    is_looking_away = True
                    text = "🛑 LOOKING AWAY"
                    ctk_color = "#ef4444"
                else:
                    EAR = (calculate_EAR(LEFT_EYE, landmarks, w, h) + calculate_EAR(RIGHT_EYE, landmarks, w, h)) / 2
                    if EAR < current_ear_threshold:
                        if not is_blinking:
                            blink_count += 1
                            is_blinking = True
                        is_looking_away = True
                        text = "👀 DISTRACTED"
                        ctk_color = "#f59e0b"
                    else:
                        is_blinking = False
                        text = "🎯 FOCUSED"
                        ctk_color = "#10b981"

        if health_timer_var.get() and running:
            if not break_active and (current_time - last_work_start >= current_work_duration):
                break_active = True
                break_accumulated_time = 0
                break_look_away_start = current_time if is_looking_away else 0
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION) 

            if break_active:
                ctk_color = "#06b6d4"
                if is_looking_away:
                    if break_look_away_start == 0: break_look_away_start = current_time 
                    current_chunk = current_time - break_look_away_start
                    total_done = break_accumulated_time + current_chunk
                    time_left = max(0, int(current_break_duration - total_done))
                    text = f"⚠ EYE BREAK: {time_left}s LEFT"
                    
                    if total_done >= current_break_duration:
                        break_active = False
                        last_work_start = current_time 
                        break_accumulated_time = 0
                        break_look_away_start = 0
                        winsound.MessageBeep(winsound.MB_OK) 
                else:
                    if break_look_away_start > 0:
                        break_accumulated_time += (current_time - break_look_away_start)
                        break_look_away_start = 0
                    time_left = max(0, int(current_break_duration - break_accumulated_time))
                    text = f"⏸ PAUSED: {time_left}s REMAINING"

        if not break_active:
            if is_looking_away:
                if not is_currently_distracted:
                    is_currently_distracted = True
                    distraction_count += 1
                    distraction_start_time = current_time
                if not paused and current_time - last_action_time > current_delay:
                    trigger_away_action()
                    paused = True
                    last_action_time = current_time
            else:
                if is_currently_distracted:
                    is_currently_distracted = False
                    total_distracted_time += (current_time - distraction_start_time)
                if paused and current_time - last_action_time > current_delay:
                    trigger_focus_action()
                    paused = False
                    last_action_time = current_time

        # Update Analytics Live
        focus_score = 100
        if current_time - last_log_time >= 1.0 and session_start_time > 0:
            total_time = current_time - session_start_time
            live_distracted = total_distracted_time
            if is_currently_distracted: live_distracted += (current_time - distraction_start_time)
            focus_score = max(0, min(100, 100 - (live_distracted / total_time * 100))) if total_time > 0 else 100
            history_timestamps.append(total_time)
            history_focus_scores.append(focus_score)
            last_log_time = current_time
            update_analytics_ui()

        if mini_mode_active:
            mini_status_label.configure(text=text, text_color=ctk_color)
            mini_progress.set(focus_score / 100)
            mini_progress.configure(progress_color=ctk_color)
        else:
            # PIL Image Overlay with Anti-Freeze TK Label
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(img)
            draw.text((32, 42), text, font=DISPLAY_FONT, fill="#000000")
            draw.text((30, 40), text, font=DISPLAY_FONT, fill=ctk_color)
            
            img = img.resize((720, 480))
            tk_img = ImageTk.PhotoImage(image=img)
            camera_label.configure(image=tk_img)
            camera_label.image = tk_img 

    root.after(30, update_camera)

def update_analytics_ui():
    if not running or session_start_time == 0: return
    current_time = time.time()
    total_time = (current_time - session_start_time)
    live_distracted = total_distracted_time
    if is_currently_distracted: live_distracted += (current_time - distraction_start_time)
    focused_time = max(0, total_time - live_distracted)
    final_score = int(max(0, min(100, 100 - (live_distracted / total_time * 100)))) if total_time > 0 else 100
    blink_rate = int(blink_count / (total_time / 60.0)) if total_time > 0 else 0

    kpi_score_val.configure(text=f"{final_score}%", text_color="#10b981" if final_score > 80 else "#f59e0b")
    kpi_time_val.configure(text=f"{int(total_time//60)}m {int(total_time%60)}s")
    kpi_distract_val.configure(text=f"{int(live_distracted//60)}m {int(live_distracted%60)}s")
    kpi_blink_val.configure(text=f"{blink_rate} /min")

    # Only draw the heavy charts if the user is looking at them
    if main_tabview.get() == " 📊 Analytics ":
        draw_graphs(focused_time, live_distracted, total_time)

def draw_graphs(focused_time, live_distracted, total_time):
    ax1.clear(); ax2.clear()
    chart_bg = "#FFFFFF" if ctk.get_appearance_mode() == "Light" else "#1A1A24"
    text_col = "#111827" if ctk.get_appearance_mode() == "Light" else "#A1A1AA"
    grid_col = "#E5E7EB" if ctk.get_appearance_mode() == "Light" else "#2c2c35"
    fig.set_facecolor(chart_bg); ax1.set_facecolor(chart_bg); ax2.set_facecolor(chart_bg)

    if total_time > 0:
        ax1.pie([focused_time, live_distracted], labels=['Focused', 'Distracted'], colors=['#10b981', '#ef4444'], autopct='%1.0f%%', startangle=90, textprops={'color':text_col, 'weight':'bold'})
        ax1.set_title("Time Distribution", color=text_col, pad=15)
    
    if len(history_timestamps) > 1:
        ax2.plot(history_timestamps, history_focus_scores, color=ACCENT_COLOR, linewidth=3)
        ax2.fill_between(history_timestamps, history_focus_scores, color=ACCENT_COLOR, alpha=0.15)
        ax2.set_title("Focus Trend", color=text_col, pad=15)
        ax2.grid(True, color=grid_col, linestyle='-', linewidth=0.5)
        ax2.tick_params(colors=text_col)

    canvas.draw_idle()

def on_tab_change():
    if main_tabview.get() == " 📊 Analytics " and running:
        update_analytics_ui()

def enable_mini_mode():
    global mini_mode_active
    mini_mode_active = True
    sidebar_frame.pack_forget()
    main_tabview.pack_forget()
    root.geometry("300x140")
    root.attributes("-topmost", True)
    mini_frame.pack(fill="both", expand=True)

def maximize_app():
    global mini_mode_active
    mini_mode_active = False
    mini_frame.pack_forget()
    root.geometry("1200x700")
    root.attributes("-topmost", False)
    sidebar_frame.pack(side="left", fill="y")
    main_tabview.pack(side="right", fill="both", expand=True, padx=25, pady=25)

def start_app():
    global running, cap, session_start_time, total_distracted_time, distraction_count, is_currently_distracted
    global history_timestamps, history_focus_scores, last_log_time, blink_count, is_blinking, last_work_start, break_active, break_accumulated_time
    
    if not running:
        cam_idx = int(camera_var.get().split()[-1])
        cap = cv2.VideoCapture(cam_idx, cv2.CAP_DSHOW) # Essential for preventing freeze
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)            # Essential for smooth queue
        
        session_start_time = time.time()
        last_work_start = time.time()
        last_log_time = session_start_time
        total_distracted_time = 0
        distraction_count = 0
        blink_count = 0
        is_blinking = False
        is_currently_distracted = False
        break_active = False
        break_accumulated_time = 0
        history_timestamps = []
        history_focus_scores = []
        
        running = True
        update_camera()
        status_indicator.configure(text="● ACTIVE", text_color="#10b981")
        status_frame.configure(border_color="#10b981")
        mini_btn.configure(state="normal")
        main_tabview.set(" 📷 Live Camera ")

def stop_app():
    global running, cap
    running = False
    if cap: cap.release()
    camera_label.configure(image="")
    status_indicator.configure(text="● STANDBY", text_color="#ef4444")
    status_frame.configure(border_color=BORDER_COLOR)
    mini_btn.configure(state="disabled")

def update_work_label(value): work_val_label.configure(text=f"{int(value)} Min")
def update_break_label(value): break_val_label.configure(text=f"{int(value)} Sec")

# ==========================================
# --- APP INITIALIZATION & UI SETUP --------
# ==========================================
root = ctk.CTk()
root.title("FocusPauser")
root.geometry("1200x700")
root.configure(fg_color=BG_COLOR)
root.withdraw() 

# --- VARIABLES ---
camera_var = ctk.StringVar(value="Camera 0")
action_var = ctk.StringVar(value="Play/Pause (Space)")
health_timer_var = ctk.BooleanVar(value=True)
delay_var = ctk.StringVar(value="2 Seconds")

# --- SPLASH SCREEN ---
splash_window = ctk.CTkToplevel(root)
splash_window.overrideredirect(True)
splash_window.configure(fg_color="#0D0D12")
splash_window.attributes("-topmost", True)

sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
splash_window.geometry(f"500x300+{int(sw/2-250)}+{int(sh/2-150)}")

logo_container = ctk.CTkFrame(splash_window, fg_color="transparent")
logo_container.place(relx=0.5, rely=0.5, anchor="center")

word_label = ctk.CTkLabel(logo_container, text="FocusPauser", font=(FONT_FAMILY, 42, "bold"), text_color="#FFFFFF")
word_label.pack(side="left")

dot_label = ctk.CTkLabel(logo_container, text=".", font=(FONT_FAMILY, 42, "bold"), text_color=ACCENT_COLOR)

sub_label = ctk.CTkLabel(splash_window, text="Attention Monitoring System", font=(FONT_FAMILY, 14), text_color=ACCENT_COLOR)
splash_progress = ctk.CTkProgressBar(splash_window, width=300, height=6, progress_color=ACCENT_COLOR, fg_color="#1A1A24")
splash_progress.set(0)
loading_text = ctk.CTkLabel(splash_window, text="Initializing Engine...", font=(FONT_FAMILY, 12), text_color="#A1A1AA")

def finish_splash():
    splash_window.destroy()
    root.deiconify()

def anim_step_3():
    current = splash_progress.get()
    if current < 1.0:
        splash_progress.set(current + 0.06)
        root.after(30, anim_step_3)
    else:
        loading_text.configure(text="System Ready.", text_color="#10b981")
        root.after(400, finish_splash)

def anim_step_2():
    logo_container.place_configure(rely=0.35)
    sub_label.place(relx=0.5, rely=0.52, anchor="center")
    splash_progress.place(relx=0.5, rely=0.68, anchor="center")
    loading_text.place(relx=0.5, rely=0.78, anchor="center")
    anim_step_3()

def anim_step_1():
    dot_label.pack(side="left")
    dot_label.configure(font=(FONT_FAMILY, 56, "bold"))
    root.after(100, lambda: dot_label.configure(font=(FONT_FAMILY, 46, "bold")))
    root.after(600, anim_step_2)

root.after(600, anim_step_1)

# --- 1. SIDEBAR ---
sidebar_frame = ctk.CTkFrame(root, width=280, corner_radius=0, fg_color=CARD_COLOR, border_width=1, border_color=BORDER_COLOR)
sidebar_frame.pack(side="left", fill="y")

logo_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
logo_frame.pack(pady=(30, 10), padx=20, fill="x")
ctk.CTkLabel(logo_frame, text="FocusPauser", font=(FONT_FAMILY, 26, "bold"), text_color=TEXT_PRIMARY).pack(side="left")
ctk.CTkLabel(logo_frame, text=".", font=(FONT_FAMILY, 26, "bold"), text_color=ACCENT_COLOR).pack(side="left")

status_frame = ctk.CTkFrame(sidebar_frame, fg_color=BORDER_COLOR, corner_radius=12, height=28, border_width=1, border_color=BORDER_COLOR)
status_frame.pack(pady=(0, 20), padx=25, anchor="w")
status_indicator = ctk.CTkLabel(status_frame, text="● STANDBY", text_color="#ef4444", font=(FONT_FAMILY, 11, "bold"))
status_indicator.pack(padx=12, pady=3)

# Premium Buttons
ctk.CTkButton(sidebar_frame, text="▶ Start Session", fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, text_color="#FFFFFF", height=45, corner_radius=10, font=(FONT_FAMILY, 14, "bold"), command=start_app).pack(pady=5, padx=25, fill="x")
ctk.CTkButton(sidebar_frame, text="■ End Session", fg_color="transparent", border_width=1.5, border_color=TEXT_SECONDARY, hover_color="#dc2626", text_color=TEXT_PRIMARY, height=45, corner_radius=10, font=(FONT_FAMILY, 14, "bold"), command=stop_app).pack(pady=5, padx=25, fill="x")
mini_btn = ctk.CTkButton(sidebar_frame, text="◱ Mini Widget", fg_color="transparent", border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_PRIMARY, height=42, corner_radius=10, font=(FONT_FAMILY, 13, "bold"), command=enable_mini_mode, state="disabled")
mini_btn.pack(pady=(15, 5), padx=25, fill="x")

# Tracking Sensitivity Panel
ctk.CTkLabel(sidebar_frame, text="TRACKING SENSITIVITY", font=(FONT_FAMILY, 10, "bold"), text_color=TEXT_SECONDARY).pack(pady=(20, 5), anchor="w", padx=30)

def select_preset(preset, auto_update=True):
    for b in [btn_strict, btn_normal, btn_relaxed, btn_custom]: 
        b.configure(fg_color="transparent", border_color=BORDER_COLOR, text_color=TEXT_SECONDARY)
    
    presets = {
        "Strict": (btn_strict, 0.26, 40, "1 Second"),
        "Normal": (btn_normal, 0.23, 60, "2 Seconds"),
        "Relaxed": (btn_relaxed, 0.18, 100, "5 Seconds"),
        "Custom": (btn_custom, None, None, None)
    }
    
    button, ear, head, delay = presets[preset]
    button.configure(fg_color=BORDER_COLOR, border_color=ACCENT_COLOR, text_color=TEXT_PRIMARY)
    
    if auto_update and preset != "Custom":
        ear_slider.set(ear)
        head_slider.set(head)
        delay_var.set(delay)

btn_strict = ctk.CTkButton(sidebar_frame, text="⚡ Strict Focus", height=35, corner_radius=8, border_width=1, command=lambda: select_preset("Strict"))
btn_strict.pack(pady=2, padx=25, fill="x")
btn_normal = ctk.CTkButton(sidebar_frame, text="🎯 Normal Mode", height=35, corner_radius=8, border_width=1, command=lambda: select_preset("Normal"))
btn_normal.pack(pady=2, padx=25, fill="x")
btn_relaxed = ctk.CTkButton(sidebar_frame, text="☕ Relaxed Watch", height=35, corner_radius=8, border_width=1, command=lambda: select_preset("Relaxed"))
btn_relaxed.pack(pady=2, padx=25, fill="x")
btn_custom = ctk.CTkButton(sidebar_frame, text="⚙️ Custom Tuning", height=35, corner_radius=8, border_width=1, command=lambda: select_preset("Custom", False))
btn_custom.pack(pady=2, padx=25, fill="x")

slider_f = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
slider_f.pack(fill="x", pady=(10, 10), padx=25)

ctk.CTkLabel(slider_f, text="Eye Tracking Tolerance", font=(FONT_FAMILY, 11), text_color=TEXT_SECONDARY).pack(anchor="w")
ear_slider = ctk.CTkSlider(slider_f, from_=0.15, to=0.35, button_color=ACCENT_COLOR, progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR, command=lambda _: select_preset("Custom", False))
ear_slider.pack(pady=(2, 12), fill="x")

ctk.CTkLabel(slider_f, text="Head Turn Tolerance", font=(FONT_FAMILY, 11), text_color=TEXT_SECONDARY).pack(anchor="w")
head_slider = ctk.CTkSlider(slider_f, from_=20, to=150, button_color=ACCENT_COLOR, progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR, command=lambda _: select_preset("Custom", False))
head_slider.pack(pady=(2, 10), fill="x")
select_preset("Normal")

# --- 2. TABS ---
main_tabview = ctk.CTkTabview(root, fg_color="transparent", segmented_button_selected_color=ACCENT_COLOR, segmented_button_unselected_color=BORDER_COLOR, text_color=TEXT_PRIMARY, command=on_tab_change)
main_tabview.pack(side="right", fill="both", expand=True, padx=25, pady=15)

tab_camera = main_tabview.add(" 📷 Live Camera ")
tab_analytics = main_tabview.add(" 📊 Analytics ")
tab_health = main_tabview.add(" 💚 Health ")
tab_settings = main_tabview.add(" ⚙ Settings ")

# TAB 1: Camera
camera_card = ctk.CTkFrame(tab_camera, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
camera_card.pack(fill="both", expand=True, pady=10)
# Standard TK Label prevents memory leak/video freeze
camera_label = tk.Label(camera_card, text="Ready. Click Start Session.", font=(FONT_FAMILY, 16), bg="#1A1A24", fg="#A1A1AA")
camera_label.pack(expand=True)

# TAB 2: Analytics Live
kpi_f = ctk.CTkFrame(tab_analytics, fg_color="transparent")
kpi_f.pack(fill="x", pady=(10, 20))
kpi_f.columnconfigure((0, 1, 2, 3), weight=1)

def create_kpi_card(parent, title, default_val, col):
    f = ctk.CTkFrame(parent, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
    f.grid(row=0, column=col, padx=8, sticky="ew")
    ctk.CTkLabel(f, text=title, text_color=TEXT_SECONDARY, font=(FONT_FAMILY, 11, "bold")).pack(pady=(15, 0))
    lbl = ctk.CTkLabel(f, text=default_val, text_color=TEXT_PRIMARY, font=(FONT_FAMILY, 28, "bold"))
    lbl.pack(pady=(5, 20))
    return lbl

kpi_score_val = create_kpi_card(kpi_f, "FOCUS SCORE", "--%", 0)
kpi_time_val = create_kpi_card(kpi_f, "TOTAL TIME", "0m 0s", 1)
kpi_distract_val = create_kpi_card(kpi_f, "DISTRACTION TIME", "0m 0s", 2)
kpi_blink_val = create_kpi_card(kpi_f, "BLINK RATE", "0 /min", 3)

graph_card = ctk.CTkFrame(tab_analytics, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
graph_card.pack(fill="both", expand=True, padx=8)

fig = Figure(figsize=(8, 3.5), dpi=100)
ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)
canvas = FigureCanvasTkAgg(fig, master=graph_card)
canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

# TAB 3: Health
health_card = ctk.CTkFrame(tab_health, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
health_card.pack(fill="both", expand=True, pady=10, padx=20)

ctk.CTkLabel(health_card, text="Eye Strain Protection", font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_PRIMARY).pack(pady=(30, 10), anchor="w", padx=40)
ctk.CTkLabel(health_card, text="Automated 20-20-20 rule tracking.", font=(FONT_FAMILY, 14), text_color=TEXT_SECONDARY).pack(anchor="w", padx=40, pady=(0, 30))

r1 = ctk.CTkFrame(health_card, fg_color="transparent")
r1.pack(fill="x", padx=40, pady=15)
ctk.CTkLabel(r1, text="Enable Break Reminders", font=(FONT_FAMILY, 16), text_color=TEXT_PRIMARY).pack(side="left")
ctk.CTkSwitch(r1, text="", variable=health_timer_var, progress_color=ACCENT_COLOR).pack(side="right")

r2 = ctk.CTkFrame(health_card, fg_color="transparent")
r2.pack(fill="x", padx=40, pady=15)
ctk.CTkLabel(r2, text="Focus Time Limit", font=(FONT_FAMILY, 16), text_color=TEXT_PRIMARY).pack(side="left")
work_val_label = ctk.CTkLabel(r2, text="20 Min", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_PRIMARY, width=60)
work_val_label.pack(side="right")
work_slider = ctk.CTkSlider(r2, from_=1, to=60, command=update_work_label, button_color=ACCENT_COLOR, progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR)
work_slider.set(20)
work_slider.pack(side="right", padx=15)

r3 = ctk.CTkFrame(health_card, fg_color="transparent")
r3.pack(fill="x", padx=40, pady=15)
ctk.CTkLabel(r3, text="Required Rest Time", font=(FONT_FAMILY, 16), text_color=TEXT_PRIMARY).pack(side="left")
break_val_label = ctk.CTkLabel(r3, text="20 Sec", font=(FONT_FAMILY, 14, "bold"), text_color=TEXT_PRIMARY, width=60)
break_val_label.pack(side="right")
break_slider = ctk.CTkSlider(r3, from_=5, to=120, command=update_break_label, button_color=ACCENT_COLOR, progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR)
break_slider.set(20)
break_slider.pack(side="right", padx=15)

# TAB 4: Settings
settings_card = ctk.CTkFrame(tab_settings, fg_color=CARD_COLOR, corner_radius=15, border_width=1, border_color=BORDER_COLOR)
settings_card.pack(fill="both", expand=True, pady=10, padx=20)

ctk.CTkLabel(settings_card, text="Hardware & Preferences", font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_PRIMARY).pack(pady=(30, 10), anchor="w", padx=40)

dropdown_cfg = {"fg_color": BORDER_COLOR, "button_color": BORDER_COLOR, "button_hover_color": ACCENT_COLOR, "dropdown_fg_color": CARD_COLOR, "dropdown_text_color": TEXT_PRIMARY, "text_color": TEXT_PRIMARY}
prefs = [
    ("UI Appearance:", None, ["Dark", "Light", "System"]), 
    ("Video Source:", camera_var, ["Camera 0", "Camera 1", "Camera 2"]), 
    ("Look-Away Trigger:", action_var, ["Play/Pause (Space)", "Mute Audio", "Lock Windows"]), 
    ("Reaction Time:", delay_var, ["1 Second", "2 Seconds", "3 Seconds", "5 Seconds"])
]

for label, var, vals in prefs:
    row = ctk.CTkFrame(settings_card, fg_color="transparent")
    row.pack(fill="x", padx=40, pady=10)
    ctk.CTkLabel(row, text=label, font=(FONT_FAMILY, 16), text_color=TEXT_PRIMARY).pack(side="left")
    if label == "UI Appearance:": 
        ctk.CTkOptionMenu(row, values=vals, command=change_appearance_mode, **dropdown_cfg).pack(side="right")
    else: 
        ctk.CTkOptionMenu(row, variable=var, values=vals, **dropdown_cfg).pack(side="right")

# --- 3. MINI WIDGET ---
mini_frame = ctk.CTkFrame(root, fg_color=CARD_COLOR, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
mini_status_label = ctk.CTkLabel(mini_frame, text="STANDBY", font=(FONT_FAMILY, 20, "bold"), text_color=TEXT_PRIMARY)
mini_status_label.pack(pady=(20, 10))

mini_progress = ctk.CTkProgressBar(mini_frame, width=200, height=6, progress_color=ACCENT_COLOR, fg_color=BORDER_COLOR)
mini_progress.set(1.0)
mini_progress.pack(pady=(0, 15))

ctk.CTkButton(mini_frame, text="⤢ Expand", fg_color="transparent", border_width=1, border_color=BORDER_COLOR, hover_color=BORDER_COLOR, text_color=TEXT_PRIMARY, height=32, corner_radius=8, command=maximize_app).pack(pady=(5, 10))

root.mainloop()