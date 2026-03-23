"""
LeNet-5 Classifier for Federated Learning on MNIST.

USE THIS FILE IN YOUR WORKER (EC2 instances — PyTorch available).

This file provides:
  - LeNet5 model class (PyTorch)
  - Serialization helpers: state_dict <-> .npz bytes
  - Model creation and loading utilities

"""

import io
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from collections import OrderedDict


NUM_CLASSES = 10


class LeNet5(nn.Module):
    """LeNet-5 for MNIST classification.

    Input:  (batch, 1, 28, 28)
    Output: (batch, 10)
    """

    def __init__(self, num_classes=NUM_CLASSES):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 6, 5, padding=2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, num_classes)

    def forward(self, x):
        x = F.max_pool2d(F.relu(self.conv1(x)), 2)
        x = F.max_pool2d(F.relu(self.conv2(x)), 2)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = self.fc3(x)
        return x


def create_model(num_classes=NUM_CLASSES):
    """Create a fresh LeNet-5 model with random weights."""
    return LeNet5(num_classes=num_classes)


def load_model(state_dict, num_classes=NUM_CLASSES):
    """Create a LeNet-5 model and load the given state_dict.

    Args:
        state_dict: OrderedDict of PyTorch tensors (from deserialize_state_dict).
        num_classes: Number of output classes (default 10).

    Returns:
        LeNet5 model with loaded weights, ready for training or inference.
    """
    model = LeNet5(num_classes=num_classes)
    model.load_state_dict(state_dict)
    return model


def serialize_state_dict(state_dict):
    """Convert a PyTorch state_dict to .npz bytes for S3 upload.

    Args:
        state_dict: OrderedDict from model.state_dict()
                    (keys are layer names, values are torch.Tensor)

    Returns:
        bytes — the .npz archive contents, ready for s3.put_object(Body=...)

    Example:
        sd = model.state_dict()
        data = serialize_state_dict(sd)
        s3.put_object(Bucket=bucket, Key="models/global_model_round_0.npz", Body=data)
    """
    buf = io.BytesIO()
    np.savez(buf, **{k: v.cpu().numpy() for k, v in state_dict.items()})
    return buf.getvalue()


def deserialize_state_dict(data):
    """Convert .npz bytes from S3 to a PyTorch state_dict.

    Args:
        data: bytes — raw .npz file content from s3.get_object()["Body"].read()

    Returns:
        OrderedDict of torch.Tensor — ready for model.load_state_dict() or load_model()

    Example:
        resp = s3.get_object(Bucket=bucket, Key="models/global_model_round_0.npz")
        sd = deserialize_state_dict(resp["Body"].read())
        model = load_model(sd)
    """
    npz = np.load(io.BytesIO(data))
    return OrderedDict({k: torch.from_numpy(npz[k]) for k in npz.files})


# ============================================================================
# TODO: Implement your worker below
# ============================================================================

def train_local(model, dataloader, lr, epochs):
    """Train the model locally and return metrics.

    Args:
        model: LeNet5 model to train
        dataloader: PyTorch DataLoader with training data
        lr: learning rate
        epochs: number of local training epochs

    Returns:
        dict with keys:
            "train_loss": float — average training loss
            "train_accuracy": float — average training accuracy
            "num_samples": int — number of training samples
    """
    # TODO: Implement local training loop
    raise NotImplementedError("Implement local training")


def worker_main():
    """FL worker main loop.

    This function runs on each EC2 instance. You need to:

    1. Read PARTITION_ID and ASU_ID from environment variables
    2. Set up boto3 S3 client
    3. Load your MNIST partition from local disk
       (data is at /home/ubuntu/fl-worker/data_cache/client-{PARTITION_ID}/)
    4. For each round (0 to NUM_ROUNDS-1):
       a. Poll S3 for global model: models/global_model_round_{R}.npz
       b. Download and deserialize the global model
       c. Train locally on your partition
       d. Upload trained model .npz to local-bucket (TRIGGERS Lambda)
          Key: updates/local_model_round_{R}_worker_{C}.npz
    5. Exit after all rounds complete
    """
    # TODO: Implement your worker logic here
    raise NotImplementedError("Implement your FL worker")


if __name__ == "__main__":
    worker_main()
