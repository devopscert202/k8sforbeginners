# **Lab: Deploying a Flask Application with Redis in Kubernetes**

This tutorial guides you through deploying a Flask application integrated with Redis in a Kubernetes cluster. The Flask app will increment and display a counter stored in Redis.

---

## **Objective**
Deploy and verify a containerized Flask application integrated with Redis using Kubernetes resources.

---

## **Prerequisites**
1. A functional Kubernetes cluster (`kubeadm`, `kubectl`, `kubelet` installed).
2. Docker installed for building images.
3. A Docker Hub account for pushing images.

---

## **Step-by-Step Guide**

### **Step 1: Prepare the Flask Application**
1. Create a directory and navigate to it:
   ```bash
   mkdir redis_flask
   cd redis_flask
   ```

2. Create the Flask app file:
   ```bash
   nano app.py
   ```

   **Content of `app.py`:**
   ```python
   from flask import Flask
   from redis import Redis

   app = Flask(__name__)
   redis = Redis(host='redis', port=6379)

   @app.route('/')
   def hello():
       count = redis.incr('hits')
       return 'Hello from Docker! I have been seen {} times.\n'.format(count)

   if __name__ == "__main__":
       app.run(host="0.0.0.0", debug=True)
   ```

3. Create a `Dockerfile`:
   ```bash
   nano Dockerfile
   ```

   **Content of `Dockerfile`:**
   ```Dockerfile
   FROM python:3.4-alpine
   ADD . /code
   WORKDIR /code
   RUN pip install -r requirements.txt
   CMD ["python", "app.py"]
   ```

4. Create a `requirements.txt` file:
   ```bash
   nano requirements.txt
   ```

   **Content of `requirements.txt`:**
   ```
   flask
   redis
   ```

---

### **Step 2: Build and Push the Flask Image**
1. Build the Docker image:
   ```bash
   sudo docker build -t flask_image .
   ```

2. Tag the image:
   ```bash
   sudo docker tag flask_image:latest <your-docker-id>/flask-image:flask_image_for_redis
   ```

   Replace `<your-docker-id>` with your Docker Hub username.

3. Log in to Docker Hub:
   ```bash
   sudo docker login
   ```

4. Push the image to Docker Hub:
   ```bash
   sudo docker push <your-docker-id>/flask-image:flask_image_for_redis
   ```

---

### **Step 3: Create Redis and Flask Deployments**

#### **3.1 Create Redis Deployment**
1. Create the `redis.yaml` file:
   ```bash
   nano redis.yaml
   ```

   **Content of `redis.yaml`:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: redis
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: redis
     template:
       metadata:
         labels:
           app: redis
       spec:
         containers:
         - name: redis
           image: redis
   ```

2. Deploy Redis:
   ```bash
   kubectl create -f redis.yaml
   ```

---

#### **3.2 Create Flask Deployment**
1. Create the `flask.yaml` file:
   ```bash
   nano flask.yaml
   ```

   **Content of `flask.yaml`:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: flask
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: flask
     template:
       metadata:
         labels:
           app: flask
       spec:
         containers:
         - name: flask-image
           image: <your-docker-id>/flask-image:flask_image_for_redis
   ```

   Replace `<your-docker-id>` with your Docker Hub username.

2. Deploy Flask:
   ```bash
   kubectl create -f flask.yaml
   ```

---

### **Step 4: Create Services**

#### **4.1 Create Redis Service**
1. Create the `redis-svc.yaml` file:
   ```bash
   nano redis-svc.yaml
   ```

   **Content of `redis-svc.yaml`:**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: redis
   spec:
     ports:
     - port: 6379
       targetPort: 6379
     selector:
       app: redis
   ```

2. Deploy the Redis service:
   ```bash
   kubectl create -f redis-svc.yaml
   ```

---

#### **4.2 Create Flask Service**
1. Create the `flask-svc.yaml` file:
   ```bash
   nano flask-svc.yaml
   ```

   **Content of `flask-svc.yaml`:**
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: flask
   spec:
     ports:
     - port: 5000
       targetPort: 5000
     selector:
       app: flask
   ```

2. Deploy the Flask service:
   ```bash
   kubectl create -f flask-svc.yaml
   ```

---

### **Step 5: Verify the Deployment**

1. Verify the services:
   ```bash
   kubectl get svc
   ```

   Note the `ClusterIP` and `Port` of the Flask service.

2. Access the Flask application:
   ```bash
   curl <ClusterIP>:5000
   ```

   Replace `<ClusterIP>` with the IP address of the Flask service.

3. Verify the counter increments with each request.

---

### **Step 6: Clean Up**

If you want to delete the resources after testing:
```bash
kubectl delete -f redis.yaml
kubectl delete -f flask.yaml
kubectl delete -f redis-svc.yaml
kubectl delete -f flask-svc.yaml
```

---

By following this tutorial, you will successfully deploy a Flask application integrated with Redis on Kubernetes, demonstrating containerized application orchestration and service management.
