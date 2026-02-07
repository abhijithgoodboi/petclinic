import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import json

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Class names (must be same order as training)
    class_names = ['Flea_Allergy', 'Health', 'Ringworm', 'Scabies']
    num_classes = len(class_names)

    # Load model architecture
    model = models.resnet50(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)

    # Load trained weights
    model.load_state_dict(torch.load("best_model_cat.pth", map_location=device))
    model = model.to(device)


    infer_transform = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                            [0.229, 0.224, 0.225])
    ])


    def predict_image(image_path, model):
        image = Image.open(image_path).convert("RGB")
        image = infer_transform(image).unsqueeze(0)  # Add batch dim
        image = image.to(device)

        with torch.no_grad():
            outputs = model(image)
            probs = torch.softmax(outputs, dim=1)
            confidence, pred_idx = torch.max(probs, 1)

        predicted_class = class_names[pred_idx.item()]
        confidence = confidence.item()

        return predicted_class, confidence



    img_path = "./Screenshot_2026-01-29-12-02-04_1920x1080.png"

    pred_class, conf = predict_image(img_path, model)

    print(f"Predicted Class: {pred_class}")


    data = {
        "cat skin disease": pred_class
    }

    with open("skin_disease.json", "w") as file:
        json.dump(data, file)


    print(f"Confidence: {conf:.4f}")


if __name__ == "__main__":
    main()
