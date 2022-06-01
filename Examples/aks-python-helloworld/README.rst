Graminizing Python Docker image
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This section demonstrates how to translate the Python Docker Hub image to a
graminized image, which can be readily to deployed to a confidential compute AKS
cluster.

.. warning::

   This example relies on insecure arguments provided at runtime and should not
   be used production. To use trusted arguments, please see the `manpage of GSC
   <https://gramine.readthedocs.io/projects/gsc/en/latest/index.html?highlight=python#using-gramine-s-trusted-command-line-arguments>`__.

#. Pull Python image::

       docker pull python

#. Create the application-specific Manifest file :file:`python.manifest`::

       sgx.enclave_size = "256M"
       sgx.thread_num = 4

#. Graminize the Python image using gsc <https://github.com/gramineproject/gsc> 
   and allow insecure runtime arguments::

       ./gsc build --insecure-args -c python python.manifest

#. Sign the graminized image with your enclave signing key::

       ./gsc sign-image python enclave-key.pem

#. Push resulting image to Docker Hub or your preferred registry::

       docker tag gsc-python <dockerhubusername>/gsc-aks-python
       docker push <dockerhubusername>/gsc-aks-python

Deploying a "HelloWorld" Python Application in a confidential compute AKS cluster
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

#. Create job deployment file :file:`gsc-aks-python-deployment.yaml` for AKS. It specifies
   the underlying Docker image and the insecure arguments (in this case Python
   code to print "HelloWorld!")::

       apiVersion: batch/v1
       kind: Job
       metadata:
          name: gsc-aks-python
          labels:
             app: gsc-aks-python
       spec:
          template:
             metadata:
                labels:
                   app: gsc-aks-python
             spec:
                containers:
                - name: gsc-aks-python
                  image:  <dockerhubusername>/gsc-aks-python
                  imagePullPolicy: Always
                  args: ["-c", "print('HelloWorld!')"]
                  resources:
                     limits:
                        kubernetes.azure.com/sgx_epc_mem_in_MiB: 10
                restartPolicy: Never
          backoffLimit: 0

#. Deploy `gsc-aks-python` job::

       kubectl apply -f gsc-aks-python-deployment.yaml

#. Test job status::

       kubectl get jobs -l app=gsc-aks-python-deployment

#. Receive logs of job::

       kubectl logs -l app=gsc-aks-python-deployment

#. Delete job after completion::

       kubectl delete -f gsc-aks-python-deployment.yaml
