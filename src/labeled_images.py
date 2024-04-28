import torch
import os
import json
from torchvision import tv_tensors
from torchvision.transforms.v2 import functional as F
from PIL import Image


class LabeledImages(torch.utils.data.Dataset):
    def __init__(self, img_dir, json_dir, transform=None):
        self.img_dir = img_dir
        self.json_dir = json_dir
        self.transform = transform
        self.img_names = os.listdir(img_dir)

    def __len__(self):
        return len(self.img_names)

    def __getitem__(self, idx):
        img_name = self.img_names[idx]
        json_name = img_name.replace(".png", ".json")

        img_path = os.path.join(self.img_dir, img_name)
        json_path = os.path.join(self.json_dir, json_name)

        image = Image.open(img_path).convert('RGB')
        img = tv_tensors.Image(image)

        if image.mode != 'RGB':
            image = image.convert('RGB')

        with open(json_path, "r") as f:
            json_data = json.load(f)

        bbox_list = []
        labels = [0]
        area = []
        labels_text = []
        i = 1
        for label, boxes in json_data.items():
            for box in boxes:
                x1 = box["x"]
                y1 = box["y"]
                x2 = x1 + box["w"]
                y2 = y1 + box["h"]
                if box["w"] <= 0 or box["h"] <= 0:
                    continue
                bbox = [x1, y1, x2, y2]
                area.append(box["w"] * box["h"])
                bbox_list.append(bbox)
                labels.append(i)
            labels_text.append(label)
            i += 1


        image_id = idx;
        iscrowd = torch.zeros((len(labels),), dtype=torch.int64)
        target = {}
        target["boxes"] = tv_tensors.BoundingBoxes(bbox_list, format="XYXY", canvas_size=F.get_size(img))
        target["labels"] = torch.tensor(labels, dtype=torch.int64)
        target["image_id"] = image_id
        target["area"] = torch.tensor(area)
        target["labels_text"] = labels_text
        target["iscrowd"] = iscrowd

        if self.transform:
            image, target = self.transform(img, target)

        return image, target