#!/usr/bin/env python3
"""Compute vanishing points using coarse-to-fine method on the evaluation dataset.
Usage:
    detect_new_1020.py [options] <yaml-config> <checkpoint>
    detect_new_1020.py ( -h | --help )

Arguments:
   <yaml-config>                 Path to the yaml hyper-parameter file
   <checkpoint>                  Path to the checkpoint

Options:
   -h --help                     Show this screen
   -d --devices <devices>        Comma separated GPU devices [default: 0]
   -o --output <output>          Path to the output AA curve [default: error.npz]
   --dump <output-dir>           Optionally, save the vanishing points to npz format.
                                 The coordinate of VPs is in the camera space.
   --noimshow                    Do not show result
   --range=<start:end>         Index range to process [default: 0:999999]
"""

import os
import sys
import math
import shlex
import pprint
import random
import os.path as osp
import threading
import subprocess

import numpy as np
import torch
import matplotlib as mpl
import skimage.io
import numpy.linalg as LA
import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d
from tqdm import tqdm
from docopt import docopt

import neurvps
import neurvps.models.vanishing_net as vn
from neurvps.config import C, M
from neurvps.datasets import Tmm17Dataset, ScanNetDataset, WireframeDataset, ATLIMG # Also import my custom dataset class
from torch.utils.data._utils.collate import default_collate
from skimage import io # add this

def AA(x, y, threshold):
    index = np.searchsorted(x, threshold)
    x = np.concatenate([x[:index], [threshold]])
    y = np.concatenate([y[:index], [threshold]])
    return ((x[1:] - x[:-1]) * y[:-1]).sum() / threshold

def main():
    args = docopt(__doc__)
    print("Parsed arguments:", args)  # For debugging; remove later.
    start_idx, end_idx = map(int, args["--range"].split(":"))
    config_file = args["<yaml-config>"]
    C.update(C.from_yaml(filename=config_file))
    C.model.im2col_step = 32  # override im2col_step for evaluation
    M.update(C.model)
    pprint.pprint(C, indent=4)

    random.seed(0)
    np.random.seed(0)
    torch.manual_seed(0)

    device_name = "cpu"
    os.environ["CUDA_VISIBLE_DEVICES"] = args["--devices"]
    if torch.cuda.is_available():
        device_name = "cuda"
        torch.backends.cudnn.deterministic = True
        torch.cuda.manual_seed(0)
        print("Let's use", torch.cuda.device_count(), "GPU(s)!")
    else:
        print("CUDA is not available")
    device = torch.device(device_name)

    if M.backbone == "stacked_hourglass":
        model = neurvps.models.hg(
            planes=64, depth=M.depth, num_stacks=M.num_stacks, num_blocks=M.num_blocks
        )
    else:
        raise NotImplementedError

    checkpoint = torch.load(args["<checkpoint>"])
    model = neurvps.models.VanishingNet(
        model, C.model.output_stride, C.model.upsample_scale
    )
    model = model.to(device)
    model = torch.nn.DataParallel(
        model, device_ids=list(range(args["--devices"].count(",") + 1))
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    if C.io.dataset.upper() == "WIREFRAME":
        Dataset = WireframeDataset
    elif C.io.dataset.upper() == "TMM17":
        Dataset = Tmm17Dataset
    elif C.io.dataset.upper() == "SCANNET":
        Dataset = ScanNetDataset
    elif C.io.dataset.upper() == "ATLIMG":
        Dataset = ATLIMG
    else:
        raise NotImplementedError

    dataset = Dataset(C.io.datadir, split="valid")
    dataset = torch.utils.data.Subset(dataset, range(start_idx, min(end_idx, len(dataset))))
    
    loader = torch.utils.data.DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        num_workers=C.io.num_workers if os.name != "nt" else 0,
        pin_memory=True,
        collate_fn=collate_fn_filter  # Use the custom collate function
    )

    if args["--dump"] is not None:
        os.makedirs(args["--dump"], exist_ok=True)

    err = []
    n = C.io.num_vpts
    for batch_idx, sample in enumerate(tqdm(loader)):
        if not sample: 
            print(f"Skipping empty batch at index {batch_idx}")
            continue

        image, target = sample
        image = image.to(device)
        input_dict = {"image": image, "test": True}
        ### save it as img_path
        img_path = target["img_path"][0]
        print(img_path)
        print(image.shape, image.min().item(), image.max().item(), image.mean().item())
        ### 
        #vpts_gt = target["vpts"][0]
        #vpts_gt *= (vpts_gt[:, 2:3] > 0).float() * 2 - 1
        vpts = sample_sphere(np.array([0, 0, 1]), np.pi / 2, 64)
        input_dict["vpts"] = vpts
        with torch.no_grad():
            score = model(input_dict)[:, -1].cpu().numpy()
        index = np.argsort(-score)
        candidate = [index[0]]
        for i in index[1:]:
            if len(candidate) == n:
                break
            dst = np.min(np.arccos(np.abs(vpts[candidate] @ vpts[i])))
            if dst < np.pi / n:
                continue
            candidate.append(i)
        vpts_pd = vpts[candidate]

        for res in range(1, len(M.multires)):
            vpts = [sample_sphere(vpts_pd[vp], M.multires[-res], 64) for vp in range(n)]
            input_dict["vpts"] = np.vstack(vpts)
            with torch.no_grad():
                score = model(input_dict)[:, -res - 1].cpu().numpy().reshape(n, -1)
                #print(score)
            for i, s in enumerate(score):
                vpts_pd[i] = vpts[i][np.argmax(s)]
        #print(vpts_pd)

        # After the refinement loop, vpts_pd has shape (n, 3)
        # Feed the refined candidates back to the model for a final scoring:
        input_dict["vpts"] = vpts_pd
        with torch.no_grad():
            final_scores = model(input_dict)[:, -1].cpu().numpy()
        # Select the candidate with the highest final score:
        best_index = np.argmax(final_scores)
        best_vp = vpts_pd[best_index]
        print(best_vp)

        # save the visualized VP on each image as .jpg
        best_vp = best_vp[:2]
        print(best_vp)
        best_vp = [
            (best_vp[0] + 1) * 256,
            (1 - best_vp[1]) * 256]
        best_vp = [
            best_vp[0] / 512 * 640 ,
            best_vp[1] / 512 * 640]
        print(best_vp)

        # save the detected VP as .npz        
        if args["--dump"]:
            np.savez(
                osp.join(args["--dump"], f"{img_path.split('/')[-1].split('.j')[0]}.npz"),
                best_vp=best_vp)
            
        #img  = skimage.io.imread(img_path)
        #plt.figure() # important to create a new figure to avoid accumulation of plt plot elements
        #plt.imshow(img)
        #plt.scatter(best_vp[0], best_vp[1], color='red')
        #plt.savefig(osp.join(args["--dump"], f"{img_path.split('/')[-1].split('.j')[0]}.png"))
        #plt.close()


def collate_fn_filter(batch):
    # Remove any samples that are None
    batch = [item for item in batch if item is not None]
    # If no valid samples remain, return an empty list (or handle as needed)
    if len(batch) == 0:
        return []
    return default_collate(batch)


def sample_sphere(v, alpha, num_pts):
    v1 = orth(v)
    v2 = np.cross(v, v1)
    v, v1, v2 = v[:, None], v1[:, None], v2[:, None]
    indices = np.linspace(1, num_pts, num_pts)
    phi = np.arccos(1 + (math.cos(alpha) - 1) * indices / num_pts)
    theta = np.pi * (1 + 5 ** 0.5) * indices
    r = np.sin(phi)
    return (v * np.cos(phi) + r * (v1 * np.cos(theta) + v2 * np.sin(theta))).T


def orth(v):
    x, y, z = v
    o = np.array([0.0, -z, y] if abs(x) < abs(y) else [-z, 0.0, x])
    o /= LA.norm(o)
    return o


if __name__ == "__main__":
    main()
