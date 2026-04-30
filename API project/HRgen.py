import random

def generate_max30100_data():
    return {
        "heart_rate": random.randint(60, 130),
        "spo2": random.randint(85, 100),
        "condition": random.choice(["normal", "low_spo2", "high_heart_rate"])
    }