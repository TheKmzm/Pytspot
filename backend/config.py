import json
import os

SPEAKER_NAME = "Redify"
VERSION_FILE = "data/app_version.json"


def increment_version():
    def congrats(v):
        return " New Version" if abs((v / 0.1) - (v // 0.1)) < 1e-9 else ""
    
    # Load current version or start at 0.0
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            data = json.load(f)
        version = data.get("version", 0.0)
    else:
        version = 0.0

    # Increment version safely
    version = round(version + 0.01, 2)

    # Save updated version
    with open(VERSION_FILE, "w") as f:
        json.dump({"version": version}, f)
    
    return f"{version}{congrats(version)}"


        
if __name__ == "__main__":
    print(increment_version())




