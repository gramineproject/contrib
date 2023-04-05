# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

FROM pytorch/pytorch:latest
COPY input.jpg ./
COPY classes.txt ./
COPY alexnet-pretrained.pt ./
COPY pytorchexample.py ./

ENTRYPOINT ["python3", "pytorchexample.py"]
