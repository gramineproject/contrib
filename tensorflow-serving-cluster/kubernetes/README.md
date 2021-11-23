 # Kubernetes
[Kubernetes](https://kubernetes.io/docs/concepts/overview/what-is-kubernetes/)
is an open-source system for automating deployment, scaling, and management of
containerized applications.
In this tutorial, we use Kubernetes to manage the TensorFlow Serving containers.

## Install kubernetes
We provide a script `install_kubernetes.sh` to install Kubernetes in your machine.

```
   ./install_kubernetes.sh
```
*Note*: Please make sure OS time is updated.

## Initialize and enable taint for master node
Kubernetes allows users to taint the node so that no pods can be scheduled to it,
unless a pod explicitly tolerates the taint.

```
swapoff -a && free -m
kubeadm init --v=5 --node-name=master-node --pod-network-cidr=10.244.0.0/16

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

kubectl taint nodes --all node-role.kubernetes.io/master-
```

## Setup flannel network service
Please refer to flannel/README.md.

## Setup ingress-nginx service
Please refer to ingress-nginx/README.md
