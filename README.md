 **L.I.F.E** (**L**ocationg **I**ndividuals **F**or **E**vacuation) **Robot**
## Rescue Voice Reporter 

A **trust-aware**, **emotionally adaptive**, and **cognitively intelligent** reporting system for rescue robots built in **Webots**. This system uses realistic voice reporting (via gTTS), dynamic emotional templates, hazard warnings, and detailed structured logging for each victim encounter.

---

## 📌 Features

- ✅ **Cognitive Victim Classification** (Harmed, Unharmed, Stable)
- ✅ **Emotionally Humanized Voice Reports** using dynamic messages
- ✅ **Hazard Detection & Alerts** (Flammable Gas, Corrosive, etc.)
- ✅ **Speaker Audio Playback using GTTS + Mutagen**
- ✅ **Distance Calculation in Meters** using GPS coordinates
- ✅ **Redundancy Avoidance** via hash-based position memory
- ✅ **Structured CSV Logging** with:
  - Victim coordinates
  - Type and Priority
  - Hazard type
  - Proximity to robot (m)
  - Timestamp
  - `Area_Code`, `Urgency_Message`, and `Zone`
- ✅ **Multilingual Support** (Expandable via gTTS)
- ✅ **Emotional Message Pool** loaded from external `.json`

---

## 📁 Project Structure

```

project/
├── reports_audio/                 # Saved voice reports (MP3)
├── victim_report.csv              # Victim logs
├── phrases.json                   # Emotion templates
├── reporting_controller.py        # Controller logic
└── README.md                      # This file

````

---

## ⚙️ Requirements

Install the required Python packages:

```bash
pip install gTTS mutagen
````

---

## 🧪 Testing

The code includes a test list of victims with varying hazard types and positions. During simulation, victims are reported every 4 seconds. The robot will:

* Announce victim condition, hazard, and distance.
* Save voice report to `.mp3`.
* Log information to `victim_report.csv`.

---

## 🧠 Emotional Voice Reporting

**Emotion templates** for victim messages are stored in an external JSON file `phrases.json`. Example format:

```json
{
  "H": ["Critical harm detected.", "Severe injuries observed."],
  "U": ["Victim is okay, needs guidance."],
  "S": ["Monitoring ongoing."]
}
```

Modify or expand this file to change tone, emotion, or social phrasing.

---

## 🌍 Multilingual Support

By default, the system speaks English:

```python
language = 'en'  # To support other languages, change to 'es', 'fr', etc.
```

Available options depend on [gTTS supported languages](https://gtts.readthedocs.io/en/latest/module.html#available-languages).
Just change the `language` value to your desired language code.

---

## 🔧 Changing File Paths (IMPORTANT)

Update the following variables in your code to match your local directory structure:

```python
# Audio output folder for voice reports
audio_folder = r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/reports/reports_audio"
os.makedirs(audio_folder, exist_ok=True)

# CSV report logging
csv_path = r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/reports/victim_report.csv"

# Emotional phrases loaded from JSON
with open(r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/player_controllers/phrases.json", "r") as f:
    phrases_data = json.load(f)
```

> ⚠️ Use **raw string (`r"..."`) format** for Windows paths to avoid backslash errors.

---

## 🎯 Research Extensions

* Add tone adaptation for urgency using pitch & speed modifiers
* Enable multilingual switching during runtime
* Integrate with path-planning and hazard avoidance
* Add trust-awareness logic to prioritize known vs unknown zones

---
**Repository Purpose:** Academic Research & Rescue Robotics Simulation

**Status:** 🚧 Actively Developing


---
