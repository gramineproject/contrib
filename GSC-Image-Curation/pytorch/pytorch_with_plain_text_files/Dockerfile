FROM pytorch/pytorch:latest
COPY plaintext/input.jpg ./
COPY plaintext/classes.txt ./
COPY plaintext/alexnet-pretrained.pt ./
COPY pytorchexample.py ./

RUN mkdir -p app

ENTRYPOINT ["python3", "pytorchexample.py"]


