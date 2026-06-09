import os
import random
from gtts import gTTS
#import pygame
import time

# Initialize the audio mixer
#pygame.mixer.init()

def generate_mission_script(event_type, location, detail):
    """
    Randomizes the narrative structure so the app doesn't sound repetitive.
    """
    intros = [
        "Agent, listen closely.",
        "HQ here, mission update.",
        "Interrupting secure channel. We have a situation."
    ]
    
    if event_type == "HAZARD":
        templates = [
            f"Enemy operatives have established a blockade at {location}. {detail}. Rerouting you to a secure channel.",
            f"Satellite imagery shows severe congestion near {location}. Looks like a hostile trap. {detail}. Proceed with caution.",
            f"Obstacle detected at {location}. {detail}. Keep a low profile and find an alternate vector."
        ]
    elif event_type == "SUPPLY_DROP":
        templates = [
            f"A secure supply drop is available ahead at {location}. {detail}.",
            f"Local informants have secured rations for you at {location}. {detail}."
        ]
    
    # Combine a random intro with a random template
    full_script = f"{random.choice(intros)} {random.choice(templates)}"
    return full_script

def broadcast_audio(text, filename="comms_audio.mp3"):
    """
    Converts the text to speech and plays it through the speakers.
    """
    print(f"\n[BROADCASTING]: {text}")
    
    # 1. Generate the audio file
    tts = gTTS(text=text, lang='en', tld='co.uk') # Using the UK domain for a slightly different accent
    tts.save(filename)
    
    # 2. Play the audio file
    #pygame.mixer.music.load(filename)
    #pygame.mixer.music.play()
    
    # Keep the script running until the audio finishes
  #  while pygame.mixer.music.get_busy():
   #     time.sleep(0.1)
        
    # 3. Clean up the temporary file
 #   pygame.mixer.music.unload()
    os.remove(filename)

# --- Test Environment ---
if __name__ == "__main__":
    # Simulating a trigger from your geofence_engine.py
    hazard_location = "Interstate 75 North"
    hazard_detail = "Multiple vehicles involved in a standstill."
    
    # Generate and play the script
    script = generate_mission_script("HAZARD", hazard_location, hazard_detail)
    broadcast_audio(script)
