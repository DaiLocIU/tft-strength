from torchvision import datasets, transforms
from torch.utils.data import DataLoader


transforms = transforms.Compose([
    transforms.Resize((160, 160)),
    transforms.ToTensor()
])

dataset = datasets.ImageFolder(
    "data/hex-occupancy/train",
    transform=transforms
)

loader = DataLoader(
    dataset,
    batch_size=4,
    shuffle=True
)

images, labels = next(iter(loader))

print(dataset.classes)
print(images.shape)
print(labels.tolist())