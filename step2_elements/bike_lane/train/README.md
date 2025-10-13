This directory contains the Jupyter Notebook `train.ipynb` used to train the best-performing multimodal bike lane classification model described in the paper. The script is designed for reproducibility and can be adapted for training on custom datasets.

The code implements the optimal architecture: a late-stage, decision-level fusion model with a hierarchical label structure.

## 🏋️‍♀️ Training Configuration
The model was trained using the following environment and hyperparameters.

| Category                 | Parameter                 | Value / Specification                                  |
| ------------------------ | ------------------------- | ------------------------------------------------------ |
| **Training Environment** | Hardware                  | NVIDIA RTX A6000 (48GB VRAM)                           |
|                          | Software                  | Python 3.10, PyTorch 2.4.1                             |
| **Model Architecture** | Backbone                  | Swin Transformer (Swin-Large, pretrained on ImageNet)  |
|                          | Transfer learning         | Backbone frozen except for the final two stages        |
|                          | Input Image Size          | 384 × 384 pixels (RGB)                                 |
| **Hyperparameters** | Number of Epochs          | 80 (with early stopping)                               |
|                          | Batch Size                | 16                                                     |
|                          | Optimizer                 | AdamW (auto-selected)                                  |
|                          | Learning Rate (Initial)   | 0.00005                                                |
|                          | LR Scheduler              | `ReduceLROnPlateau` (factor 0.5, patience 3)           |
|                          | Weight Decay              | Default (AdamW eps = 1e-6)                             |
| **Regularization** | Dropout                   | 0.3                                                    |
|                          | Early Stopping Patience   | 15 Epochs (stops if validataion loss does not improve) |
|                          | Dataloadeer Workers       | 4                                                      |
| **Evaluation Protocol** | Metrics                   | Accuracy, Macro Precision, Macro Recall, Macro F1      |
|                          | Seeds                     | 5 random seeds (2023-2027) to account for stochastic variation; results reported as mean ± std     |

## Dataset
The model was trained on a custom-built, geographically diverse dataset. The completed dataset encompasses 1,459 unique street segments across 28 U.S. cities, broken down as follows:
- 764 locations with no bike lanes
- 459 with designated bike lanes
- 236 with protected bike lanes

With three images per location (two street-level, one satellite), the dataset contains 4,377 total images.

For model training, the data was split into training and validation sets using an approximate 7:3 ratio. The training sets for protected and designated bike lanes were upsampled to address class imbalance. The `TRAIN.csv` file defines the samples used for training, while `VAL.csv` defines the validation set.

## 🚀 Train on Your Own Data
If you are interested in training the model on your own dataset, please refer to the `train.ipynb` notebook.

You will need to modify the configuration settings under **Block 2** of the notebook to set the appropriate directories for your image data and your custom `TRAIN.csv` and `VAL.csv` files.
