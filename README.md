 **L.I.F.E** (**L**ocationg **I**ndividuals **F**or **E**vacuation) **Robot**
# Rescue Robot Project – Technical Instructions

## Prerequisites
1. **Install Webots** (version: R2023b).
2. **Download the Erebus Rescue Simulation environment** from the official source.
   [erebus-25.0.1.zip](https://github.com/user-attachments/files/21799569/erebus-25.0.1.1.zip)

4. **Ensure the Erebus environment is extracted and ready** on your local machine.

---

## Folder Setup
1. Clone or download this repository.
2. Rename the repository folder to **`reports`**.
3. Move the renamed **`reports`** folder into the main **Erebus Rescue Simulation** project directory so it sits alongside `docs`, `game`, and `player_controllers`.

**Expected final directory structure:**

```

Erebus Rescue Simulation/
│
├── docs/
├── game/
├── player_controllers/
├── L.I.F.E-Robot/   ← Our Project Code
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
└── README.md
```
---

## Running the Project
1. Launch **Webots**.
2. Open the world file:

```
/game/worlds/world1.wbt
````
3. In the **Competition Controller** panel on the left:
- Click **LOAD**.
- Select the main controller file from:

 ```
/L.I.F.E-Robot/V2.py
  ```
4. Wait until the **LOAD** button changes to **orange**.
5. Click **Start** to begin the simulation.

---

## Simulation Controls
- **Pause** → Temporarily stop the robot.
- **Restart** → Respawn the robot at the last checkpoint.
- **Reset** → Restart the entire simulation and reload code.
- **Settings** → Toggle debugging options.

---

## Manual Robot Movement (Optional)
- Click the robot in the simulation window → red, blue, and green arrows appear.
- Drag to reposition the robot (only after starting the simulation).

---

## Common Issues & Fixes
**Competition Supervisor Not Visible:**
1. Go to **Tools → Scene Tree**.
2. Expand and locate **`DEF MAINSUPERVISOR Robot`**.
3. Right-click → **Show Robot Window**.


**Status:** 🚧 Actively Developing


---
