### **Azure Kubernetes Service (AKS) Lab Tutorial - Part 3: Using Ingress with AKS (Updated with Distinguishable Sample Pages)**

---

### **1. Introduction to Ingress in AKS**

Ingress is an API object in Kubernetes that manages external access to services within a cluster, typically HTTP. It provides routing rules to manage how external traffic is directed to your services, allowing advanced features like load balancing, SSL termination, and URL path-based routing.

In AKS, the **Ingress Controller** manages the ingress traffic. One of the most commonly used controllers is the **NGINX Ingress Controller**.

In this tutorial, we will:
- Install the NGINX Ingress Controller using Helm.
- Deploy a sample website using multi-path routing via Ingress, with different HTML content for each path.
- Verify that the routing works as expected and we can differentiate the pages.

---

### **2. Installing NGINX Ingress Controller Using Helm**

#### **Step 1: Install Helm**

Before we can use Helm to install the Ingress Controller, we need to install Helm if it's not already installed on your system. If you don't have it, follow these steps:

```bash
# Install Helm on your local machine (macOS example)
brew install helm
```

For other operating systems, check the [Helm installation guide](https://helm.sh/docs/intro/install/).

#### **Step 2: Add the NGINX Ingress Controller Helm Chart**

To install the NGINX Ingress Controller, we first need to add the Helm chart repository:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

#### **Step 3: Install the NGINX Ingress Controller**

Now, use Helm to install the NGINX Ingress Controller in your AKS cluster:

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace kube-system \
  --create-namespace
```

This will install the NGINX Ingress Controller into the `kube-system` namespace. It will also create all the necessary resources, including the required deployments and services for NGINX.

#### **Step 4: Verify the Ingress Controller Installation**

After installation, verify that the NGINX Ingress Controller pods are running:

```bash
kubectl get pods -n kube-system -l app.kubernetes.io/name=ingress-nginx
```

You should see something like this:

```bash
NAME                                        READY   STATUS    RESTARTS   AGE
ingress-nginx-controller-7c9b89f57d-7gfm8   1/1     Running   0          1m
ingress-nginx-controller-7c9b89f57d-mk4lz   1/1     Running   0          1m
```

You can also verify that the NGINX service is running by checking the services:

```bash
kubectl get svc -n kube-system -l app.kubernetes.io/name=ingress-nginx
```

The service should be of type `LoadBalancer`, and you'll get an external IP once it is assigned by Azure.

---

### **3. Deploying a Sample Website with Multi-Path Routing (with Distinguishable HTML Pages)**

In this step, we'll deploy two different web applications (website-1 and website-2) that will serve distinguishable HTML pages for each path.

#### **Step 1: Create Namespace for the Website**

Create a new namespace where we will deploy the website resources:

**website-namespace.yaml**:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: website
```

Apply the namespace:

```bash
kubectl apply -f website-namespace.yaml
```

#### **Step 2: Deploy Two Sample Web Applications (with Different HTML Pages)**

We'll create two different sample websites using NGINX as the web server, with distinguishable HTML content.

**nginx-deployment-1.yaml** (Website 1):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: website-1
  namespace: website
spec:
  replicas: 1
  selector:
    matchLabels:
      app: website-1
  template:
    metadata:
      labels:
        app: website-1
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
        volumeMounts:
        - mountPath: /usr/share/nginx/html/index.html
          name: website-1-html
          subPath: index.html
      volumes:
      - name: website-1-html
        configMap:
          name: website-1-html
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: website-1-html
  namespace: website
data:
  index.html: |
    <html>
      <head><title>Website 1</title></head>
      <body><h1>Welcome to Website 1</h1><p>This is the page for /site1 path.</p></body>
    </html>
```

**nginx-deployment-2.yaml** (Website 2):
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: website-2
  namespace: website
spec:
  replicas: 1
  selector:
    matchLabels:
      app: website-2
  template:
    metadata:
      labels:
        app: website-2
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80
        volumeMounts:
        - mountPath: /usr/share/nginx/html/index.html
          name: website-2-html
          subPath: index.html
      volumes:
      - name: website-2-html
        configMap:
          name: website-2-html
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: website-2-html
  namespace: website
data:
  index.html: |
    <html>
      <head><title>Website 2</title></head>
      <body><h1>Welcome to Website 2</h1><p>This is the page for /site2 path.</p></body>
    </html>
```

Apply the deployments and config maps:

```bash
kubectl apply -f nginx-deployment-1.yaml
kubectl apply -f nginx-deployment-2.yaml
```

#### **Step 3: Expose the Web Applications with Services**

Now, expose both NGINX deployments using ClusterIP services.

**nginx-service-1.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: website-1-service
  namespace: website
spec:
  selector:
    app: website-1
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

**nginx-service-2.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: website-2-service
  namespace: website
spec:
  selector:
    app: website-2
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

Apply the services:

```bash
kubectl apply -f nginx-service-1.yaml
kubectl apply -f nginx-service-2.yaml
```

#### **Step 4: Create Ingress Resource for Multi-Path Routing**

Now, create an Ingress resource to route traffic to these two services based on the URL path.

**website-ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: website-ingress
  namespace: website
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: <external-ip>   # Replace <external-ip> with the external IP or DNS name of your Ingress controller
    http:
      paths:
      - path: /site1
        pathType: Prefix
        backend:
          service:
            name: website-1-service
            port:
              number: 80
      - path: /site2
        pathType: Prefix
        backend:
          service:
            name: website-2-service
            port:
              number: 80
```

Make sure to replace `<external-ip>` with the external IP of your NGINX Ingress Controller.

Apply the Ingress resource:

```bash
kubectl apply -f website-ingress.yaml
```

---

### **4. Verifying the Multi-Path Routing**

Once the Ingress is applied, the NGINX Ingress Controller will route traffic based on the path defined in the `Ingress` resource.

1. Get the external IP address of the Ingress controller:

```bash
kubectl get svc -n kube-system -l app.kubernetes.io/name=ingress-nginx
```

2. Visit the following URLs to access the websites:
   - `http://<external-ip>/site1` will route to `website-1`, displaying "Welcome to Website 1" and a description of path `/site1`.
   - `http://<external-ip>/site2` will route to `website-2`, displaying "Welcome to Website 2" and a description of path `/site2`.

You should see different content for each path, confirming that the Ingress controller is routing correctly.

---

### **5. Important Notes for AKS Ingress**

- **NGINX Ingress Controller**: The NGINX Ingress Controller is a

 robust and widely used solution for managing ingress traffic in Kubernetes. In AKS, it works seamlessly with Azure’s load balancers and can manage both external and internal traffic.
  
- **Annotations**: The `nginx.ingress.kubernetes.io/rewrite-target` annotation is used to ensure that the traffic is correctly routed to the service without the path prefix. You can define other annotations like SSL support, rate limiting, etc.

- **DNS and External IP**: In a production environment, you would likely use a custom domain (via Azure DNS) rather than an external IP address. You can configure this in the Ingress resource.

- **Scaling**: The web applications we deployed are basic. However, you can scale them by increasing the number of replicas in the deployment YAML, and Kubernetes will automatically balance traffic to the new pods.

---

This concludes Part 3 of the AKS tutorial, where we explored how to use Ingress to route traffic to different services within your AKS cluster using multi-path routing and distinguishable HTML content for each path.
