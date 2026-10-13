# Level 4 · Image classifiers: teaching a computer to see

To a computer, a picture is just a grid of numbers (0 = black, 255 = white, times 3 for red/green/blue).
In this level you'll go from a plain network that reads handwritten digits, to a CNN that tells cats from dogs, to borrowing a model pre-trained on millions of photos and teaching it **your own** photos. Then you put it behind an API and a drawing app.

| # | Project | New idea |
|---|---------|----------|
| 4.1 | [MNIST digits](01-mnist-digits-simple-neural-net) | PyTorch training loop, DataLoader, saving models |
| 4.2 | [Cats vs dogs CNN](02-cats-vs-dogs-cnn) | convolutions, pooling, data augmentation |
| 4.3 | [Transfer learning on your photos](03-transfer-learning-resnet-on-your-own-photos) | pretrained ResNet, freezing layers |
| 4.4 | [Serve it: `/predict` API](04-serve-image-classifier-fastapi) | file uploads, model loading, inference in an API |
| 4.5 | [Draw-a-digit web app](05-draw-a-digit-web-app) | front end + model: a demo you can show anyone |

```bash
pip install torch torchvision pillow fastapi uvicorn python-multipart
```
A GPU helps but isn't needed: everything here trains on a laptop CPU in minutes. Every training script has a `--smoke` flag that runs for 10 seconds on fake data to check that everything is wired up.

**Watch:** "But what is a convolution?" (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+convolution
