# FocusPauser 🎯

**FocusPauser** is a real-time attention monitoring desktop application that uses a webcam and computer vision to detect whether the user is focused, looking away, or blinking. It can automatically control media playback, mute audio, or lock the Windows workstation when prolonged distraction is detected.

The application also provides **focus analytics, distraction tracking, blink-rate monitoring, configurable sensitivity, eye-break reminders, and a compact always-on-top mini widget**.

---

## ✨ Features

### 👁️ Real-Time Attention Monitoring

* Uses the webcam to monitor the user's face.
* Detects whether the user is:

  * 🎯 Focused
  * 👀 Blinking / distracted
  * 🛑 Looking away
  * 👤 Not detected
* Uses **MediaPipe Face Mesh** for facial landmark detection.
* Supports detection of multiple faces and selects the closest/largest detected face.

### 🎮 Automatic Computer Actions

When the application detects that the user has looked away for the configured reaction time, it can automatically:

* ▶️ Pause/play media using the `Space` key
* 🔇 Mute system audio
* 🔒 Lock the Windows workstation

The action can be selected from the Settings panel.

### 📊 Focus Analytics

The application records session information and displays:

* Focus Score
* Total Session Time
* Total Distraction Time
* Blink Rate
* Focused vs. Distracted time
* Focus trend over time

Analytics are displayed using interactive Matplotlib charts.

### 💚 Eye Health Protection

FocusPauser includes an automated eye-break system based on the **20-20-20 rule**.

Users can configure:

* Focus/work duration
* Required rest duration
* Enable/disable break reminders

During a break, the application monitors whether the user looks away and tracks the completed break duration.

### ⚙️ Customizable Sensitivity

Three predefined monitoring modes are available:

* **Strict Focus**
* **Normal Mode**
* **Relaxed Watch**

There is also a **Custom Tuning** mode that allows the user to adjust:

* Eye tracking tolerance
* Head-turn tolerance
* Reaction time

### 🌓 Appearance Settings

The interface supports:

* Dark mode
* Light mode
* System appearance

### 📷 Camera Selection

Users can select between available camera sources such as:

* Camera 0
* Camera 1
* Camera 2

### 🖥️ Mini Widget

FocusPauser includes a compact mini mode that displays the current attention status and focus progress.

The widget stays on top of other windows and can be expanded back into the main application.

### 🎨 Modern Desktop Interface

The application uses **CustomTkinter** to provide a modern desktop UI containing:

* Splash screen
* Sidebar navigation
* Live camera view
* Analytics dashboard
* Health settings
* Application settings
* Mini widget

---

# 🧠 How It Works

The application follows this general pipeline:

```text
Webcam
   ↓
OpenCV captures video
   ↓
MediaPipe Face Mesh
   ↓
Facial landmarks detected
   ↓
Head position + Eye Aspect Ratio calculated
   ↓
Attention state determined
   ↓
Focused / Distracted / Looking Away
   ↓
Automatic action triggered
   ↓
Analytics updated
```

## 1. Camera Capture

OpenCV continuously captures frames from the selected webcam.

The camera frame is flipped horizontally to provide a mirror-like experience.

## 2. Face Detection

MediaPipe Face Mesh detects facial landmarks from the camera frame.

The application can process up to three faces and selects the face with the largest detected width as the primary user.

## 3. Head-Turn Detection

The position of the nose landmark is compared with the horizontal center of the camera frame.

If the difference exceeds the configured head-turn threshold, the application considers the user to be looking away.

## 4. Eye Detection

The application uses selected MediaPipe eye landmarks to calculate the **Eye Aspect Ratio (EAR)**.

The basic calculation is:

```text
EAR = (A + B) / (2 × C)
```

where the vertical and horizontal distances between eye landmarks are used to estimate whether the eye is open or closed.

If the EAR falls below the configured threshold, the application detects a blink/distraction state.

## 5. Distraction Detection

When the user is looking away or blinking for long enough, the application:

1. Records the distraction.
2. Starts measuring distraction duration.
3. Waits for the configured reaction time.
4. Performs the selected action.

When the user returns to a focused state, the application can reverse actions such as pausing media.

## 6. Focus Score

The application calculates a live focus score based on the amount of time spent distracted during the session.

Conceptually:

```text
Focus Score =
100 - (Distracted Time / Total Session Time × 100)
```

The result is constrained between 0 and 100.

## 7. Analytics

During the session, focus scores are recorded over time.

This data is used to generate:

* Time Distribution chart
* Focus Trend chart

The dashboard also displays total time, distraction time, focus score, and blink rate.

---

# ⌨️ Keyboard Shortcuts

The current application does **not implement dedicated application keyboard shortcuts** such as `Ctrl+S`, `Ctrl+Q`, etc.

However, it can use the following keyboard/system actions:

| Key / Action | Function                                    |
| ------------ | ------------------------------------------- |
| `Space`      | Used by the Play/Pause action               |
| System Mute  | Mutes system audio when selected            |
| Windows Lock | Locks the Windows workstation when selected |

The `Space` action is triggered automatically by the application when the configured distraction condition is met.

---

# 🛠️ Technologies Used

| Technology        | Purpose                                 |
| ----------------- | --------------------------------------- |
| **Python**        | Core programming language               |
| **OpenCV**        | Webcam/video processing                 |
| **MediaPipe**     | Face mesh and facial landmark detection |
| **NumPy**         | Mathematical calculations               |
| **PyAutoGUI**     | Keyboard/system automation              |
| **CustomTkinter** | Modern graphical user interface         |
| **Tkinter**       | Base desktop UI functionality           |
| **Pillow (PIL)**  | Image processing and camera display     |
| **Matplotlib**    | Analytics and visualization             |
| **ctypes**        | Windows system functions                |
| **winsound**      | Break notification sounds               |

---

# 📁 Project Structure

A recommended GitHub structure is:

```text
FocusPauser/
│
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
│
└── screenshots/
    ├── dashboard.png
    ├── analytics.png
    └── mini-widget.png
```

At the moment, the supplied code is implemented as a single Python application. Splitting it into separate modules would make future development easier.

---

# 🚀 How to Run

## 1. Install Python

Install **Python 3.10+** on Windows.

Verify the installation:

```bash
python --version
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/FocusPauser.git
cd FocusPauser
```

---

## 3. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

---

## 4. Install Dependencies

Create a `requirements.txt` file containing:

```text
opencv-python
mediapipe
numpy
pyautogui
Pillow
customtkinter
matplotlib
```

Then run:

```bash
pip install -r requirements.txt
```

> **Note:** `tkinter`, `ctypes`, `time`, and `winsound` are part of the standard Python/Windows environment and normally do not need to be installed separately.

---

## 5. Run the Application

```bash
python main.py
```

Allow camera access if Windows asks for permission.

Click:

**▶ Start Session**

The webcam will begin monitoring your attention.

---

# 🖥️ Windows Compatibility

FocusPauser is currently designed primarily for **Windows** because some functionality uses Windows-specific APIs.

In particular:

* `ctypes.windll.user32.LockWorkStation()` is Windows-specific.
* `winsound` is Windows-specific.
* The DirectShow camera backend (`cv2.CAP_DSHOW`) is used for camera capture.

Therefore, some functionality may not work correctly on Linux or macOS without modification.

---

# 📚 What I Learned

Developing FocusPauser helped me understand how different technologies can be combined into a complete AI/computer-vision application.

### Computer Vision

I learned how to:

* Capture real-time webcam video using OpenCV.
* Process video frames continuously.
* Convert images between different color spaces.
* Work with facial landmarks.
* Use MediaPipe Face Mesh.
* Calculate Eye Aspect Ratio.
* Detect changes in head position.

### AI / Machine Learning Concepts

Although the project does not train a custom machine-learning model, I learned how to use a **pre-trained computer vision model** as part of a real-world application.

This helped me understand the difference between:

```text
Training an AI model
        ↓
Using a pre-trained AI model
        ↓
Building an application around the model
```

### GUI Development

I learned how to build a desktop application using:

* Tkinter
* CustomTkinter
* Frames and layouts
* Tabs
* Sliders
* Buttons
* Progress bars
* Dropdown menus
* Dynamic UI updates

### Real-Time Programming

The application continuously processes camera frames while simultaneously updating the graphical interface.

This required understanding:

* Timers
* State variables
* Event-driven programming
* Real-time data updates
* Resource management

### Data Visualization

I learned how to collect real-time session data and convert it into useful visualizations using Matplotlib.

### System Automation

I learned how Python can interact with the operating system to perform actions such as:

* Simulating keyboard input
* Muting audio
* Locking Windows

---

# 🔮 Future Improvements

Several improvements can be made to make FocusPauser more accurate, reliable, and feature-rich.

### 1. Better Head Pose Estimation

The current system primarily uses the horizontal position of the nose to detect head turns.

A future version could use full **3D head-pose estimation** to detect:

* Left/right rotation
* Up/down movement
* Tilting

This could significantly improve attention detection.

### 2. Better Blink Detection

The current system treats a low EAR as a distraction state.

A future version could distinguish between:

* Normal blink
* Long blink
* Eye closure
* Genuine distraction

This would reduce false distraction detections.

### 3. Gaze Tracking

Future versions could estimate where the user is actually looking instead of relying mainly on head position.

For example:

```text
Looking at screen → Focused
Looking away → Distracted
Looking down → Possibly distracted
```

### 4. User Calibration

Different users have different facial structures and camera positions.

A calibration system could learn the user's normal:

* Eye Aspect Ratio
* Face position
* Head position
* Camera distance

This could improve accuracy.

### 5. Machine Learning-Based Classification

The current system relies on threshold-based rules.

A future version could collect features such as:

```text
EAR
Head angle
Face position
Gaze direction
Blink frequency
Distraction duration
```

and use them to train a classification model.

### 6. Session History

Currently, analytics primarily represent the active session.

A future version could save sessions to a database and provide:

* Daily focus score
* Weekly focus score
* Monthly trends
* Average distraction time
* Productivity history

### 7. More Automation Options

Additional actions could include:

* Pause YouTube
* Pause Spotify
* Send notifications
* Show desktop notifications
* Start a Pomodoro timer
* Automatically start an eye break

### 8. Cross-Platform Support

The application could be redesigned to support:

* Windows
* Linux
* macOS

by replacing Windows-specific functionality with platform-independent alternatives.

### 9. Privacy Improvements

Because the application uses a webcam, a future version could clearly communicate that:

* Camera processing happens locally.
* Frames are not uploaded to a server.
* No facial images need to be stored.

### 10. Modular Architecture

The current implementation is contained in one Python file.

It could be divided into modules such as:

```text
camera.py
face_detection.py
attention.py
analytics.py
health.py
automation.py
ui.py
main.py
```

This would make the project easier to maintain and extend.

---

# ⚠️ Current Limitations

* Requires a working webcam.
* Accuracy depends on camera position and lighting.
* Head position is used as an approximation for looking direction.
* Blinks may sometimes be interpreted as distraction.
* Thresholds may need adjustment for different users.
* Some automation functions are Windows-specific.
* The application currently does not store long-term session history.
* The project does not train its own machine-learning model.

---

# 🔐 Privacy

FocusPauser uses the webcam for real-time attention monitoring.

The current implementation processes the camera frames locally and does not contain functionality for uploading camera footage to an external server.

Users should still review and understand the code before deploying the application in environments where privacy requirements are important.

---

# 🎯 Project Goal

The goal of FocusPauser is to explore how **computer vision, AI-assisted perception, real-time analytics, and desktop automation** can be combined to create a practical productivity and digital-wellness application.

Instead of simply detecting a face, the project attempts to turn facial information into meaningful application behavior:

```text
Face
 ↓
Facial Landmarks
 ↓
Attention Estimation
 ↓
Distraction Detection
 ↓
Automation
 ↓
Analytics
```

---

# 👨‍💻 Author

**Your Name**

B.Tech Computer Science & Engineering

---

# 📄 License

This project can be released under the **MIT License** if you want others to freely use, modify, and distribute the code.

Add a `LICENSE` file to the repository before publishing under the MIT License.
