# Vision_Gestures_Interface

**Vision_Gestures_Interface** is a gesture-based human-computer interface that enables **touchless desktop interaction** using real-time computer vision. Built using **MediaPipe**, **OpenCV**, and **PyAutoGUI**, the system recognizes hand gestures to control system functions such as mouse movement, clicks, scrolling, volume, and brightness — creating a seamless, contact-free user experience.

---

## ✨ Key Features

- 🖐️ **Real-Time Hand Tracking**  
  Utilizes Google MediaPipe for accurate 21-point hand landmark detection at 30+ FPS.

- 🖱️ **Mouse Control via Gestures**  
  Control the cursor, left/right click, drag, and scroll with intuitive hand gestures.

- 🔊 **System Volume & Brightness Control**  
  Adjust system volume and brightness using pinch gestures (Windows only).

- 🧠 **Gesture Recognition Engine**  
  Built on a state-based logic model with temporal smoothing to ensure stable gesture recognition.

- ⚙️ **Modular and Extensible Design**  
  Gesture-to-action mappings are modular and easy to extend or modify.

- 🌐 **Cross-Platform Capabilities**  
  Works on Windows, macOS, and Linux (note: some features may be OS-specific).

---

## 🧠 System Architecture

The following architecture outlines the internal working pipeline of the application:

Camera Feed (OpenCV)
↓
Hand Detection (MediaPipe)
↓
Gesture Classification
↓
Controller Logic (Gesture → Action)
↓
System Control via PyAutoGUI / OS APIs


Each gesture is interpreted through a combination of spatial data (e.g., landmark distance/angle) and temporal smoothing (tracking over multiple frames). Actions are triggered only when confidence and stability thresholds are met, ensuring both accuracy and usability.

---

## 🚀 Installation Instructions

Follow the steps below to set up and run the project locally.

### Prerequisites

Ensure Python 3.8+ is installed. Then install the dependencies:

```bash
# Clone the repository
git clone https://github.com/uayushdubey/Vision_Gestures_Interface.git
cd Vision_Gestures_Interface

# Install dependencies
pip install -r requirements.txt

✋ Supported Gestures
Gesture	Action
✌️ Victory	Move Cursor
👆 Index Up	Left Click
🤏 Pinch	Volume/Brightness Control
✊ Fist	Drag
🤘 Rock	Scroll
