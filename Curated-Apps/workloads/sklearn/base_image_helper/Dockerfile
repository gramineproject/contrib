FROM bitnami/scikit-learn-intel

RUN pip3 install pandas

COPY kmeans_perf_eval.py /app/
COPY data /app/data

ENTRYPOINT ["python3", "kmeans_perf_eval.py"]
