from controller import Robot, GPS
from gtts import gTTS
from mutagen.mp3 import MP3
import os
import csv
import time
import math
import json
import random
from datetime import datetime

# --- INITIAL SETUP ---
robot = Robot()
timestep = int(robot.getBasicTimeStep())
gps = robot.getDevice("gps")
gps.enable(timestep)
speaker = robot.getDevice("speaker")
language = 'en'  # To support other languages, change to 'es', 'fr', etc.
audio_folder = r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/reports/reports_audio"
os.makedirs(audio_folder, exist_ok=True)
csv_path = r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/reports/victim_report.csv"
reported_hashes = set()

# --- LOAD PHRASES ---
with open(r"D:\SHU\AI_RDP\erebus-25.0.0 (1)\erebus-25.0.0\player_controllers\phrases.json", "r") as f:
    phrases_data = json.load(f)

# --- CSV HEADER ---
if not os.path.exists(csv_path):
    with open(csv_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["X (m)", "Z (m)", "Type", "Priority", "Hazard", "Proximity (m)", "Timestamp", "Area_Code", "Urgency_Message", "Zone"])

print("[SYSTEM] Emotional Cognitive Reporting Module Initialized.")

# --- GET POSITION ---
def get_robot_position():
    pos = gps.getValues()
    return pos[0], pos[2]  # in meters

# --- CLASSIFY VICTIM TYPE ---
def classify_priority(type_code):
    entry = phrases_data["priorities"].get(type_code, phrases_data["priorities"]["S"])
    label = entry["label"]
    messages = entry["voice_lines"]
    urgency_msg = entry["urgency"]
    return label, random.choice(messages), urgency_msg

# --- HAZARD DESCRIPTION ---
def hazard_phrase(hazard_tag):
    return phrases_data["hazards"].get(hazard_tag, "")

# --- REPORT FUNCTION ---
def report_victim(x_cm, z_cm, type_code, hazard_tag, count):
    x_m = round(x_cm / 100.0, 2)
    z_m = round(z_cm / 100.0, 2)
    pos_hash = f"{x_m}_{z_m}_{type_code}"

    if pos_hash in reported_hashes:
        # Even for skipped, show distance in meters
        robot_x, robot_z = get_robot_position()
        proximity_m = round(math.sqrt((x_m - robot_x) ** 2 + (z_m - robot_z) ** 2), 2)
        print(f"[SKIPPED] Already reported: {type_code} at ({x_m} m, {z_m} m) | Distance: {proximity_m} m")
        return

    reported_hashes.add(pos_hash)

    # Distance calculation
    robot_x, robot_z = get_robot_position()
    proximity_m = round(math.sqrt((x_m - robot_x) ** 2 + (z_m - robot_z) ** 2), 2)

    # Priority logic
    priority, message_line, urgency = classify_priority(type_code)
    timestamp = datetime.now().strftime("%m/%d/%Y %H:%M")

    # CSV meta info
    area_code = f"PS{count}"
    zone = f"Zone-{(count % 3) + 1}"

    # Console log
    print(f"[COGNITIVE] Victim at ({x_m} m, {z_m} m) → {priority}")
    print(f"[DISTANCE] Proximity: {proximity_m} meters")
    if hazard_tag:
        print(f"[HAZARD] {hazard_tag} detected")

    # Write to CSV
    with open(csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([x_m, z_m, type_code, priority, hazard_tag or "None", proximity_m, timestamp, area_code, urgency, zone])

    # --- Construct voice message ---
    voice_lines = [
        f"{message_line} Victim located at {x_m} and {z_m} meters.",
        f"Classification: {priority}.",
        f"Distance from robot: {proximity_m} meters.",
        hazard_phrase(hazard_tag),
        urgency
    ]
    voice_message = " ".join([line for line in voice_lines if line])

    # --- Speak ---
    mp3_path = os.path.join(audio_folder, f"report_{count}.mp3")
    tts = gTTS(text=voice_message, lang=language)
    tts.save(mp3_path)
    audio = MP3(mp3_path)
    duration = audio.info.length
    speaker.playSound(speaker, speaker, mp3_path, 1.0, 1.0, 0.0, False)
    time.sleep(duration)

# --- TEST VICTIMS ---
victims = [
    (200, 400, 'H', 'Flammable Gas'),
    (100, 300, 'U', None),
    (150, 250, 'S', 'Organic Peroxide'),
    (200, 400, 'H', 'Flammable Gas'),  # Duplicate
    (300, 320, 'S', 'Corrosive'),
    (350, 320, 'U', 'Poison')
]

# --- MAIN LOOP ---
index = 0
start_time = robot.getTime()

while robot.step(timestep) != -1:
    current_time = robot.getTime() - start_time
    if index < len(victims) and current_time > (index + 1) * 4:
        x, z, type_code, hazard = victims[index]
        report_victim(x, z, type_code, hazard, index + 1)
        index += 1
