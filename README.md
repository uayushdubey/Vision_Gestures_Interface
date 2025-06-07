**Vision_Gestures_Interface**


Vision_Gestures_Interface is a gesture-based Human-Computer Interface that enables touchless desktop control using real-time computer vision. Built using MediaPipe, OpenCV, and PyAutoGUI, the system maps hand gestures to desktop functions including mouse movement, clicking, scrolling, volume control, and brightness adjustment. The result is an intuitive, contact-free interaction experience across various platforms.

Key Features:
1. Real-Time Hand Tracking
Leverages Google MediaPipe for efficient 21-point hand landmark detection, running at over 30 FPS for seamless performance.

2. Mouse Control via Gestures
Supports cursor movement, left/right clicking, drag, and scroll through natural hand gestures.

3. Volume and Brightness Adjustment
Enables gesture-based control for system volume and screen brightness (Windows only).

4. Robust Gesture Recognition Engine
Implements state-driven logic with temporal smoothing to ensure accurate and stable gesture interpretation.

5. Modular and Extensible Architecture
Designed for easy integration and extension of new gestures and actions.

Cross-Platform Compatibility
Works on Windows, macOS, and Linux (feature availability may vary by OS).

**System Architecture**
The system processes input in a modular pipeline, converting real-time visual data into operating system commands:

Camera Feed (OpenCV) → Hand Detection (MediaPipe) → Gesture Classification → Controller Logic (Gesture-to-Action Mapping) → System Control (via PyAutoGUI / OS APIs)

Gesture recognition is based on spatial features (such as landmark positions, distances, and angles), enhanced by temporal smoothing over multiple frames. Actions are triggered only when confidence and stability thresholds are met, ensuring both responsiveness and accuracy.

**Installation Instructions**
Prerequisites
Python 3.8 or later

pip package manager

Setup
# Clone the repository
git clone https://github.com/uayushdubey/Vision_Gestures_Interface.git
cd Vision_Gestures_Interface

# Install dependencies
pip install -r requirements.txt

# Install dependencies
pip install -r requirements.txt

Gesture Mapping Overview

Gesture	Action

Victory (✌️)	Move Cursor

Index Finger Up	Left Click

Pinch Gesture	Volume/Brightness Adjustment

Fist	Drag Operation

Rock Sign	Scroll

