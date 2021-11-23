# TensorFlow Serving Cluster PPML Tutorial Scripts

This directory contains the scripts package for [TensorFlow Serving cluster PPML tutorial](https://gramine.readthedocs.io/en/latest/tutorials/tensorflow-serving-cluster/index.html), split into two sub-directories:
- Kubernetes. This directory contains Yaml configuration files of the services
  `flannel` and `ingress-nginx` and installation scripts. We need to setup these
  two services in the host to run Kubernetes.

- TensorFlow Serving. This directory contains the client scripts, docker image
  related scripts, the Yaml configuration of TensorFlow Serving in Kubernetes.

We build Kubernetes and TensorFlow Serving on SGX-enabled platforms with Ubuntu
18.04.

# Tutorial Introduction

Simply running a TensorFlow Serving system inside Gramine is not enough for a
safe & secure end-user experience. Thus, there is a need to build a complete
secure inferencing flow. [The linked tutorial](https://gramine.readthedocs.io/en/latest/tutorials/tensorflow-serving-cluster/index.html)
will present TensorFlow Serving with Intel SGX and Gramine and will provide
end-to-end protection (from client to servers) and integrate various security
ingredients such as the load balancer (nginx Ingress) and elastic scheduler
(Kubernetes).

# Prerequisites

The following steps should suffice to run the PPML on a Ubuntu 18.04 installation.

- Ubuntu 18.04. The linked tutorial should work on other Linux distributions as
  well, but for simplicity we provide the steps for Ubuntu 18.04 only.
  Please install additional DNS-resolver libraries:
```
   sudo apt install libnss-mdns libnss-myhostname
```

- Docker Engine. Docker Engine is an open source containerization technology for
  building and containerizing your applications. In the linked tutorial, applications,
  like Gramine, TensorFlow Serving, secret providers, will be built in Docker
  images. Then Kubernetes will manage these Docker images.
  Please follow [this guide](https://docs.docker.com/engine/install/ubuntu/#install-using-the-convenience-script)
  to install Docker engine.

- Python3. Please install python3 package since our python script is based on
  python3.

- TensorFlow Serving. [TensorFlow Serving](https://www.TensorFlow.org/tfx/guide/serving)
  is a flexible, high-performance serving system for machine learning models,
  designed for production environments. Install:
```
     pip3 install -r <gramine-contrib repository>/tensorflow-serving-cluster/tensorflow-serving/client/requirements.txt
```
- Kubernetes. [Kubernetes](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)
  is an open-source system for automating deployment,
  scaling, and management of containerized applications. In the linked tutorial,
  we provide a script (`install_kubernetes.sh`) under `<gramine-contrib repository>/tensorflow-serving-cluster/kubernetes/` to install Kubernetes on your machine.

- Intel SGX Driver and SDK/PSW. You need a machine that supports Intel SGX and
  FLC/DCAP. Please follow [this guide](https://download.01.org/intel-sgx/latest/linux-latest/docs/Intel_SGX_Installation_Guide_Linux_2.10_Open_Source.pdf)
  to install the Intel SGX driver and SDK/PSW. Make sure to install the driver with ECDSA/DCAP attestation.

- Gramine. Follow [Quick Start](https://gramine.readthedocs.io/en/latest/quickstart.html)
  to build Gramine. [In the linked tutorial](https://gramine.readthedocs.io/en/latest/tutorials/tensorflow-serving-cluster/index.html),
  we will need to build Gramine in the host to get the tool `pf_crypt`, which
  will be used to encrypt the model file.

# Run the PPML

Please follow the [TensorFlow Serving cluster PPML tutorial](https://gramine.readthedocs.io/en/latest/tutorials/tensorflow-serving-cluster/index.html)
to execute the provided scripts step by step.

