import os
import numpy as np
import torch, torchvision

### Google API Key ###
API_KEY = "YOUR_API_KEY"

### Semantic segmentation ###
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CONFIG_FILE = '../YOUR/PATH/mmsegmentation/configs/segformer/segformer_mit-b5_8xb1-160k_cityscapes-1024x1024.py'
CHECKPOINT_FILE = "../YOUR/PATH/mmsegmentation/checkpoints/segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934-87a052ec.pth"
LABELS = np.array([
    "road", "sidewalk", "building", "wall", "fence", "pole", "traffic light", "traffic sign",
    "vegetation", "terrain", "sky", "person", "rider", "car", "truck", "bus", "train", "motorcycle", "bicycle"
])

### Directory for saving outputs ###
OUTPUT_DIR = "../YOUR/PATH"
os.makedirs(OUTPUT_DIR, exist_ok=True)