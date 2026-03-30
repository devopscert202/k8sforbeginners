### **Azure Kubernetes Service (AKS) Lab Tutorial - Part 2**

---

### **1. Introduction to Kubernetes Resources in AKS**

Kubernetes (K8s) provides a rich set of abstractions to manage containerized applications. When using **Azure Kubernetes Service (AKS)**, you can easily manage these resources through the Azure CLI (`kubectl`). These resources include:

- **Namespaces**: Logical partitions of cluster resources.
- **Deployments**: Manages the creation and scaling of application pods.
- **Services**: Provides networking solutions for applications, enabling them to communicate both internally and externally.
- **Load Balancers**: Manages traffic distribution across pods.

In this tutorial, we will explore how to create these resources with YAML files, starting from namespaces to deployments, services, and updates.

---

### **2. Creating Kubernetes Resources in AKS Using YAML Files**

#### **Step 1: Create a Namespace**

A namespace in Kubernetes helps you organize resources within the cluster. Create a YAML file for the namespace.

**namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: apache-namespace
```

To apply this namespace to your cluster, run the following command:

```bash
kubectl apply -f namespace.yaml
```

---

#### **Step 2: Create an Apache Deployment with 3 Replicas**

The following YAML file will define a deployment for the Apache web server with 3 replicas.

**apache-deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apache-server
  namespace: apache-namespace
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apache-server
  template:
    metadata:
      labels:
        app: apache-server
    spec:
      containers:
      - name: apache-server
        image: httpd:latest
        ports:
        - containerPort: 80
```

To create the deployment, use the following command:

```bash
kubectl apply -f apache-deployment.yaml
```

---

#### **Step 3: Expose Apache Deployment with a Load Balancer**

To expose the Apache deployment externally using a load balancer, create the following service YAML file:

**apache-service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: apache-service
  namespace: apache-namespace
spec:
  selector:
    app: apache-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer
```

To expose the service, apply this YAML file:

```bash
kubectl apply -f apache-service.yaml
```

---

#### **Step 4: Verify the Load Balancer IP**

After creating the service, check the external IP assigned to the load balancer:

```bash
kubectl get svc apache-service --namespace apache-namespace
```

**Expected Output**:
```bash
NAME              TYPE           CLUSTER-IP    EXTERNAL-IP    PORT(S)        AGE
apache-service    LoadBalancer   10.0.0.10     52.123.45.67   80:32387/TCP   1m
```

The `EXTERNAL-IP` column shows the IP address of the LoadBalancer. This IP can be used to access the Apache server externally.

---

### **3. How AKS Manages Load Balancers**

In AKS, the **Cloud Controller Manager** interacts with the Azure API to provision and manage Azure Load Balancers. When you create a `LoadBalancer` service, the Cloud Controller Manager automatically:

- Provisions an Azure Load Balancer.
- Associates the Load Balancer with the Kubernetes nodes.
- Assigns an external IP.
- Routes traffic to the pods based on their endpoints.

You can also create **Internal Load Balancers (ILB)** by modifying the service type to `LoadBalancer` and specifying `internal` in the annotations:

**apache-service-ilb.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: apache-service-ilb
  namespace: apache-namespace
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
spec:
  selector:
    app: apache-server
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
  type: LoadBalancer
```

To create the internal load balancer, run:

```bash
kubectl apply -f apache-service-ilb.yaml
```

---

### **4. Kubernetes Services Overview**

Kubernetes services provide different types of networking solutions. The following table summarizes the types of services available in Kubernetes:

| Service Type           | Description                                                                                  | Use Case                                  |
|------------------------|----------------------------------------------------------------------------------------------|-------------------------------------------|
| **ClusterIP**           | Exposes the service on a cluster-internal IP. Default service type.                           | Internal communication between services.  |
| **NodePort**            | Exposes the service on a static port on each node's IP.                                      | External access to services (but requires port management). |
| **LoadBalancer**        | Exposes the service externally via an external load balancer (automatically created in cloud environments like AKS). | External access via cloud-managed load balancer (default in AKS for public services). |
| **ExternalName**        | Maps a service to an external DNS name (outside the cluster).                                | Accessing services outside the cluster using DNS. |

---

### **5. Updating the Apache Deployment**

To update the Apache image in the deployment, Kubernetes allows for **rolling updates**. Here's how you can define an updated Apache deployment:

#### **Step 1: Update Apache Image**

To update the Apache image version in the deployment, modify the `image` field in the `apache-deployment.yaml` file.

**apache-deployment-update.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apache-server
  namespace: apache-namespace
spec:
  replicas: 3
  selector:
    matchLabels:
      app: apache-server
  template:
    metadata:
      labels:
        app: apache-server
    spec:
      containers:
      - name: apache-server
        image: httpd:2.4   # Updated image version
        ports:
        - containerPort: 80
```

To apply the update:

```bash
kubectl apply -f apache-deployment-update.yaml
```

#### **Step 2: Verify the Update**

Check the pods to ensure that they have been updated with the new image:

```bash
kubectl get pods --namespace apache-namespace
```

**Expected Output**: The pods should now show the updated image version.

---

### **6. Important AKS-Specific Notes**

- **Cloud Controller Manager**: AKS automatically uses the Cloud Controller Manager to manage cloud resources like load balancers, which simplifies the networking setup in the Azure environment.
- **Internal Load Balancers**: You can specify the creation of internal load balancers for secure, internal-only communication between services.
- **Scaling**: AKS supports easy scaling of workloads. You can scale the number of replicas in your deployment manually or automatically based on resource utilization.
- **Network Policies**: Azure Network Policies can be implemented to manage communication between pods and ensure secure access.
- **Managed Identity**: AKS provides built-in support for Azure Managed Identity, which can be used to grant Azure resources secure access to the cluster without needing to manage credentials manually.

---

This concludes Part 2, where we created various Kubernetes resources, deployed a service, and discussed how load balancing works in AKS. You can continue experimenting with other resource configurations, and scale your application as needed!
