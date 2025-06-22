import requests
import os

api_url = "http://10.29.25.245:8000/predict"
samples_dir = "/Users/suhail/Library/CloudStorage/SynologyDrive-dataLib/threeD/courses/05_Machine_Learning_in_VFX/ml4vfxTrees/fashionMNIST/data/samples"

for fname in os.listdir(samples_dir):
    if fname.endswith(".png"):
        with open(os.path.join(samples_dir, fname), "rb") as f:
            files = {"file": (fname, f, "image/png")}
            response = requests.post(api_url, files=files)
            print(f"{fname}: {response.json()}")
