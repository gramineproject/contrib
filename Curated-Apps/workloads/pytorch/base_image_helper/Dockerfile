FROM pytorch/pytorch:latest
COPY input.jpg ./
COPY classes.txt ./
COPY alexnet-pretrained.pt ./
COPY pytorchexample.py ./

ENTRYPOINT ["python3", "pytorchexample.py"]
