# Deploying WordPress and MySQL on Kubernetes

## Introduction
WordPress is one of the most popular open-source content management systems (CMS) used for creating dynamic websites and blogs. It is highly customizable, easy to use, and widely supported by the developer community. 

MySQL, on the other hand, is a powerful open-source relational database management system. It is often used alongside WordPress to store website content such as posts, user data, and configurations.

In this tutorial, we will set up a WordPress site with a MySQL database on a Kubernetes lab cluster. By the end of this guide, you will understand the basics of deploying applications on Kubernetes and be able to verify your WordPress site.

### Prerequisites
Before starting, you should have:
1. A basic understanding of Kubernetes concepts like Deployments, Services, and Pods.
2. Access to a Kubernetes lab cluster.
3. The `kubectl` CLI tool installed and configured to interact with your lab cluster.

## Step-by-Step Deployment

### 1. MySQL Deployment
Let's start by deploying MySQL, which will serve as the database for WordPress. Below is the YAML configuration for the MySQL Deployment and Service.

#### MySQL Deployment (`mysql.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
  labels:
    app: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
      - name: mysql
        image: mysql:5.6
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: k8slearning
        - name: MYSQL_DATABASE
          value: database1
```

- **`replicas`**: Specifies the number of Pod replicas to maintain.
- **`image`**: Specifies the Docker image for MySQL version 5.6.
- **Environment variables**:
  - `MYSQL_ROOT_PASSWORD`: Sets the root password for MySQL. This password is crucial for administrative access to the database.
  - `MYSQL_DATABASE`: Creates a new database (`database1`) for WordPress to use.

#### MySQL Service (`mysql-service.yaml`)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: mysql
spec:
  type: NodePort
  selector:
    app: mysql
  ports:
    - protocol: TCP
      port: 3306
      targetPort: 3306
```

- **`type: NodePort`**: Exposes the MySQL service on a specific port to allow external access.
- **`port` and `targetPort`**: Specifies that traffic should be directed to port 3306, the default MySQL port.

### 2. WordPress Deployment
Next, we will deploy WordPress, which will connect to the MySQL database.

#### WordPress Deployment (`wordpress.yaml`)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wordpress
  labels:
    app: wordpress
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wordpress
  template:
    metadata:
      labels:
        app: wordpress
    spec:
      containers:
      - name: wordpress
        image: wordpress
        env:
        - name: WORDPRESS_DB_HOST
          value: mysql
        - name: WORDPRESS_DB_PASSWORD
          value: k8slearning
        - name: WORDPRESS_DB_USER
          value: root
        - name: WORDPRESS_DB_NAME
          value: database1
```

- **Environment variables**:
  - `WORDPRESS_DB_HOST`: Specifies the MySQL service name (`mysql`). This allows WordPress to locate the database within the Kubernetes cluster.
  - `WORDPRESS_DB_PASSWORD`: Uses the root password defined in the MySQL Deployment to authenticate database connections.
  - `WORDPRESS_DB_USER`: Sets the MySQL username (default: `root`) for database access.
  - `WORDPRESS_DB_NAME`: Specifies the database name (`database1`) that WordPress will use to store its data.

#### WordPress Service (`wordpress-service.yaml`)
```yaml
apiVersion: v1
kind: Service
metadata:
  name: wordpress-service
spec:
  type: NodePort
  selector:
    app: wordpress
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
```

- **`type: NodePort`**: Exposes the WordPress service on a port accessible externally.
- **`port` and `targetPort`**: Routes traffic to port 80, where WordPress serves its content.

### 3. Deploy the Resources
Apply the YAML files to your Kubernetes lab cluster:
```bash
kubectl apply -f mysql.yaml
kubectl apply -f mysql-service.yaml
kubectl apply -f wordpress.yaml
kubectl apply -f wordpress-service.yaml
```
Verify that the Pods and Services are running:
```bash
kubectl get pods
kubectl get svc
```

### 4. Access the WordPress Site
Once the WordPress and MySQL services are up and running, you can access the WordPress site via the `NodePort` assigned to the `wordpress-service`.

Find the NodePort:
```bash
kubectl get svc wordpress-service
```
Open your browser and navigate to `http://<NodeIP>:<NodePort>` to see the WordPress installation page.

### 5. Verify Connectivity
Ensure that WordPress can connect to the MySQL database:
1. Fill out the installation form on the WordPress setup page.
2. Use the database details provided in the YAML configurations.
3. Complete the WordPress installation and verify that the site is functional.

## Conclusion
Congratulations! You have successfully deployed a WordPress site with a MySQL database on your Kubernetes lab cluster. This tutorial demonstrated how to define Kubernetes resources, manage deployments, and expose services for external access. With these skills, you can explore further Kubernetes concepts and host more complex applications.

