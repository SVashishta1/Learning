"""Shared bits used by training here AND by the API in project 4.4 (copy this file there)."""
import torch
from torch import nn
from torchvision import models, transforms

IMAGENET_MEAN, IMAGENET_STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)

# The pretrained model expects 224x224 images normalised exactly like its original training data
eval_transform = transforms.Compose([
    transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
    transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0)), transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(0.2, 0.2, 0.2), transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)])


def build_model(num_classes: int, pretrained: bool = True) -> nn.Module:
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)       # 11M parameters trained on 1.2M ImageNet photos
    for p in model.parameters():
        p.requires_grad = False                    # FREEZE: keep all the general "seeing" skills
    model.fc = nn.Linear(model.fc.in_features, num_classes)   # NEW head: only this learns your classes
    return model


def load_checkpoint(path, device="cpu"):
    ckpt = torch.load(path, map_location=device)
    model = build_model(len(ckpt["classes"]), pretrained=False)
    model.load_state_dict(ckpt["state_dict"])
    return model.eval(), ckpt["classes"]
