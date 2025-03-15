import os
import json
from pathlib import Path
from PIL import Image
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration, DetrImageProcessor, DetrForObjectDetection

if __name__ == "__main__":
    # Load Caption Model (BLIP)
    caption_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    caption_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    # Load Object Detection Model (DETR)
    object_processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
    object_model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

    # Folder where images are stored
    UPLOAD_FOLDER = Path('./uploads')  
    OUTPUT_FILE = "image_metadata.json"

    # Get all images from the folder
    image_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith((".jpg", ".png", ".jpeg"))]

    if not image_files:
        print("No images found in the upload folder.")
        exit()

    # Load existing metadata if available
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, "r") as f:
            image_metadata = json.load(f)
    else:
        image_metadata = {}

    # Process images (captions + objects)
    for filename in image_files:
        if filename in image_metadata:
            print(f"Skipping {filename} (already processed)")
            continue

        img_path = UPLOAD_FOLDER / filename
        image = Image.open(img_path).convert("RGB")

        # Generate Caption
        caption_inputs = caption_processor(images=image, return_tensors="pt")
        caption_ids = caption_model.generate(**caption_inputs)
        caption = caption_processor.decode(caption_ids[0], skip_special_tokens=True)

        # Detect Objects
        object_inputs = object_processor(images=image, return_tensors="pt")
        outputs = object_model(**object_inputs)

        # Extract detected objects (confidence > 0.7)
        logits = outputs.logits.softmax(-1)[0]  # Get class probabilities
        threshold = 0.7  # Set a confidence threshold
        labels = [object_model.config.id2label.get(i.item(), "unknown") for i in logits.argmax(-1) if logits.max(-1)[0][i] > threshold]
        object_list = list(set(labels))

        # Save metadata
        image_metadata[filename] = {
            "caption": caption,
            "objects": object_list
        }

        print(f"Processed {filename} | Caption: {caption} | Objects: {object_list}")

    # Save metadata to JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(image_metadata, f, indent=4)

    print(f"Metadata saved in '{OUTPUT_FILE}'")
