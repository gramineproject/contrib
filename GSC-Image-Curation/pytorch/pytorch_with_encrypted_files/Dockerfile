FROM pytorch/pytorch:latest
COPY encrypted/input.jpg ./
COPY encrypted/classes.txt ./
COPY encrypted/alexnet-pretrained.pt ./
COPY pytorchexample.py ./

RUN mkdir -p app

ENTRYPOINT ["python3", "pytorchexample.py"]
