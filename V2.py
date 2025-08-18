import csv
from datetime import datetime
from gtts import gTTS
from mutagen.mp3 import MP3

from controller import Robot, Camera, GPS
import time
import math
import random
import json
import os

# Constants
HOLE_COLOR_THRESHOLD = 90       # Dark colors for holes
TRAP_COLOR_THRESHOLD = (200, 100, 50)  # RGB range for orange traps
TIME_STEP = 32
MAX_VELOCITY = 6.28
HOLE_BACK_STEPS = 52            # Steps to move back when hole detected
TRAP_BACK_DURATION = 25.0       # Seconds to move back from trap
HOLE_PAUSE_TIME = 1             # Seconds to pause after detecting hole
SHADOW_THRESHOLD = 0.15         # Seconds to confirm hole
RIGHT_MOVE_DURATION = 2.0       # Seconds to move right after hole

# Obstacle Avoidance Constants
OBSTACLE_THRESHOLD = 80         # Distance to consider obstacle
TURN_DURATION = 0.5             # Seconds to turn when avoiding
BACKUP_DURATION = 0.5           # Seconds to back up
TURN_SPEED = 5.0                # Turning speed
BACKUP_SPEED = -4.0             # Back up speed

# Target Navigation Constants
TARGET_POSITIONS = [
    (-0.49, -0.28),
    (-0.42, -0.25),
    (-0.24,  0.13),
    ( 0.11,  0.16)
]

# Wall Following Constants
WALL_B_MIN = 120                # Minimum blue value for wall
WALL_R_MAX = 80                 # Maximum red value
WALL_G_MAX = 140                # Maximum green value
VICTIM_THRESHOLD = 200          # Minimum RGB values for white victims
WALL_FOLLOW_DISTANCE = 60       # Ideal distance from wall
VICTIM_PAUSE_TIME = 3.0         # Time to pause when victim found
WALL_LOST_TIMEOUT = 2.0         # Time before considering wall lost

# Target Navigation Constants
#TARGET_X = -0.48
#TARGET_Z = 0.25
POSITION_TOLERANCE = 0.05       # How close we need to get to target
NAVIGATION_SPEED = 5.0          # Base speed for navigation
DIRECTIONS = {
    'forward': (NAVIGATION_SPEED, NAVIGATION_SPEED),
    'left': (NAVIGATION_SPEED*0.3, NAVIGATION_SPEED),
    'right': (NAVIGATION_SPEED, NAVIGATION_SPEED*0.3),
    'back': (-NAVIGATION_SPEED, -NAVIGATION_SPEED)
}

# Enhanced Stuck Prevention Constants
STUCK_THRESHOLD = 0.01          # Minimum position change
STUCK_TIME = 2.0                # Seconds before considering stuck
MAX_STUCK_ATTEMPTS = 10         # Max recovery attempts
POSITION_HISTORY_SIZE = 10      # Number of positions to track
RECOVERY_MOVE_STEPS = 50        # Steps for recovery moves

# Path Following Constants
PATH_FILENAME = "robot_path.json"

class ErebusInference:
    def __init__(self, robot):
        self.robot = robot
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Initialize motors
        self.left_motor = self.robot.getDevice("wheel1 motor")
        self.right_motor = self.robot.getDevice("wheel2 motor")
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        
        # Initialize path data with default empty path
        self.path_data = {'path': []}
        self.path_index = 0
        self.current_action = None
        self.action_steps_remaining = 0
        
        # Get the absolute path to the controller directory
        controller_dir = os.path.dirname(os.path.abspath(__file__))
        self.path_file = os.path.join(controller_dir, PATH_FILENAME)

        # Try to load path, create new file if not exists
        try:
            if os.path.exists(self.path_file):
                with open(self.path_file, 'r') as f:
                    self.path_data = json.load(f)
                print(f"Successfully loaded path from {self.path_file}")
            else:
                # Create new empty path file
                with open(self.path_file, 'w') as f:
                    json.dump(self.path_data, f)
                print(f"Created new path file at {self.path_file}")
        except Exception as e:
            print(f"Error handling path file: {e}")
            # Continue with empty path data


        # ------SEEMA------

        self.speaker = self.robot.getDevice("speaker")
        self.language = 'en'
        self.report_audio_end_time = 0 
        self.audio_folder = r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/reports/reports_audio"
        os.makedirs(self.audio_folder, exist_ok=True)
        # Clean the report audio folder at startup
        for filename in os.listdir(self.audio_folder):
            file_path = os.path.join(self.audio_folder, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
        self.csv_path = r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/reports/victim_report.csv"
        self.reported_hashes = set()
        with open(r"D:/SHU/AI_RDP/erebus-25.0.0 (1)/erebus-25.0.0/reports/phrases.json", "r") as f:
            self.phrases_data = json.load(f)
        # if not os.path.exists(self.csv_path):
        with open(self.csv_path, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["X (m)", "Z (m)", "Type", "Priority", "Hazard", "Proximity (m)", "Timestamp", "Area_Code", "Urgency_Message", "Zone"])

    def get_position(self):
        gps = self.robot.getDevice("gps")
        return gps.getValues()[0], gps.getValues()[2]
    
    def run_path_following(self):
        print("Starting path following mode")
        self.path_following = True
        path_completed = self.path_follower.run()
        self.path_following = False
        return path_completed

    def report_victim(self, x_cm, z_cm, type_code, hazard_tag, urgency_msg,voice_message, victim_count):
        print(f"---"*20)
        print('Victim_Count:', victim_count)
        # with open(self.csv_path, mode='a', newline='') as file:
        #     writer = csv.writer(file)
        #     writer.writerow([
        #         x_m, z_m, type_code, priority, hazard_tag or "None", proximity_m, timestamp, area_code, urgency_msg, zone
        #     ])
        x_m = round(x_cm / 100.0, 2)
        z_m = round(z_cm / 100.0, 2)
        pos_hash = f"{x_m}_{z_m}_{type_code}"

        if pos_hash in self.reported_hashes:
            robot_x, robot_z = self.get_position()
            proximity_m = round(math.sqrt((x_m - robot_x) ** 2 + (z_m - robot_z) ** 2), 2)
            print(f"[SKIPPED] Already reported: {type_code} at ({x_m} m, {z_m} m) | Distance: {proximity_m} m")
            return

        self.reported_hashes.add(pos_hash)
        robot_x, robot_z = self.get_position()
        proximity_m = round(math.sqrt((x_m - robot_x) ** 2 + (z_m - robot_z) ** 2), 2)

        def classify_priority(type_code):
            entry = self.phrases_data["priorities"].get(type_code, self.phrases_data["priorities"]["S"])
            label = entry["label"]
            messages = entry["voice_lines"]
            urgency_msg = entry["urgency"]
            return label, random.choice(messages), urgency_msg

        def hazard_phrase(hazard_tag):
            return self.phrases_data["hazards"].get(hazard_tag, "")

        priority, message_line, urgency_msg = classify_priority(type_code)
        timestamp = datetime.now().strftime("%m/%d/%Y %H:%M")
        area_code = f"Area_Code{victim_count}"
        zone = f"Zone-{(victim_count % 3) + 1}"

        print(f"[COGNITIVE] Victim at ({x_m} m, {z_m} m) → {priority}")
        print(f"[DISTANCE] Proximity: {proximity_m} meters")
        if hazard_tag:
            print(f"[HAZARD] {hazard_tag} detected")

        with open(self.csv_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([x_m, z_m, type_code, priority, hazard_tag or "None", proximity_m, timestamp, area_code, urgency_msg, zone])

        voice_lines = [
            f"{message_line} Victim located at {x_m} and {z_m} meters.",
            f"Classification: {priority}.",
            f"Distance from robot: {proximity_m} meters.",
            hazard_phrase(hazard_tag),
            urgency_msg
        ]
        voice_message = " ".join([line for line in voice_lines if line])

        mp3_path = os.path.join(self.audio_folder, f"report_{victim_count}.mp3")
        tts = gTTS(text=voice_message, lang=self.language)
        tts.save(mp3_path)
        audio = MP3(mp3_path)
        duration = audio.info.length
        self.speaker.playSound(self.speaker, self.speaker, mp3_path, 1.0, 1.0, 0.0, False)
        self.report_audio_end_time = self.robot.getTime() + duration
        # time.sleep(duration)

        # ----SHEEMA

    def save_path(self):
        """Save the current path data to the JSON file"""
        try:
            with open(self.path_file, 'w') as f:
                json.dump(self.path_data, f, indent=2)
            print(f"Path successfully saved to {self.path_file}")
            return True
        except Exception as e:
            print(f"Error saving path: {e}")
            return False

    def add_path_action(self, action_type, steps):
        """Add a new action to the path"""
        self.path_data['path'].append({
            'type': action_type,
            'steps': steps
        })
        return self.save_path()

    def execute_movement(self, action_type):
        """Execute movement based on action type"""
        if action_type == 'F':  # Forward
            self.left_motor.setVelocity(MAX_VELOCITY * 0.7)
            self.right_motor.setVelocity(MAX_VELOCITY * 0.7)
        elif action_type == 'B':  # Backward
            self.left_motor.setVelocity(-MAX_VELOCITY * 0.5)
            self.right_motor.setVelocity(-MAX_VELOCITY * 0.5)
        elif action_type == 'L':  # Left turn
            self.left_motor.setVelocity(MAX_VELOCITY * 0.3)
            self.right_motor.setVelocity(MAX_VELOCITY)
        elif action_type == 'R':  # Right turn
            self.left_motor.setVelocity(MAX_VELOCITY)
            self.right_motor.setVelocity(MAX_VELOCITY * 0.3)

    def run(self):
        # last_report_time = self.robot.getTime()
        # victim_count = 1
        # while self.robot.step(self.timestep) != -1 and not self.reached_target:
        # -----SEEMA----
        last_report_time = self.robot.getTime()
        victim_count = 1
        victim_types = ['U', 'S', 'H']
        while self.robot.step(self.timestep) != -1 and not self.reached_target:
            current_time = self.robot.getTime()

            if current_time - last_report_time >20:
                x, z = self.get_position()
                type_code = victim_types[(victim_count - 1) % len(victim_types)]
                hazard_tag = None
                urgency_msg = None
                self.report_victim(x * 100, z * 100, type_code, hazard_tag, urgency_msg, victim_count)
                victim_count += 1
                last_report_time = current_time
            #  -------SHEEMA------
            if self.path_index >= len(self.path_data['path']):
                print("Path completed!")
                self.left_motor.setVelocity(0)
                self.right_motor.setVelocity(0)
                return True
            
            # Get current action
            if self.current_action is None:
                self.current_action = self.path_data['path'][self.path_index]
                self.execute_movement(self.current_action['type'])
                self.action_steps_remaining = self.current_action['steps']
                print(f"Executing {self.current_action['type']} for {self.current_action['steps']} steps")
            
            # Execute current step
            self.robot.step(self.timestep)
            self.action_steps_remaining -= 1
            
            # Check if action completed
            if self.action_steps_remaining <= 0:
                self.current_action = None
                self.path_index += 1
        return False
    
TIME_STEP = 32
FORWARD_SPEED = 5.0
TURN_SPEED = 3.0

class PathFollower:
    def __init__(self):
        self.path = []


    def add_path_action(self, action_type, steps):
        self.path.append({"type": action_type, "steps": steps})

    def save_path(self, file_path='robot_path.json'):
        with open(file_path, 'w') as f:
            json.dump(self.path, f, indent=2)

class ErebusController:
    def __init__(self):
        self.robot = Robot()
        self.timestep = int(self.robot.getBasicTimeStep())
        
        # Detection flags
        self.hole_detection_start = -1
        self.in_hole_sequence = False
        self.in_trap_sequence = False
        self.obstacle_detected = False
        self.turn_start_time = 0
        self.current_target_index = 0
        self.total_targets = len(TARGET_POSITIONS)

        # Wall following parameters
        self.wall_following = False
        self.wall_side = "right"
        self.last_wall_time = 0
        self.victim_reported = False
        
        # Target navigation parameters
        self.reached_target = False
        self.last_distance = float('inf')
        
        # Enhanced stuck prevention
        self.position_history = []
        self.stuck_attempts = 0
        self.last_recovery_time = 0
        
        # Path following
        self.path_following = False
        self.path_follower = ErebusInference(self.robot)
        
        # Initialize devices
        self.left_motor = self.robot.getDevice("wheel1 motor")
        self.right_motor = self.robot.getDevice("wheel2 motor")
        self.left_motor.setPosition(float('inf'))
        self.right_motor.setPosition(float('inf'))
        
        self.color_sensor = self.robot.getDevice("colour_sensor")
        self.color_sensor.enable(self.timestep)
        
        self.camera = self.robot.getDevice("camera_centre")
        self.camera.enable(TIME_STEP)
        self.camera_width = self.camera.getWidth()
        self.camera_height = self.camera.getHeight()
        
        self.gps = self.robot.getDevice("gps")
        self.gps.enable(TIME_STEP)
        
        self.distance_sensors = []
        for i in range(8):
            sensor = self.robot.getDevice(f"ps{i}")
            sensor.enable(TIME_STEP)
            self.distance_sensors.append(sensor)
        
        self.front_sensors = [self.distance_sensors[0], self.distance_sensors[7]]
        self.right_sensors = [self.distance_sensors[1], self.distance_sensors[2]]
        self.left_sensors = [self.distance_sensors[5], self.distance_sensors[6]]

    def get_color_values(self):
        image = self.color_sensor.getImage()
        return (self.color_sensor.imageGetRed(image, 1, 0, 0),
                self.color_sensor.imageGetGreen(image, 1, 0, 0),
                self.color_sensor.imageGetBlue(image, 1, 0, 0)) if image else (0, 0, 0)

    def get_camera_color_values(self):
        image = self.camera.getImage()
        if image:
            x, y = self.camera_width//2, self.camera_height//2
            return (Camera.imageGetRed(image, self.camera_width, x, y),
                    Camera.imageGetGreen(image, self.camera_width, x, y),
                    Camera.imageGetBlue(image, self.camera_width, x, y))
        return (0, 0, 0)

    def get_position(self):
        return self.gps.getValues()[0], self.gps.getValues()[2]

    def get_sensor_readings(self):
        return {
            'front_left': self.front_sensors[0].getValue(),
            'front_right': self.front_sensors[1].getValue(),
            'left': min(s.getValue() for s in self.left_sensors),
            'right': min(s.getValue() for s in self.right_sensors)
        }

    def distance_to_target(self, x, z):
        target_x, target_z = TARGET_POSITIONS[self.current_target_index]
        return math.sqrt((x - target_x)**2 + (z - target_z)**2)
    def detect_obstacle(self):
        readings = self.get_sensor_readings()
        return readings['front_left'] > OBSTACLE_THRESHOLD or readings['front_right'] > OBSTACLE_THRESHOLD

    def evaluate_move(self, direction):
        x, z = self.get_position()
        self.move(*DIRECTIONS[direction], steps=1)
        new_x, new_z = self.get_position()
        self.move(*DIRECTIONS['back'], steps=1)
        return self.distance_to_target(new_x, new_z)

    def is_robot_stuck(self):
        if len(self.position_history) < POSITION_HISTORY_SIZE:
            return False
            
        total_movement = 0
        for i in range(1, len(self.position_history)):
            dx = self.position_history[i][0] - self.position_history[i-1][0]
            dz = self.position_history[i][1] - self.position_history[i-1][1]
            total_movement += math.sqrt(dx**2 + dz**2)
        
        avg_movement = total_movement / (len(self.position_history)-1)
        return avg_movement < STUCK_THRESHOLD and \
               (self.robot.getTime() - self.last_recovery_time) > STUCK_TIME

    def execute_recovery_sequence(self):
        self.stuck_attempts += 1
        current_time = self.robot.getTime()
        
        # Try different strategies based on attempt count
        if self.stuck_attempts % 4 == 0:
            # Full rotation + forward
            print("Recovery: Full rotation + forward")
            self.move(MAX_VELOCITY, -MAX_VELOCITY, steps=40)
            self.move(*DIRECTIONS['forward'], steps=RECOVERY_MOVE_STEPS)
        elif self.stuck_attempts % 3 == 0:
            # Strong left turn
            print("Recovery: Strong left turn")
            self.move(MAX_VELOCITY*0.2, MAX_VELOCITY, steps=RECOVERY_MOVE_STEPS)
        elif self.stuck_attempts % 2 == 0:
            # Strong right turn
            print("Recovery: Strong right turn")
            self.move(MAX_VELOCITY, MAX_VELOCITY*0.2, steps=RECOVERY_MOVE_STEPS)
        else:
            # Long backward + slight turn
            print("Recovery: Long backward + turn")
            self.move(*DIRECTIONS['back'], steps=RECOVERY_MOVE_STEPS)
            self.move(MAX_VELOCITY, MAX_VELOCITY*0.7, steps=20)
        
        # Check if recovery worked
        new_pos = self.get_position()
        movement = math.sqrt((new_pos[0]-self.position_history[-1][0])**2 + 
                            (new_pos[1]-self.position_history[-1][1])**2)
        
        if movement > STUCK_THRESHOLD*5:
            print("Recovery successful!")
            self.position_history = []
            self.last_recovery_time = current_time
            return True
        
        if self.stuck_attempts >= MAX_STUCK_ATTEMPTS:
            print("Max recovery attempts reached - hard reset")
            self.move(*DIRECTIONS['back'], steps=100)
            self.move(MAX_VELOCITY, -MAX_VELOCITY, steps=60)
            self.stuck_attempts = 0
            self.position_history = []
            return False
            
        return False

    def detect_hole(self):
        if self.in_hole_sequence or self.in_trap_sequence:
            return False
            
        r, g, b = self.get_color_values()
        current_time = self.robot.getTime()
        
        if all(c < HOLE_COLOR_THRESHOLD for c in (r, g, b)):
            if self.hole_detection_start < 0:
                self.hole_detection_start = current_time
            elif current_time - self.hole_detection_start > SHADOW_THRESHOLD:
                return True
        else:
            self.hole_detection_start = -1
        return False

    def detect_trap(self):
        if self.in_hole_sequence or self.in_trap_sequence:
            return False
            
        r, g, b = self.get_color_values()
        return (r > TRAP_COLOR_THRESHOLD[0] and 
                g > TRAP_COLOR_THRESHOLD[1] and 
                b < TRAP_COLOR_THRESHOLD[2])

    def detect_wall(self):
        r, g, b = self.get_camera_color_values()
        return (b > WALL_B_MIN and 
                r < WALL_R_MAX and 
                g < WALL_G_MAX)

    def detect_victim(self):
        r, g, b = self.get_camera_color_values()
        return (r > VICTIM_THRESHOLD and 
                g > VICTIM_THRESHOLD and 
                b > VICTIM_THRESHOLD)

    def execute_hole_avoidance(self):
        print("HOLE DETECTED! Starting avoidance...")
        self.in_hole_sequence = True
        
        # 1. Immediate stop
        self.stop()
        
        # 2. Pause for specified time
        start_pause = self.robot.getTime()
        while self.robot.getTime() - start_pause < HOLE_PAUSE_TIME:
            self.robot.step(TIME_STEP)
        
        # 3. Move back
        steps_completed = 0
        self.move(-0.5 * MAX_VELOCITY, -0.5 * MAX_VELOCITY)
        while steps_completed < HOLE_BACK_STEPS:
            self.robot.step(TIME_STEP)
            steps_completed += 1
        
        # 4. Move right
        self.move(0.7 * MAX_VELOCITY, 0.3 * MAX_VELOCITY)
        move_start = self.robot.getTime()
        while self.robot.getTime() - move_start < RIGHT_MOVE_DURATION:
            self.robot.step(TIME_STEP)
        
        # Complete
        self.stop()
        self.in_hole_sequence = False
        self.hole_detection_start = -1
        print("Hole avoidance complete")

    def execute_trap_avoidance(self):
        print("TRAP DETECTED! Quick escape!")
        self.in_trap_sequence = True
        
        # Asymmetric backward movement
        self.move(-0.3 * MAX_VELOCITY, -0.9 * MAX_VELOCITY)
        
        # Continue for duration
        start_time = self.robot.getTime()
        while self.robot.getTime() - start_time < TRAP_BACK_DURATION:
            self.robot.step(TIME_STEP)
        
        # Complete
        self.stop()
        self.in_trap_sequence = False
        print("Trap escape complete")

    def follow_wall(self):
        if not self.detect_wall():
            if self.wall_following and (self.robot.getTime() - self.last_wall_time > WALL_LOST_TIMEOUT):
                self.wall_following = False
                print("WALL LOST - RESUMING NORMAL MOVEMENT")
            return False
        
        if not self.wall_following:
            self.wall_following = True
            print("WALL DETECTED - STARTING WALL FOLLOWING")
        
        self.last_wall_time = self.robot.getTime()
        sensors = self.get_sensor_readings()
        
        # Check for victims
        # if self.detect_victim() and not self.victim_reported:
        #     print("VICTIM DETECTED! Reporting...")
        #     self.stop()
        #     start_pause = self.robot.getTime()
        #     while self.robot.getTime() - start_pause < VICTIM_PAUSE_TIME:
        #         self.robot.step(TIME_STEP)
        #     self.victim_reported = True
        #     print("VICTIM REPORTED - CONTINUING")
        #     return True

        # -------SEEMA--------
        if self.detect_victim() and not self.victim_reported:
            print("VICTIM DETECTED! Reporting...")
            self.stop()
            x, z = self.get_position()
            # Assuming type_code and hazard_tag are determined based on context
            type_code = 'U'  # Unknown, or set based on context
            hazard_tag = 'Poission'
            count = len(self.reported_hashes) + 1
            self.report_victim(x * 100, z * 100, type_code, hazard_tag, count)
            start_pause = self.robot.getTime()
            while self.robot.getTime() - start_pause < VICTIM_PAUSE_TIME:
                self.robot.step(TIME_STEP)
            self.victim_reported = True
            print("VICTIM REPORTED - CONTINUING")
            return True
        
        self.victim_reported = False
        
        # Wall following logic (right wall)
        if self.wall_side == "right":
            if sensors['right'] < WALL_FOLLOW_DISTANCE:
                self.move(MAX_VELOCITY * 0.3, MAX_VELOCITY)  # Turn left
            else:
                self.move(MAX_VELOCITY, MAX_VELOCITY * 0.8)  # Parallel
        else:  # Left wall
            if sensors['left'] < WALL_FOLLOW_DISTANCE:
                self.move(MAX_VELOCITY, MAX_VELOCITY * 0.3)  # Turn right
            else:
                self.move(MAX_VELOCITY * 0.8, MAX_VELOCITY)  # Parallel
        
        return True
    
        # ------SHEEMA------

    def move(self, left_speed, right_speed, steps=1):
        self.left_motor.setVelocity(left_speed)
        self.right_motor.setVelocity(right_speed)
        for _ in range(steps):
            self.robot.step(TIME_STEP)

    def stop(self):
        self.move(0, 0)

    def navigate_to_target(self):
        current_pos = self.get_position()
        self.position_history.append(current_pos)
        if len(self.position_history) > POSITION_HISTORY_SIZE:
            self.position_history.pop(0)
        
        current_dist = self.distance_to_target(*current_pos)
        if current_dist < POSITION_TOLERANCE:
            print(f"Target {self.current_target_index + 1} reached at X:{current_pos[0]:.2f} Z:{current_pos[1]:.2f}")
            self.stop()
            
            self.current_target_index += 1
            if self.current_target_index >= self.total_targets:
                print("All targets reached!")
                self.reached_target = True
            else:
                print(f"Moving to next target: {TARGET_POSITIONS[self.current_target_index]}")
                self.last_distance = float('inf')
                self.position_history = []
            
            return True
        
        if self.is_robot_stuck():
            print("Robot stuck - initiating recovery sequence")
            if self.execute_recovery_sequence():
                self.last_distance = float('inf')
                return False
                
        # Normal navigation
        best_direction = None
        best_distance = float('inf')
        
        for direction in DIRECTIONS:
            test_distance = self.evaluate_move(direction)
            if test_distance < best_distance:
                best_distance = test_distance
                best_direction = direction
        
        if best_direction:
            self.move(*DIRECTIONS[best_direction])
            print(f"Moving {best_direction} (Distance: {best_distance:.2f})")
        
        return False

    def run_path_following(self):
        """Execute the path following behavior"""
        print("Starting path following mode")
        self.path_following = True
        path_completed = self.path_follower.run()
        self.path_following = False
        return path_completed

    def run(self):
        # First check if we have a path to follow
        if len(self.path_follower.path_data['path']) > 0:
            print(f"Found {len(self.path_follower.path_data['path'])} path steps - attempting to follow...")
            path_success = self.run_path_following()
            
            if path_success:
                print("Successfully completed path following")
                return
            else:
                print("Path following incomplete, falling back to normal navigation")
        else:
            print("No path steps available, using normal navigation")
            print("You can record a path by calling add_path_action()")

        # -------SEEMA-------
        # Timed victim reporting setup
        last_report_time = self.robot.getTime()
        victim_count = 1
        victim_types = ['U', 'S', 'H']
        hazard_tag_list = ['Flammable Gas', 'Poission', 'Organic Peroxide', 'Corrosive']
        
        urgency_msg = None
        count = len(self.path_follower.reported_hashes) + 1
        # urgency_msg = self.path_follower.phrases_data["priorities"].get(type_code, {}).get("urgency", "No urgency message")

        # Fall back to normal navigation
        while self.robot.step(TIME_STEP) != -1 and not self.reached_target:
            # ------SEEMA---------
            current_time = self.robot.getTime()
            # Timed victim reporting
            if current_time - last_report_time > 20:
                if current_time >= self.path_follower.report_audio_end_time:
                    print(f"Reporting victim at time {current_time}")
                    x, z = self.get_position()
                    type_code = victim_types[(victim_count - 1) % len(victim_types)]
                    hazard_tag = random.choice(hazard_tag_list)
                    
                
                    self.path_follower.report_victim(x * 100, z * 100, type_code, hazard_tag, urgency_msg, None, victim_count)
                    print(f"[DEBUG] Timed victim report triggered at {current_time}")
                    victim_count += 1
                    last_report_time = current_time
                # else:
                #     print("[DEBUG] Skipping report: previous audio still playing")

            # --------SHEEMA----------
            # Priority 1: Trap detection
            if not self.in_trap_sequence and self.detect_trap():
                self.execute_trap_avoidance()
                continue
                
            # Priority 2: Hole detection
            if not self.in_hole_sequence and self.detect_hole():
                self.execute_hole_avoidance()
                continue
                
            # Priority 3: Wall following
            if self.detect_wall():
                self.follow_wall()
                continue
                
            # Normal operation - target navigation
            x_pos, z_pos = self.get_position()
            self.navigate_to_target()
            
            # Debug output
            floor_r, floor_g, floor_b = self.get_color_values()
            cam_r, cam_g, cam_b = self.get_camera_color_values()
            current_dist = self.distance_to_target(x_pos, z_pos)
            print(f"Pos: X:{x_pos:5.2f} Z:{z_pos:5.2f} | "
                  f"Dist: {current_dist:.2f} | "
                  f"Floor - R:{floor_r:3d} G:{floor_g:3d} B:{floor_b:3d} | "
                  f"Camera - R:{cam_r:3d} G:{cam_g:3d} B:{cam_b:3d}")

# Create and run controller
controller = ErebusController()
controller.run()