# Kubernetes Troubleshooting Guide

- [Kubernetes Troubleshooting Guide](#kubernetes-troubleshooting-guide)
  * [Introduction](#introduction)
- [Kubernetes Troubleshooting Areas](#kubernetes-troubleshooting-areas)
  * [Section 1: Troubleshooting Kubernetes Cluster](#section-1--troubleshooting-kubernetes-cluster)
    + [Areas to Troubleshoot](#areas-to-troubleshoot)
    + [Possible Scenarios](#possible-scenarios)
    + [Steps and Commands to Troubleshoot](#steps-and-commands-to-troubleshoot)
      - [1. View Nodes in the Cluster](#1-view-nodes-in-the-cluster)
      - [2. Fetch Cluster Information](#2-fetch-cluster-information)
      - [3. Obtain a Cluster Dump](#3-obtain-a-cluster-dump)
      - [4. Explore Dump Command Options](#4-explore-dump-command-options)
      - [5. Generate Namespace-Specific Dump](#5-generate-namespace-specific-dump)
      - [6. Check Cluster Component Health](#6-check-cluster-component-health)
    + [Things to Check](#things-to-check)
  * [Section 2: Understanding Kubernetes Logging Architecture](#section-2--understanding-kubernetes-logging-architecture)
    + [Areas to Troubleshoot](#areas-to-troubleshoot-1)
    + [Possible Scenarios](#possible-scenarios-1)
    + [Steps and Commands to Troubleshoot](#steps-and-commands-to-troubleshoot-1)
      - [Step 1: Get Help with Logging](#step-1--get-help-with-logging)
      - [Step 2: Create a Pod and View Logs](#step-2--create-a-pod-and-view-logs)
      - [Step 3: Advanced Log Options](#step-3--advanced-log-options)
    + [Things to Check](#things-to-check-1)
    + [Tools and Prerequisites](#tools-and-prerequisites)
  * [Section 3: Understanding Cluster and Node Logs](#section-3--understanding-cluster-and-node-logs)
    + [Areas to Troubleshoot](#areas-to-troubleshoot-2)
    + [Possible Scenarios](#possible-scenarios-2)
    + [Steps and Commands to Troubleshoot](#steps-and-commands-to-troubleshoot-2)
      - [Step 1: View Control-Plane Component Logs](#step-1--view-control-plane-component-logs)
      - [Step 2: View Controller Manager Logs](#step-2--view-controller-manager-logs)
      - [Step 3: View etcd Logs](#step-3--view-etcd-logs)
      - [Step 4: View Worker Node Logs](#step-4--view-worker-node-logs)
    + [Things to Check](#things-to-check-2)
    + [Tools and Prerequisites](#tools-and-prerequisites-1)
  * [Section 4: Troubleshooting Node Readiness](#section-4--troubleshooting-node-readiness)
    + [Areas to Troubleshoot](#areas-to-troubleshoot-3)
    + [Possible Scenarios](#possible-scenarios-3)
    + [Steps and Commands to Troubleshoot](#steps-and-commands-to-troubleshoot-3)
      - [Step 1: Check the Node Status on the Master Node](#step-1--check-the-node-status-on-the-master-node)
      - [Step 2: Disable the Worker Node and Diagnose](#step-2--disable-the-worker-node-and-diagnose)
      - [Step 3: Fix the Worker Node](#step-3--fix-the-worker-node)
    + [Things to Check](#things-to-check-3)
    + [Tools and Prerequisites](#tools-and-prerequisites-2)
  * [Section 5: Understanding Container Logs](#section-5--understanding-container-logs)
      - [Steps to Check Container Logs:](#steps-to-check-container-logs-)
  * [Section 6: Analyzing Pod Logs and Troubleshooting Pod Issues](#section-6--analyzing-pod-logs-and-troubleshooting-pod-issues)
      - [6.1 Configure and Verify Nginx Deployment](#61-configure-and-verify-nginx-deployment)
      - [6.2 Tainting Worker Nodes and Deployment Failures](#62-tainting-worker-nodes-and-deployment-failures)
      - [6.3 Troubleshooting Incorrect Image Names](#63-troubleshooting-incorrect-image-names)
      - [6.4 Pod and Container Status Issues and Fixes](#64-pod-and-container-status-issues-and-fixes)
  * [Section 7: Understanding Application Troubleshooting](#section-7--understanding-application-troubleshooting)
      - [7.1 Setup and Diagnose the Application Pod](#71-setup-and-diagnose-the-application-pod)
      - [7.2 Troubleshooting the Application Pod](#72-troubleshooting-the-application-pod)
      - [7.3 Common Pod Troubleshooting Scenarios](#73-common-pod-troubleshooting-scenarios)
      - [7.4 Additional Troubleshooting Tools](#74-additional-troubleshooting-tools)
  * [Section 8: Handling Component Failure Threshold](#section-8--handling-component-failure-threshold)
      - [8.1 Check the Cluster Health Information](#81-check-the-cluster-health-information)
  * [Section 9: Troubleshooting Networking Issues](#section-9--troubleshooting-networking-issues)
      - [9.1 Create an HTTPD Pod](#91-create-an-httpd-pod)
      - [9.2 Create an HTTPD Service](#92-create-an-httpd-service)
      - [9.3 Check Labels for All Pods](#93-check-labels-for-all-pods)
      - [9.4 Modify and Create a New Service](#94-modify-and-create-a-new-service)
  * [Additional Reading](#additional-reading)
  * [Importance of Troubleshooting Skills](#importance-of-troubleshooting-skills)


---

## Introduction

Kubernetes, while immensely powerful, can present a variety of challenges during day-to-day operations. From application deployment issues to cluster-level failures, having a structured approach to diagnosing and resolving these problems is essential. This troubleshooting guide aims to assist users in identifying common issues encountered in Kubernetes environments and provides actionable steps to resolve them effectively.

By following this guide, you will gain insights into:
- Diagnosing pod-related issues.
- Investigating cluster health and node failures.
- Resolving networking and service connectivity problems.
- Debugging persistent storage and volume-related errors.
- Troubleshooting authentication and role-based access control (RBAC).

This guide builds upon practical lab exercises to ensure a hands-on understanding of Kubernetes troubleshooting. Use it as a reference for identifying and resolving issues in real-world scenarios. The structure of this document will evolve as we incorporate detailed steps and case studies from provided lab materials.

# Kubernetes Troubleshooting Areas

## Section 1: Troubleshooting Kubernetes Cluster

### Areas to Troubleshoot

- Cluster health and configuration.
- Node statuses and connectivity.
- Namespace-specific issues.

### Possible Scenarios

- The cluster is unresponsive or partially operational.
- Nodes are not in a ready state.
- Namespace-specific issues causing resource unavailability.

### Steps and Commands to Troubleshoot

#### 1. View Nodes in the Cluster

**Command:**

```bash
kubectl get nodes
```

Provides an overview of all nodes and their statuses.

#### 2. Fetch Cluster Information

**Command:**

```bash
kubectl cluster-info
```

Details about the cluster's control plane and components.

#### 3. Obtain a Cluster Dump

**Command:**

```bash
kubectl cluster-info dump
```

Generates diagnostic information about the cluster's state.

#### 4. Explore Dump Command Options

**Command:**

```bash
kubectl cluster-info dump --help
```

Displays available options for generating a cluster dump.

#### 5. Generate Namespace-Specific Dump

**Command:**

```bash
kubectl cluster-info -n <namespace> dump
```

For example, to diagnose issues in the `test` namespace:

```bash
kubectl cluster-info -n test dump
```

#### 6. Check Cluster Component Health

**Command:**

```bash
kubectl get componentstatus
```

Reports the health of cluster components such as etcd, scheduler, and controller-manager.

### Things to Check

- Are all nodes in a `Ready` state?
- Is the control plane accessible using `kubectl cluster-info`?
- Are specific namespaces experiencing issues?
- Are cluster components reporting healthy statuses?

By following these steps, you can effectively diagnose and resolve common Kubernetes cluster issues.

---

## Section 2: Understanding Kubernetes Logging Architecture

### Areas to Troubleshoot

- Application logs and debugging.
- Container-level logging.
- Namespace-wide log aggregation.

### Possible Scenarios

- Logs are not accessible for a specific pod or container.
- Need to debug application behavior using logs.
- Cluster-wide log monitoring requirements.

### Steps and Commands to Troubleshoot

#### Step 1: Get Help with Logging

**Command:**

```bash
kubectl logs --help
```

Displays available options and flags for fetching logs.

#### Step 2: Create a Pod and View Logs

1. Create a YAML file for the pod: **Command:**

   ```bash
   vi busybox.yaml
   ```

   Add the following content to the file:

   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: counter
   spec:
     containers:
     - name: count
       image: busybox:1.28
       args: [/bin/sh, -c, 'i=0; while true; do echo "$i: $(date)"; i=$((i+1)); sleep 1; done']
   ```

2. Deploy the pod and fetch logs: **Command:**

   ```bash
   kubectl apply -f busybox.yaml
   kubectl logs counter
   ```

3. Retrieve the last five lines of logs: **Command:**

   ```bash
   kubectl logs counter --tail=5
   ```

#### Step 3: Advanced Log Options

1. Fetch logs from all containers in a namespace: **Command:**

   ```bash
   kubectl logs counter --all-containers
   ```

2. Fetch logs from a specific time range: **Command:**

   ```bash
   kubectl logs counter --since=<timespan>
   ```

   Example: To retrieve logs from the last hour:

   ```bash
   kubectl logs counter --since=1h
   ```

### Things to Check

- Are logs being generated by the pod/container?
- Is the `kubectl logs` command correctly targeting the pod or namespace?
- Are appropriate log filters, such as `--tail` or `--since`, being applied?

### Tools and Prerequisites

- Tools: `kubectl`, `kubeadm`, `kubelet`, `containerd`.
- Prerequisite: A functioning Kubernetes cluster.

By following these steps, you can effectively monitor and troubleshoot application logs in Kubernetes, ensuring better visibility into system behavior and application performance.

---

## Section 3: Understanding Cluster and Node Logs

### Areas to Troubleshoot

- Control-plane component logs.
- Worker node logs.
- Logs from services like the API server, controller manager, etcd, and kubelet.

### Possible Scenarios

- Control-plane components are unresponsive or showing errors.
- Worker nodes are not functioning as expected.
- Logs are inaccessible or incomplete.

### Steps and Commands to Troubleshoot

#### Step 1: View Control-Plane Component Logs
1. Navigate to the logs directory:
   **Command:**
   ```bash
   cd /var/log/pods
   ls
   ```
   Lists all the components and their directories.

2. Navigate to the API server logs:
   **Command:**
   ```bash
   cd kube-system_kube-apiserver-<master-node>_<unique-id>/kube-apiserver
   ```

3. View the latest log file:
   **Command:**
   ```bash
   ls -la
   sudo cat 0.log
   ```

#### Step 2: View Controller Manager Logs
1. Navigate to the controller manager logs directory:
   **Command:**
   ```bash
   cd kube-system_kube-controller-manager-<master-node>_<unique-id>/kube-controller-manager
   ```

2. View the logs:
   **Command:**
   ```bash
   ls -la
   sudo cat 0.log
   ```

#### Step 3: View etcd Logs
1. Navigate to the etcd logs directory:
   **Command:**
   ```bash
   cd kube-system_etcd-<master-node>_<unique-id>/etcd
   ```

2. View the logs:
   **Command:**
   ```bash
   ls -la
   sudo cat 0.log
   ```

#### Step 4: View Worker Node Logs
1. View the kubelet service logs:
   **Command:**
   ```bash
   sudo journalctl -xu kubelet -n
   ```
   Press `q` to exit the log viewer.

2. View pod logs on the worker node:
   **Command:**
   ```bash
   cd /var/log/pods/
   ls
   ```
   Navigate into specific pod directories to view logs.

### Things to Check

- Are control-plane component logs accessible and free of errors?
- Are kubelet service logs showing any issues on worker nodes?
- Is the logging directory structure consistent across nodes?

### Tools and Prerequisites

- Tools: `kubeadm`, `kubectl`, `kubelet`, `containerd`.
- Prerequisite: A functioning Kubernetes cluster.

By following these steps, you can inspect and troubleshoot control-plane and worker node logs, ensuring smooth cluster operations.

---

## Section 4: Troubleshooting Node Readiness

### Areas to Troubleshoot

- Node readiness and status.
- Kubelet service issues on worker nodes.
- Node transitioning between `Not Ready` and `Ready`.

### Possible Scenarios

- Worker node status shows `Not Ready`.
- Kubelet service on a worker node is inactive or malfunctioning.
- Issues after restarting or disabling a worker node.

### Steps and Commands to Troubleshoot

#### Step 1: Check the Node Status on the Master Node
1. View the status of all nodes in the cluster:
   **Command:**
   ```bash
   kubectl get nodes
   ```

2. Identify the problematic worker node (e.g., `worker-node-2`) from the output.

#### Step 2: Disable the Worker Node and Diagnose
1. Stop the kubelet service on the worker node:
   **Command:**
   ```bash
   sudo service kubelet stop
   ```

2. Verify the kubelet service status:
   **Command:**
   ```bash
   sudo service kubelet status
   ```
   (Press `q` to exit the status viewer.)

3. Check the node's status from the master node after stopping the kubelet service:
   **Command:**
   ```bash
   kubectl get nodes
   ```
   The node status should show `Not Ready`.

4. Describe the node to diagnose the problem:
   **Command:**
   ```bash
   kubectl describe node worker-node-2.example.com
   ```

#### Step 3: Fix the Worker Node
1. Start the kubelet service on the worker node:
   **Command:**
   ```bash
   sudo systemctl start kubelet
   ```

2. Verify the kubelet service status:
   **Command:**
   ```bash
   sudo systemctl status kubelet
   ```
   (Press `q` to exit the status viewer.)

3. After a few minutes, recheck the node's status from the master node:
   **Command:**
   ```bash
   kubectl get nodes
   ```
   The node status should now display `Ready`.

### Things to Check

- Is the kubelet service running correctly on the worker node?
- Are there any errors in the output of `kubectl describe node`?
- Does the node transition back to `Ready` after restarting the kubelet service?

### Tools and Prerequisites

- Tools: `kubeadm`, `kubectl`, `kubelet`, `containerd`.
- Prerequisite: A functioning Kubernetes cluster.

By following these steps, you can successfully diagnose and resolve issues causing a worker node to transition from `Not Ready` to `Ready`.

---


## Section 5: Understanding Container Logs

In this section, you will learn how to check and access container logs using `crictl` commands. These logs are crucial for troubleshooting and understanding container behavior.

#### Steps to Check Container Logs:

1. **Navigate to Worker Node:**
   - Log in to the worker-node-2 in the LMS dashboard.

2. **Fetch the Container ID:**
   - Use the following command to fetch the container ID:
     ```bash
     sudo crictl ps -a
     ```

3. **Access and View Container Logs:**
   - To view the logs of a specific container, use the following command:
     ```bash
     sudo crictl logs <container_id>
     ```
     Replace `<container_id>` with the actual container ID from the previous command.

4. **Retrieve the Latest Log Entry:**
   - If you need to retrieve the most recent log entry, use the following command:
     ```bash
     sudo crictl logs --tail=1 <container_id>
     ```
     This will return the latest log entry for the specified container.

By following these steps, you have successfully demonstrated how to use `crictl` commands to monitor container logs and troubleshoot container-related issues.

---

## Section 6: Analyzing Pod Logs and Troubleshooting Pod Issues

In this section, you will analyze pod logs, troubleshoot common pod and container issues, and explore scenarios such as tainting nodes, incorrect image names, and various pod/container status problems.

---

#### 6.1 Configure and Verify Nginx Deployment

Follow the steps to configure and deploy an Nginx application in Kubernetes.

1. **Create a Configuration File for Nginx Deployment:**
   - Create a file `nginx.yaml` for your Nginx deployment:
     ```bash
     vi nginx.yaml
     ```

   2. **Insert the Nginx Deployment Configuration:**
      Insert the following YAML configuration:
      ```yaml
      apiVersion: apps/v1
      kind: Deployment
      metadata:
        labels:
          app: nginx
        name: nginx
      spec:
        replicas: 1
        selector:
          matchLabels:
            app: nginx
        template:
          metadata:
            labels:
              app: nginx
          spec:
            containers:
            - image: nginx
              name: nginx
      ```

   3. **Create the Nginx Deployment:**
      ```bash
      kubectl create -f nginx.yaml
      ```

   4. **Verify the Deployment and Pod Status:**
      ```bash
      kubectl get deployments
      kubectl get pods
      ```

   5. **View the Logs of the Nginx Pod:**
      ```bash
      kubectl logs nginx-7854ff8877-mvrtr
      ```

---

#### 6.2 Tainting Worker Nodes and Deployment Failures

1. **Taint the Worker Node:**
   - Taint the worker node to prevent any pods from being scheduled on it:
     ```bash
     kubectl taint nodes worker-node-1 key=value:NoSchedule
     ```

2. **Check Deployment Status:**
   - After tainting the node, check the status of the deployment and pods:
     ```bash
     kubectl get deployments
     kubectl get pods
     ```
     **Expected Outcome:** The pod(s) will not be scheduled, and the deployment will not reach the "READY" state.

3. **Troubleshooting the Issue:**
   - To resolve the issue, you can either:
     - Remove the taint from the node:
       ```bash
       kubectl taint nodes worker-node-1 key=value:NoSchedule-
       ```
     - Or, you can add a toleration in your Nginx deployment YAML to allow the pod to be scheduled on tainted nodes:
       ```yaml
       spec:
         template:
           spec:
             tolerations:
             - key: "key"
               operator: "Equal"
               value: "value"
               effect: "NoSchedule"
       ```

---

#### 6.3 Troubleshooting Incorrect Image Names

1. **Use an Incorrect Image Name:**
   - Modify your `nginx.yaml` to use a non-existent image (e.g., `nginx:wrongtag`):
     ```yaml
     containers:
     - image: nginx:wrongtag
       name: nginx
     ```

2. **Check the Pod Status:**
   - After applying the deployment with the incorrect image, check the pod status:
     ```bash
     kubectl get pods
     ```

   **Expected Outcome:** The pod will be stuck in `ImagePullBackOff` or `ErrImagePull` status.

3. **Troubleshoot the Image Pull Error:**
   - To troubleshoot, you can describe the pod to get more information:
     ```bash
     kubectl describe pod nginx-7854ff8877-mvrtr
     ```
     Look for error messages related to the image pull. In this case, it will indicate that the image does not exist.

4. **Fix the Issue:**
   - Update the deployment YAML to use the correct image tag:
     ```yaml
     containers:
     - image: nginx:latest
       name: nginx
     ```

   - Apply the changes:
     ```bash
     kubectl apply -f nginx.yaml
     ```

   - Verify the pod status:
     ```bash
     kubectl get pods
     ```

---

#### 6.4 Pod and Container Status Issues and Fixes

Here are some common pod and container status issues you may encounter, along with troubleshooting steps and fixes.

1. **Pod Status: CrashLoopBackOff**
   - **Cause:** The container within the pod repeatedly crashes (often due to application errors).
   - **Troubleshooting:**
     ```bash
     kubectl describe pod <pod_name>
     kubectl logs <pod_name>
     ```
     - Look for error messages in the logs and investigate the container's behavior.
   - **Fix:** Modify the deployment YAML or the container configuration to fix the application errors. You might need to adjust resource limits, environment variables, or code.

2. **Pod Status: Pending**
   - **Cause:** The pod cannot be scheduled because there are not enough resources available.
   - **Troubleshooting:**
     ```bash
     kubectl describe pod <pod_name>
     ```
     - Check the events section for resource allocation issues.
   - **Fix:** Ensure that the node has enough resources (CPU, memory) or scale up your cluster if necessary.

3. **Pod Status: Terminating**
   - **Cause:** The pod is stuck in the `Terminating` state due to an issue with the deletion process (e.g., finalizers not completing).
   - **Troubleshooting:**
     ```bash
     kubectl get pod <pod_name> -o yaml
     ```
     - Check for the `finalizers` field and any associated issues.
   - **Fix:** Force delete the pod if necessary:
     ```bash
     kubectl delete pod <pod_name> --force --grace-period=0
     ```

4. **Container Status: Waiting (Reason: ContainerCreating)**
   - **Cause:** The container is waiting for necessary resources or dependencies.
   - **Troubleshooting:**
     ```bash
     kubectl describe pod <pod_name>
     ```
     - Check the events section for more information on why the container is stuck in this state.
   - **Fix:** Ensure the required resources (e.g., images, volumes) are available and accessible.

5. **Container Status: Running (but Application is Not Responding)**
   - **Cause:** The container is running, but the application inside it is not behaving as expected (e.g., not starting, crashing).
   - **Troubleshooting:**
     ```bash
     kubectl logs <pod_name> -c <container_name>
     kubectl exec -it <pod_name> -- /bin/bash
     ```
     - Use the logs and interactive shell to investigate the application inside the container.
   - **Fix:** Modify the application configuration, fix any application-level issues, or redeploy the pod.

---

By following these steps, you can troubleshoot various pod and container issues, including node tainting, incorrect image names, and common status problems, ensuring your Kubernetes deployments run smoothly.

---
Here is the revised **Section 7: Understanding Application Troubleshooting** with all instances of "k8slearning" replaced with "ckacourse":

---

## Section 7: Understanding Application Troubleshooting

In this section, you will learn how to set up a Kubernetes application pod, diagnose potential issues, and implement corrections to ensure successful deployment and smooth operation of the application.

---

#### 7.1 Setup and Diagnose the Application Pod

This section outlines the steps to create a pod, verify its state, diagnose issues, and apply fixes.

1. **Create the Application Pod Deployment:**

   1.1 **Create the `issue-pod.yaml` File:**
   - Draft the following YAML code to create a pod and save it in a file called `issue-pod.yaml`:
     ```bash
     vi issue-pod.yaml
     ```
     ```yaml
     apiVersion: v1
     kind: Pod
     metadata:
       name: openshift
       labels:
         Podlabel: ckacourse
     spec:
       containers:
       - name: mycontainer
         image: docker.io/openshift
         ports:
         - containerPort: 80
     ```
     **Objective:** To create a Kubernetes pod for troubleshooting application issues.

2. **Deploy the Pod:**

   1.2 **Create the Pod:**
   - Deploy the `issue-pod.yaml` file to the Kubernetes cluster:
     ```bash
     kubectl create -f issue-pod.yaml
     ```

3. **Verify the Pod Status:**

   1.3 **Check the Pod Status:**
   - To verify if the pod is running correctly, use the following command:
     ```bash
     kubectl get pods
     ```
     **Expected Outcome:** The pod may be stuck in a `Pending`, `CrashLoopBackOff`, or `ContainerCreating` state, indicating an issue.

4. **Retrieve Events and Pod Details:**

   1.4 **Check Events for Errors:**
   - To diagnose any cluster-wide or pod-specific issues, view the events:
     ```bash
     kubectl get events
     ```

   1.5 **Describe the Pod:**
   - To get detailed information about the pod and potential error messages, use:
     ```bash
     kubectl describe pod openshift
     ```

   **Expected Outcome:** You may encounter errors in the `Events` section, such as image pull errors, insufficient resources, or other configuration issues.

---

#### 7.2 Troubleshooting the Application Pod

Once you have diagnosed the issue with the pod, the next step is to troubleshoot and resolve it.

1. **Change the Container Image:**

   1.6 **Edit the Pod's Service Image:**
   - If the issue is related to an incorrect image, edit the pod definition to change the container image. For example, change the image from `docker.io/openshift` to `openshift/helloopenshift`:
     ```bash
     kubectl edit pod openshift
     ```
     - This will open the pod configuration in your default editor. Update the image field as follows:
       ```yaml
       image: openshift/helloopenshift
       ```

2. **Verify Changes to the Pod:**

   1.7 **Confirm the Changes:**
   - After editing the pod, check the pod status to confirm that it is now running:
     ```bash
     kubectl get pods
     ```
     **Expected Outcome:** The pod should now be in the `Running` state if the issue has been resolved.

---

#### 7.3 Common Pod Troubleshooting Scenarios

Here are some common pod-related issues you may encounter, along with troubleshooting steps and fixes.

1. **Pod Status: CrashLoopBackOff**
   - **Cause:** The container inside the pod repeatedly crashes, often due to an application issue (e.g., missing dependencies, incorrect configurations).
   - **Troubleshooting:**
     ```bash
     kubectl describe pod openshift
     kubectl logs openshift
     ```
     - Look for errors in the logs and the `Events` section of the description.
   - **Fix:** Modify the container's configuration, fix the application issue, or update the container image.

2. **Pod Status: ImagePullBackOff or ErrImagePull**
   - **Cause:** The container image is either incorrect or unavailable.
   - **Troubleshooting:**
     ```bash
     kubectl describe pod openshift
     ```
     - Look for error messages related to the image pull.
   - **Fix:** Ensure the correct image name and tag are used in the pod configuration. Update the pod definition if needed:
     ```bash
     kubectl edit pod openshift
     ```

3. **Pod Status: Pending**
   - **Cause:** The pod cannot be scheduled due to insufficient resources or other node issues.
   - **Troubleshooting:**
     ```bash
     kubectl describe pod openshift
     kubectl get nodes
     ```
     - Check for resource allocation issues (e.g., memory, CPU) in the pod description and node status.
   - **Fix:** Adjust the resource requests and limits in the pod configuration, or scale the cluster to accommodate the pod.

4. **Pod Status: Terminating**
   - **Cause:** The pod is stuck in the `Terminating` state due to issues with resource cleanup or finalizer blocks.
   - **Troubleshooting:**
     ```bash
     kubectl get pod openshift -o yaml
     ```
     - Look for any hanging finalizer blocks preventing the pod from terminating.
   - **Fix:** Force delete the pod if necessary:
     ```bash
     kubectl delete pod openshift --force --grace-period=0
     ```

5. **Container Status: Waiting (Reason: ContainerCreating)**
   - **Cause:** The container is waiting for necessary resources (e.g., storage or network connectivity) or dependencies.
   - **Troubleshooting:**
     ```bash
     kubectl describe pod openshift
     ```
     - Check for any missing resources or dependencies in the `Events` section.
   - **Fix:** Ensure that the required resources (such as persistent volumes or network configurations) are available.

---

#### 7.4 Additional Troubleshooting Tools

1. **Use `kubectl logs -f` to Follow Logs in Real-Time:**
   - If your pod is running but the application inside it is not responding, follow the logs to monitor its output:
     ```bash
     kubectl logs -f openshift
     ```

2. **Use `kubectl exec` to Access the Container:**
   - To further diagnose an issue, you can access the container and interact with it:
     ```bash
     kubectl exec -it openshift -- /bin/bash
     ```
     This allows you to troubleshoot the application from inside the pod.

By following these steps, you will be able to set up a Kubernetes pod, diagnose any issues, and apply fixes to resolve problems that may arise during deployment. These troubleshooting techniques are essential for ensuring that your Kubernetes applications run smoothly.

---

## Section 8: Handling Component Failure Threshold

In this section, you will learn how to check the health of your Kubernetes cluster, including the nodes and overall cluster health status, and how to diagnose issues that may arise due to component failures.

---

#### 8.1 Check the Cluster Health Information

This section outlines the steps to gather information about the health of the cluster, including nodes and configuration.

1. **Check the Nodes in the Cluster:**

   1.1 **View Cluster Nodes:**
   - To get detailed information about the nodes in the cluster, execute the following command:
     ```bash
     kubectl get nodes
     ```
     **Objective:** To view the list of nodes in the cluster, their status, and health. This provides an overview of the cluster's node-level health.

   **Expected Outcome:**
   - The command should display the nodes along with their status (e.g., `Ready`, `NotReady`), version, and other relevant details.
   
   Example output:
   ```bash
   NAME              STATUS   ROLES    AGE   VERSION
   worker-node-1     Ready    <none>   5d    v1.20.0
   worker-node-2     NotReady <none>   5d    v1.20.0
   master-node-1     Ready    master   5d    v1.20.0
   ```

2. **Dump Cluster Information and Check Health:**

   1.2 **Generate and View Cluster Health Dump:**
   - To get a comprehensive collection of diagnostic information about the cluster's health, use the following commands:
     ```bash
     kubectl cluster-info dump > dump.json
     vi dump.json
     ```
     **Objective:** To gather detailed cluster configuration, resource usage, and status in a JSON file for further analysis.

   **Expected Outcome:**
   - The `dump.json` file contains a wealth of information, including details about nodes, pods, namespaces, and cluster components, which can be used for diagnosing potential failures.

   Example:
   - The contents of `dump.json` will include details like:
     - Cluster configuration
     - Node and pod status
     - Component health (e.g., API server, controller manager, scheduler)
   
   **Tip:** Use `vi` or any text editor to search through the file for any error or warning messages regarding component health.

3. **Interpret Cluster Health Information:**

   - After obtaining the cluster dump, you may encounter different failure scenarios:
     - **Component Failure:** If the dump contains error logs or `NotReady` status for critical components (e.g., API server, controller manager), further investigation is needed.
     - **Node Failures:** Nodes marked as `NotReady` might indicate issues such as resource exhaustion, network partitioning, or configuration issues.

4. **Addressing Node Failures:**

   - If a node is in the `NotReady` state, use the following to investigate further:
     ```bash
     kubectl describe node <node-name>
     ```
     This command provides detailed information on the node’s condition, including events that may indicate why it is not in a `Ready` state.

By following these steps, you can successfully gather diagnostic information about your Kubernetes cluster, enabling you to identify and resolve issues related to node health, component failures, or configuration errors. Regularly checking cluster health is essential for maintaining a highly available and reliable Kubernetes environment.

---

## Section 9: Troubleshooting Networking Issues

In this section, you will learn how to troubleshoot networking issues by setting up an `httpd` pod, creating an `httpd` service, checking pod labels, and testing the service connectivity.

---

#### 9.1 Create an HTTPD Pod

1. **Install the Metrics API:**
   - To begin troubleshooting networking issues, you need to install the metrics API:
     ```bash
     kubectl apply -f https://github.com/kubernetes-sigs/metricsserver/releases/latest/download/components.yaml
     ```

   **Objective:** Set up the necessary components to monitor and troubleshoot pod networking in the cluster.

2. **Create the HTTPD Pod:**
   1.2 Create a YAML file for the `httpd-pod` with the following content:
   ```bash
   vim network-issue.yaml
   ```
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: httpd-pod
     labels:
       mycka: ckacourse-network-1
   spec:
     containers:
     - name: mycontainer
       image: docker.io/httpd
       ports:
       - containerPort: 80
   ```

   1.3 Execute the following command to create the pod:
   ```bash
   kubectl create -f network-issue.yaml
   ```

   **Expected Outcome:** The pod should be created and running. Check the pod status using:
   ```bash
   kubectl get pods
   ```

---

#### 9.2 Create an HTTPD Service

1. **Create the HTTPD Service:**
   2.1 Create a YAML file for the `httpd` service:
   ```bash
   vi network-issue-svc.yaml
   ```
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: httpd-service
   spec:
     selector:
       mycka: ckacourse-network-1
     ports:
     - protocol: TCP
       port: 18080
       targetPort: 80
   ```

   2.2 Execute the following command to create the service:
   ```bash
   kubectl create -f network-issue-svc.yaml
   ```

   **Expected Outcome:** The service should be created and accessible. Check the service status:
   ```bash
   kubectl get svc
   ```

---

#### 9.3 Check Labels for All Pods

1. **Check Pod Labels:**
   3.1 To view the labels for all pods, run the following command:
   ```bash
   kubectl get pods --show-labels
   ```

2. **Get Endpoints:**
   3.2 To check the service endpoints, execute:
   ```bash
   kubectl get svc -o wide
   kubectl get endpoints
   ```

3. **Verify Service Connectivity:**
   3.3 Use the following command to verify if the service is responding correctly. Replace `172.16.232.199` with your cluster's `httpd-service` cluster IP:
   ```bash
   curl 172.16.232.199:80
   ```

4. **Delete the Service:**
   3.4 Delete the `httpd-service`:
   ```bash
   kubectl get svc
   kubectl delete svc httpd-service
   ```

---

#### 9.4 Modify and Create a New Service

1. **Modify Service YAML:**
   3.5 Edit the `network-issue-svc.yaml` file to use a different network name:
   ```bash
   vi network-issue-svc.yaml
   ```
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: httpd-service
   spec:
     selector:
       mycka: ckacourse-network-2
     ports:
     - protocol: TCP
       port: 18080
       targetPort: 80
   ```

2. **Create the Modified Service:**
   3.6 Create the new service:
   ```bash
   kubectl create -f network-issue-svc.yaml
   ```

3. **Check the Pod Labels Again:**
   3.7 List the pods with their labels:
   ```bash
   kubectl get pods --show-labels
   ```

4. **Retrieve the Cluster IP and Endpoints:**
   3.8 Retrieve the service's cluster IP and endpoints:
   ```bash
   kubectl get svc -o wide
   kubectl get endpoints
   ```

5. **Verify Service Connectivity:**
   3.9 Access the service again using `curl`:
   ```bash
   curl 172.16.232.199:8080
   ```

---

By following these steps, you will have successfully set up an `httpd` pod and service, performed troubleshooting steps, and verified the network connectivity within your Kubernetes environment.

---

## Additional Reading

For more in-depth understanding, you can refer to the following resources:

- [Kubernetes Documentation - Troubleshooting](https://kubernetes.io/docs/tasks/debug/debug-cluster/)
- [Kubernetes Networking Concepts](https://kubernetes.io/docs/concepts/services-networking/)
- [CKA Exam Preparation Guide](https://www.cncf.io/certification/certified-kubernetes-administrator/)

---

## Importance of Troubleshooting Skills

In a **job** or **interview** scenario, troubleshooting skills are highly valued as they demonstrate your ability to solve complex problems under pressure. For example, during an interview for a Kubernetes-related position, employers will often ask you to troubleshoot a Kubernetes cluster or application failure. Having hands-on experience in diagnosing and fixing issues with networking, pods, containers, and services will set you apart.

In the **CKA exam**, troubleshooting is a key component. You'll be asked to resolve cluster issues, network failures, and pod-related problems. Having practiced these scenarios will not only help you pass the exam but also prepare you for real-world challenges as a Kubernetes administrator.


By regularly practicing troubleshooting scenarios, you can ensure you're well-prepared for both the CKA exam and practical job situations.

---

