#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import torch
import numpy as np
import pandas as pd
import csv
import os
import pickle
import mmcv
import matplotlib.pyplot as plt
from mmseg.apis import init_model, inference_model, show_result_pyplot
from config import LABELS, CONFIG_FILE, CHECKPOINT_FILE, DEVICE

# Load the model once to avoid reloading for each image
def load_segmentation_model():
    """Load the SegFormer segmentation model."""
    model = init_model(CONFIG_FILE, CHECKPOINT_FILE, device=DEVICE)
    # print(f"Model loaded on {DEVICE}")
    return model

def run_segmentation(model, img_path, save_dir):
    """Run segmentation model, save segmented image, and store results."""
    os.makedirs(save_dir, exist_ok=True)  # Ensure save directory exists

    # Run segmentation
    result = inference_model(model, img_path)

    # Define segmented image save path
    segmented_img_path = os.path.join(save_dir, os.path.basename(img_path).replace(".jpg", "_segmented.jpg"))

    # Ensure visualization backend saves correctly
    plt.figure(figsize=(8, 6))
    
    # ✅ Pass `save_dir` directly into `show_result_pyplot`
    vis_result = show_result_pyplot(model, img_path, result, show=False)

    # Convert to RGB and save the segmented image
    plt.imshow(mmcv.bgr2rgb(vis_result))
    plt.axis("off")
    plt.savefig(segmented_img_path, bbox_inches='tight', pad_inches=0)
    plt.close()

    # print(f"Segmented image saved: {segmented_img_path}")

    # Convert segmentation result to numpy
    result_mat = torch.Tensor.cpu(result.pred_sem_seg.data).squeeze().numpy()
    
    if result_mat.size == 0:
        print(f"Warning: Empty segmentation result for {img_path}")
        return

    # Extract pixel data
    height, width = result_mat.shape
    pixel_data = [(x, y, LABELS[result_mat[y, x]]) for y in range(height) for x in range(width)]

    # ✅ Return DataFrame instead of saving a pickle file
    pixel_df = pd.DataFrame(pixel_data, columns=["x", "y", "label"])
    
    # Save CSV (Optional: If you still want CSV output)
    csv_file_path = os.path.join(save_dir, os.path.basename(img_path).replace(".jpg", "_pixel_categories.csv"))
    pixel_df.to_csv(csv_file_path, index=False)
    # print(f"Segmentation results saved to {csv_file_path}")

    return pixel_df  # ✅ Directly return the DataFrame

