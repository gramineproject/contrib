# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

FROM bitnami/scikit-learn-intel

RUN pip3 install pandas

COPY kmeans_perf_eval.py /app/
COPY data /app/data

CMD ["python3", "kmeans_perf_eval.py"]
