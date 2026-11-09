"""
PyTorch Dataset and DataLoader Module for Waste Image Classification.
Loads images from stratified split manifests and applies standard
ImageNet normalization and augmentations.
"""

import os
from pathlib import Path
from typing import Optional, Callable, Tuple, List
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms

# Standard ImageNet statistics
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def get_train_transforms(image_size: Tuple[int, int] = (224, 224)) -> transforms.Compose:
    """Returns training data augmentation & normalization pipeline."""
    return transforms.Compose([
        transforms.Resize((int(image_size[0] * 1.1), int(image_size[1] * 1.1))),
        transforms.RandomCrop(image_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

def get_val_transforms(image_size: Tuple[int, int] = (224, 224)) -> transforms.Compose:
    """Returns deterministic validation & test preprocessing pipeline."""
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    ])

class WasteDataset(Dataset):
    """
    PyTorch Dataset loading images and canonical category IDs from split CSVs.
    """
    def __init__(
        self,
        csv_file: Path,
        transform: Optional[Callable] = None,
        base_dir: Optional[Path] = None
    ):
        self.csv_file = Path(csv_file)
        if not self.csv_file.exists():
            raise FileNotFoundError(f"Manifest CSV not found: {self.csv_file}")
            
        self.df = pd.read_csv(self.csv_file)
        self.transform = transform
        self.base_dir = base_dir

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int, str]:
        row = self.df.iloc[idx]
        file_path = row["file_path"]
        
        # Resolve path
        p = Path(file_path)
        if not p.is_absolute() and self.base_dir:
            p = self.base_dir / p
            
        try:
            image = Image.open(p).convert("RGB")
        except Exception as e:
            # Fallback black image if corrupted at runtime
            image = Image.new("RGB", (224, 224), (0, 0, 0))
            
        category_id = int(row["category_id"])
        canonical_name = str(row["canonical_category"])
        
        if self.transform:
            image = self.transform(image)
            
        return image, category_id, canonical_name

def create_dataloaders(
    train_csv: Path,
    val_csv: Path,
    batch_size: int = 32,
    num_workers: int = 2,
    pin_memory: bool = True
) -> Tuple[DataLoader, DataLoader]:
    """Factory creating Train and Validation DataLoaders."""
    train_dataset = WasteDataset(train_csv, transform=get_train_transforms())
    val_dataset = WasteDataset(val_csv, transform=get_val_transforms())
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=pin_memory
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory
    )
    return train_loader, val_loader

