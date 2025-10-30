# neurvps Environment Setup

This document explains how to reproduce the `neurvps` Conda environment, including CUDA toolkit support and GPU compatibility verification.

## 1. Create Conda Environment from YAML

Save the following YAML content as `neurvps_env.yaml` and run:

```bash
conda env create -f neurvps_env.yaml
conda activate neurvps
```

## 2. Install PyTorch with CUDA 12.1

Ensure you have a compatible GPU and run:

```bash
pip install torch==2.1.2+cu121 torchvision==0.16.2+cu121 --index-url https://download.pytorch.org/whl/cu121
```

## 3. Verify CUDA and GPU Tools

### Check `nvcc` Version

```bash
nvcc --version
```

Ensure it shows version 12.4 or your desired CUDA version.

### Check GPU Availability with `nvidia-smi`

```bash
nvidia-smi
```

This will confirm the GPU is recognized and the correct driver is installed.

## 4. Additional Notes

- This setup assumes you're using Linux and have `conda` and NVIDIA drivers installed.
- PyTorch should detect the GPU automatically after activating the environment and installing CUDA-specific wheels.

