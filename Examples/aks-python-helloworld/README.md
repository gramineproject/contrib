# Deploying a graminized Python Docker image to AKS cluster

This example demonstrates how to translate the Python Docker Hub image to a
graminized image, which can be readily deployed to a confidential compute AKS
cluster.

   *Warning:* this example relies on insecure arguments provided at runtime and
   should not be used production. To use trusted arguments, please see
   [GSC documentation] (https://gramine.readthedocs.io/projects/gsc).

## Pull Python image:

       docker pull python

## Graminize the Python image using GSC, and allow insecure runtime arguments::

       ./gsc build --insecure-args python python.manifest

## Sign the graminized image with your enclave signing key:

       ./gsc sign-image python enclave-key.pem

## Push resulting image to Docker Hub or your preferred registry:

       docker tag gsc-python <dockerhubusername>/gsc-aks-python
       docker push <dockerhubusername>/gsc-aks-python

Deploying a "HelloWorld" Python Application in a confidential compute AKS cluster

## Deploy `gsc-aks-python` job:

       kubectl apply -f gsc-aks-python-deployment.yaml

## Test job status::

       kubectl get jobs -l app=gsc-aks-python-deployment

## Receive logs of job:

       kubectl logs -l app=gsc-aks-python-deployment

## Delete job after completion:

       kubectl delete -f gsc-aks-python-deployment.yaml
