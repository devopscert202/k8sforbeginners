# Lab 05: Kind Local Kubernetes Cluster

## Overview

In this lab, you will set up a local Kubernetes cluster using **Kind**. Kind stands for **Kubernetes IN Docker** and runs Kubernetes nodes as containers on your machine. It is one of the fastest ways to create a disposable cluster for learning, testing, demos, and local development.

This lab is intentionally designed for **learning purposes**. Kind is excellent for practice and experimentation, but it should not be treated as a production cluster platform.

## Background

The official Kind project describes Kind as a tool for running local Kubernetes clusters using container-based nodes. It was originally designed for testing Kubernetes itself, but it is also widely used for:

- Kubernetes learning
- local application development
- CI pipelines
- quick feature validation
- YAML testing before using a larger cluster

Kind uses `kubeadm` to bootstrap the cluster, which makes it a very useful way to learn real Kubernetes concepts without having to provision full virtual machines.

## Prerequisites

- A machine with:
  - at least 2 CPUs
  - at least 4 GB RAM available for the lab
  - enough free disk space for container images
- A working container runtime:
  - Docker is the most common choice
  - Podman is also supported by Kind
- `kubectl` installed
- `kind` installed
- internet access to pull Kind node images and test container images
- basic familiarity with:
  - containers
  - YAML files
  - `kubectl` basics

## Learning Objectives

By the end of this lab, you will be able to:

- explain what Kind is and why it is useful
- identify the main use cases for Kind
- install and verify Kind prerequisites
- create a local Kubernetes cluster
- inspect the Kind-created nodes and kubeconfig context
- create a multi-node Kind cluster from a config file
- load a local image into Kind
- expose a simple sample app
- clean up the cluster when finished

---

## What is Kind?

**Kind** is a local Kubernetes environment that runs Kubernetes nodes as containers. Instead of creating full virtual machines, it creates Docker containers that act like Kubernetes nodes.

That gives you a lightweight cluster with a very fast setup and cleanup cycle.

### Why Kind is popular

- fast cluster creation
- easy teardown and recreation
- great for practice labs
- good for CI/CD testing
- closer to real Kubernetes behavior than only reading YAML
- useful for multi-node learning on a single laptop

### Recommendation

Use Kind for:

- learning Kubernetes
- testing manifests
- validating app deployments
- trying controllers, ingress, metrics, and dashboards locally

Do **not** treat Kind as a production platform. It is best for **learning, development, and experimentation**.

---

## Common Use Cases

### 1. Learning Kubernetes

Kind is one of the best choices for beginners because you can:

- create a cluster quickly
- break things safely
- delete and recreate the cluster in minutes

### 2. Local Application Development

Developers often use Kind to:

- test manifests locally
- validate services and deployments
- try config changes before using a shared cluster

### 3. CI Pipelines

Many teams use Kind in automation to:

- run integration tests
- verify Helm charts
- test operators and controllers
- validate Kubernetes behavior in pull requests

### 4. Multi-Node Scheduling Practice

Kind can create:

- single-node clusters
- multi-node clusters

That makes it useful for learning scheduling, taints, affinity, storage behavior, and networking concepts.

---

## Exercise 1: Verify Prerequisites

### Step 1: Check container runtime

For Docker:

```bash
docker version
docker info
```

If Docker is installed and running, both commands should return valid output.

For Podman:

```bash
podman version
```

### Step 2: Check kubectl

```bash
kubectl version --client
```

### Step 3: Check Kind

```bash
kind version
```

If `kind` is not installed yet, install it before continuing.

### Step 4: Confirm no old cluster conflicts

```bash
kind get clusters
kubectl config get-contexts
```

This helps you see whether an older local cluster already exists.

---

## Exercise 2: Install Kind

Use the official Kind quick start and release binaries for your operating system.

### Windows

- download the `kind.exe` binary from the official releases page
- place it in a directory that is part of your `PATH`

### Linux

Typical official example:

```bash
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind
```

### macOS

You can install Kind using:

```bash
brew install kind
```

After installation, verify:

```bash
kind version
```

---

## Exercise 3: Create Your First Kind Cluster

### Step 1: Create the default cluster

```bash
kind create cluster
```

This creates a cluster named `kind` by default.

### Step 2: Check the nodes

```bash
kubectl get nodes
```

Expected result:

- one control-plane node in `Ready` state

### Step 3: Check the current context

```bash
kubectl config current-context
kubectl cluster-info
```

You should see the current context set to the Kind cluster.

### Step 4: See the underlying container nodes

For Docker:

```bash
docker ps
```

You will notice the Kind node is actually running as a container.

---

## Exercise 4: Understand the Default Kind Architecture

In the simplest setup:

1. Kind creates a container to act as the control-plane node
2. Kubernetes components start inside that container
3. Kind updates kubeconfig so `kubectl` can talk to the cluster
4. workloads are scheduled inside the local cluster

This makes Kind lightweight, fast, and perfect for repeatable local labs.

---

## Exercise 5: Create a Multi-Node Kind Cluster

A multi-node setup is better for learning scheduling and more realistic cluster behavior.

### Step 1: Create a config file

Create `kind-multinode.yaml`:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
```

### Step 2: Delete the default cluster if needed

```bash
kind delete cluster
```

### Step 3: Create the multi-node cluster

```bash
kind create cluster --name kind-lab --config kind-multinode.yaml
```

### Step 4: Verify the nodes

```bash
kubectl cluster-info --context kind-kind-lab
kubectl get nodes
```

Expected result:

- one control-plane node
- two worker nodes
- all nodes in `Ready` state

### Step 5: List Kind clusters

```bash
kind get clusters
```

---

## Exercise 6: Deploy a Test Application

### Step 1: Create a simple deployment

```bash
kubectl create deployment hello-kind --image=nginx --replicas=2
```

### Step 2: Expose it as a service

```bash
kubectl expose deployment hello-kind --port=80 --target-port=80 --type=ClusterIP
```

### Step 3: Verify the resources

```bash
kubectl get deploy,pods,svc
```

### Step 4: Test from inside the cluster

```bash
kubectl run curl-test --image=curlimages/curl:8.7.1 --restart=Never -it --rm -- \
  curl http://hello-kind
```

If the app is healthy, you should receive the default nginx HTML output.

---

## Exercise 7: Load a Local Image into Kind

One of Kind's most practical features is loading a local image directly into the cluster nodes.

### Step 1: Build a local image

Example:

```bash
docker build -t myapp:dev .
```

### Step 2: Load the image into Kind

```bash
kind load docker-image myapp:dev --name kind-lab
```

### Step 3: Use the image in a Deployment

```bash
kubectl create deployment local-app --image=myapp:dev
```

If your image is only local and already loaded into Kind, this is a convenient way to test without pushing it to an external registry first.

---

## Exercise 8: Optional Port Mapping for Browser Access

Kind supports host-to-cluster port mappings through the cluster config file.

### Step 1: Create a config with extra port mappings

Create `kind-portmap.yaml`:

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080
    hostPort: 8080
    protocol: TCP
- role: worker
```

### Step 2: Recreate the cluster with the new config

```bash
kind delete cluster --name kind-lab
kind create cluster --name kind-lab --config kind-portmap.yaml
```

### Step 3: Expose an app using NodePort

```bash
kubectl create deployment hello-nodeport --image=nginx
kubectl expose deployment hello-nodeport --type=NodePort --port=80 --target-port=80
kubectl get svc hello-nodeport
```

Map the assigned NodePort to the `containerPort` you planned for, or use ingress-oriented labs later for a cleaner access model.

---

## Exercise 9: Functional Validation Checklist

- [ ] Kind is installed and returns a version
- [ ] Docker or Podman is running
- [ ] `kubectl` can reach the cluster
- [ ] the cluster context is visible in kubeconfig
- [ ] node objects are in `Ready` state
- [ ] sample deployment starts successfully
- [ ] service is created successfully
- [ ] local image loading works if tested
- [ ] cluster can be deleted and recreated cleanly

---

## Troubleshooting

### Issue 1: `kind create cluster` fails

Check:

```bash
docker info
kind version
```

Common causes:

- Docker not running
- insufficient CPU or memory
- image pull issues
- corporate proxy or DNS issues

### Issue 2: `kubectl` points to the wrong cluster

Check:

```bash
kubectl config get-contexts
kubectl config current-context
```

Switch if needed:

```bash
kubectl config use-context kind-kind-lab
```

### Issue 3: nodes are not `Ready`

Check:

```bash
kubectl get nodes
kubectl describe nodes
```

Also inspect container runtime health:

```bash
docker ps
docker logs kind-control-plane
```

### Issue 4: local image does not start

Check:

```bash
kubectl describe pod <pod-name>
```

Common causes:

- image was not loaded into the correct Kind cluster
- image name/tag mismatch
- imagePullPolicy behavior causing a pull attempt

### Issue 5: browser access does not work

Check:

- whether your cluster config includes `extraPortMappings`
- whether the service type and NodePort are correct
- whether the container is listening on the expected port

---

## Cleanup

Delete the test applications:

```bash
kubectl delete deployment hello-kind hello-nodeport local-app --ignore-not-found
kubectl delete service hello-kind hello-nodeport --ignore-not-found
```

Delete the Kind cluster:

```bash
kind delete cluster --name kind-lab
```

If you created the default cluster earlier:

```bash
kind delete cluster
```

Verify cleanup:

```bash
kind get clusters
```

---

## Key Takeaways

1. Kind is a fast local Kubernetes environment that runs nodes as containers.
2. It is strongly recommended for **learning, testing, and local development**.
3. Kind makes it easy to create both single-node and multi-node clusters.
4. It works well for validating YAML, scheduling behavior, and local app deployments.
5. Local image loading is one of the most useful features for developers.
6. Kind is not a production replacement for managed or VM-based Kubernetes clusters.

---

## Further Reading

- Kind home page: https://kind.sigs.k8s.io/
- Kind quick start: https://kind.sigs.k8s.io/docs/user/quick-start/
- Kind configuration guide: https://kind.sigs.k8s.io/docs/user/configuration/
- Kind private registries and local image workflows: https://kind.sigs.k8s.io/docs/user/private-registries/
- Kubernetes learning environment overview: https://kubernetes.io/docs/setup/learning-environment/

---

**Lab Created**: March 2026  
**Recommended Use**: Learning, local development, experimentation, CI validation  
**Not Recommended For**: Production clusters
