# Level 4 · Computer vision: teaching a computer to see

To a computer, a picture is just a grid of numbers (0 = black, 255 = white, times 3 for red/green/blue).
In this level you'll go from a plain network that reads handwritten digits, to a CNN that tells cats from dogs, to borrowing a model pre-trained on millions of photos and teaching it **your own** photos. Then you put it behind an API and a drawing app you can show anyone.

| # | Project | New idea | Time |
|---|---------|----------|------|
| 4.1 | [MNIST digits](01-mnist-digits-simple-neural-net) | PyTorch training loop, DataLoader, saving models | 1 h |
| 4.2 | [Cats vs dogs CNN](02-cats-vs-dogs-cnn) | convolutions, pooling, data augmentation | 2 h |
| 4.3 | [Transfer learning on your photos](03-transfer-learning-resnet-on-your-own-photos) | pretrained ResNet, freezing layers | 2 h |
| 4.4 | [Serve it: `/predict` API](04-serve-image-classifier-fastapi) | file uploads, model loading, inference in an API | 1.5 h |
| 4.5 | [Draw-a-digit web app](05-draw-a-digit-web-app) | front end + model: a demo you can show anyone | 1.5 h |

```bash
pip install torch torchvision pillow numpy fastapi "uvicorn[standard]" python-multipart httpx pytest
```
That covers the whole level. Each project folder also has its own `requirements.txt` (`pip install -r requirements.txt` inside a folder). If pip can't find a PyTorch build for your computer, use the install selector at https://pytorch.org/get-started/locally/.

**GPU?** It helps but isn't needed: everything here trains on a laptop CPU in minutes (4.1 in about a minute, 4.2 in 5–15 minutes). Google Colab has free GPUs if your laptop is slow. Every training script has a `--smoke` flag that runs for a few seconds on fake data to check everything is wired up, without downloading or saving anything.

**Downloads:** 4.1 downloads MNIST (~12 MB), 4.2 downloads CIFAR-10 (~170 MB), 4.3 downloads ResNet-18 weights (~45 MB, plus CIFAR-10 if you use the demo photos). Each happens once.

**The projects connect:** 4.3's `transfer_model.pt` is served by 4.4, and 4.1's `mnist_mlp.pt` powers 4.5, so do them in order.

**Watch:** "But what is a convolution?" (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+convolution

**Finish line for Level 4:** you can draw a digit in your browser and watch your own model read it (4.5). Then go to [Level 5 · Text models](../level-5-text-models).
