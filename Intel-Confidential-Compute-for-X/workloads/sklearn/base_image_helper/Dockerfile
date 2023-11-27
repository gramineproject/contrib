# SPDX-License-Identifier: LGPL-3.0-or-later
# Copyright (C) 2022 Intel Corporation

FROM intel/intel-optimized-ml:scikit-learn-2023.1.1-xgboost-1.7.5-pip-base

RUN pip3 install pandas

COPY kmeans_perf_eval.py ./
COPY data ./data

CMD ["python3", "kmeans_perf_eval.py"]
