# Resources

## Label Studio

- [Label Studio export annotations guide](https://labelstud.io/guide/export.html)
  Explains how Label Studio exports annotations and notes that image rectangle coordinates in JSON are percentages of the original image.

- [Label Studio API guide](https://labelstud.io/guide/api)
  Useful later if you want scripts to import/export tasks automatically.

- [Label Studio KeyPointLabels tag](https://labelstud.io/tags/keypointlabels)
  Explains labeled keypoint annotations for images and the exported percentage-based point values.

- [Label Studio YOLO export guide](https://labelstud.io/guide/export.html)
  Notes that YOLO keypoint export needs `KeyPointLabels` with ordered `model_index` values and a
  parent `RectangleLabels` box.

## YOLO / Ultralytics

- [Ultralytics YOLO Python usage](https://docs.ultralytics.com/usage/python/)
  Official guide for loading models, training, validation, prediction, and export from Python.

- [Ultralytics object detection task guide](https://docs.ultralytics.com/tasks/detect/)
  Official guide for object detection training, validation, prediction, and dataset expectations.

- [Ultralytics predict mode guide](https://docs.ultralytics.com/modes/predict/)
  Official guide for running inference with trained models, including `source`, `conf`, `save`,
  `project`, and `name` prediction arguments.

- [Ultralytics image classification dataset guide](https://docs.ultralytics.com/datasets/classify/)
  Official folder layout for classification datasets, where each class is a folder under `train`,
  `val`, and optionally `test`.

- [Ultralytics image classification task guide](https://docs.ultralytics.com/tasks/classify/)
  Official guide for training and predicting with YOLO classification models.

- [Ultralytics pose dataset guide](https://docs.ultralytics.com/datasets/pose/)
  Official format for YOLO pose/keypoint datasets, including `kpt_shape` and normalized keypoint
  label rows.

## PyTorch / TorchVision

- [PyTorch: Datasets & DataLoaders](https://docs.pytorch.org/tutorials/beginner/basics/data_tutorial.html)
  Official introduction to separating image data from the training loop. Use for: understanding
  `Dataset`, `DataLoader`, batches, and train/validation iteration.

- [TorchVision `ImageFolder`](https://docs.pytorch.org/vision/stable/generated/torchvision.datasets.ImageFolder.html)
  Official reference for the folder-per-class dataset format. Use for: loading the existing
  `occupied` and `empty` hex-crop folders without a new annotation format.

- [PyTorch transfer-learning tutorial](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html)
  Official example of adapting a pretrained vision model to a small image-classification task. Use
  for: choosing a practical first PyTorch model after the data pipeline is understood.

- [PyTorch: Build the Neural Network](https://docs.pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html)
  Official explanation of `nn.Module`, `forward`, and composing layers. Use for: understanding the
  first hex-occupancy model before training it.

## Hex Geometry

- [Red Blob Games: Hexagonal Grids](https://www.redblobgames.com/grids/hexagons/)
  Visual guide to hex grid geometry, including pointy-top spacing, center distances, offsets, and
  coordinate systems.
