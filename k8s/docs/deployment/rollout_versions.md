# **Lab Title**: Kubernetes Deployment with Rolling Updates and Rollbacks

---

## **Objective**
1. Build Docker images for two versions of a simple Apache-based application.
2. Push the images to a container registry.
3. Deploy the application to Kubernetes using the created images.
4. Perform a rollout to update the application from v1 to v2.
5. Demonstrate rollback to the previous version in case of issues.
6. Verify updates and rollbacks using the same service.

---

## **Prerequisites**
- Docker installed.
- Kubernetes cluster running.
- kubectl CLI installed and configured.
- A container registry account (e.g., Docker Hub).
- NodePort access for services.

---

## **Step 1: Build Docker Images**

### **1.1 Create the Application Files**

#### **Version 1 - HTML File**
Create a file named `index-v1.html` with the following content:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Apache HTML Index - Version 1</title>
</head>
<body>
    <h1>Welcome to Apache HTML Index - Version 1</h1>
</body>
</html>
```

#### **Version 2 - HTML File**
Create a file named `index-v2.html` with the following content:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Apache HTML Index - Version 2</title>
</head>
<body>
    <h1>Welcome to Apache HTML Index - Version 2</h1>
</body>
</html>
```

---

### **1.2 Create Dockerfiles**

#### **Dockerfile for Version 1**
Save the following content in a file named `Dockerfile-v1`:
```Dockerfile
FROM httpd:2.4
COPY index-v1.html /usr/local/apache2/htdocs/index.html
EXPOSE 80
```

#### **Dockerfile for Version 2**
Save the following content in a file named `Dockerfile-v2`:
```Dockerfile
FROM httpd:2.4
COPY index-v2.html /usr/local/apache2/htdocs/index.html
EXPOSE 80
```

---

### **1.3 Build the Images**

Run the following commands to build the Docker images:

```bash
docker build -t karthickponcloud/k8slabs:apache_v1 -f Dockerfile-v1 .
docker build -t karthickponcloud/k8slabs:apache_v2 -f Dockerfile-v2 .
```

---

### **1.4 Push the Images to a Registry**

1. Log in to Docker Hub. Here you use your login credentials to Docker Hub. Sign Up for free and create a repository like k8slabs.
   ```bash
   docker login
   ```

2. Push the images:
   ```bash
   docker push karthickponcloud/k8slabs:apache_v1
   docker push karthickponcloud/k8slabs:apache_v2
   ```

Verify the images are available in the registry.

---

## **Step 2: Deploy the Application**

### **2.1 Deployment YAML**

Create a file named `deployment.yaml` with the following content:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: apache-deployment
  labels:
    app: apache
spec:
  replicas: 2
  selector:
    matchLabels:
      app: apache
  template:
    metadata:
      labels:
        app: apache
    spec:
      containers:
      - name: apache-container
        image: karthickponcloud/k8slabs:apache_v1
        ports:
        - containerPort: 80
```

---

### **2.2 Service YAML**

Create a file named `service.yaml` with the following content:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: apache-service
spec:
  selector:
    app: apache
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: NodePort
```

---

### **2.3 Apply the Configuration**

1. Apply the deployment and service manifests:
   ```bash
   kubectl apply -f deployment.yaml
   kubectl apply -f service.yaml
   ```

2. Verify the resources:
   ```bash
   kubectl get deployments
   kubectl get pods
   kubectl get svc
   ```

3. Access the application:
   - Note the `NodePort` from `kubectl get svc`.
   - Open `http://<Node_IP>:<NodePort>` in a browser. You should see the **Version 1** page.

---

## **Step 3: Rollout Update**

### **3.1 Update Deployment**

Update the deployment image to **Version 2**:
```bash
kubectl set image deployment/apache-deployment apache-container=karthickponcloud/k8slabs:apache_v2 --record

```
Annotate the deployment as record option will be deprecated:
```bash
kubectl annotate deployment/apache-deployment  kubernetes.io/change-cause="Apache version 2"
```
---

### **3.2 Verify Rollout**

1. Check the rollout status:
   ```bash
   kubectl rollout status deployment/apache-deployment
   ```

2. Verify the pods:
   ```bash
   kubectl get pods
   ```

3. Refresh the browser at `http://<Node_IP>:<NodePort>`. You should see the **Version 2** page.

---

## **Step 4: Rollback**

### **4.1 Rollback to Previous Version**

If there’s an issue with Version 2, rollback to Version 1:
```bash
kubectl rollout undo deployment/apache-deployment
```

---

### **4.2 Verify Rollback**

1. Check the rollout status:
   ```bash
   kubectl rollout status deployment/apache-deployment
   ```

2. Verify the image:
   ```bash
   kubectl describe deployment apache-deployment | grep Image
   ```

3. Refresh the browser. You should see the **Version 1** page.

---

## **Step 5: Rollout History**

View the deployment history:
```bash
kubectl rollout history deployment/apache-deployment
```
You’ll see revisions and change details.

Alternatively, --to-revision parameter is used to undo the deployment and point a particular version from the history
```bash
kubectl rollout undo deployment/apache-deployment --to-revision=2
```

Above command will undo the deployment and directly going back to version 2 in the history. You may verify the deployment by accessing the service.

---

## **Step 6: Cleanup**

Remove the resources after completing the lab:
```bash
kubectl delete -f deployment.yaml
kubectl delete -f service.yaml
```

---

## **Conclusion**

1. **Built and pushed images** for Apache HTML pages (v1 and v2).
2. **Deployed the application** to Kubernetes with NodePort service.
3. **Performed a rolling update** to switch from v1 to v2 without downtime.
4. **Demonstrated rollback** to the previous version in case of issues.
5. Used **rollout history** to track changes.

This lab demonstrated how Kubernetes enables smooth application management with rolling updates and rollbacks.
