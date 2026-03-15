**Implementation Approach Guide for Multi-Tier WordPress and MySQL Application Deployment**

## Project Title: **Deploying a Multi-Tier WordPress and MySQL Application Using Kubernetes**

---

### **Description**

#### **Objectives**
To deploy a multi-tier WordPress and MySQL application using Kubernetes with specific configurations for user roles, storage, service verification, namespace restrictions, quota limits, and data management.

#### **Problem Statement and Motivation**

**Real-Time Scenario:**
An organization is tasked with deploying a newly developed application using WordPress and MySQL. The company leverages Kubernetes for its robust container orchestration capabilities. The task involves implementing specific configurations for storage, user roles, service verification, and data management.

**Industry Relevance:**
This project incorporates tools and techniques widely used in the industry:
- **kubeadm:** Simplifies Kubernetes cluster bootstrap.
- **kubectl:** Manages cluster resources and deployments.
- **kubelet:** Ensures container health on Kubernetes nodes.
- **Docker:** Facilitates application containerization and management.

---

### **Prerequisite Knowledge**
To complete this project successfully, ensure familiarity with:
1. Kubernetes core concepts: Pods, Deployments, Services, Secrets, ConfigMaps, Persistent Volumes (PVs), and Persistent Volume Claims (PVCs).
2. YAML configuration files for Kubernetes resources.
3. Kubernetes storage concepts (e.g., NFS setup and usage).
4. Basic Linux commands and Docker basics.
5. Kubernetes dashboard and RBAC.

---

### **Implementation Tasks**

#### **Task 1: Getting Started with Pods, Services, and Deployments**
##### Description:
Deploy the WordPress and MySQL application using Kubernetes Pods and Services.

##### Underlying Kubernetes Concepts:
- **Pods:** The smallest deployable units in Kubernetes.
- **Services:** Expose Pods to enable communication.
- **Deployments:** Manage Pod replicas and ensure consistent application state.

##### Steps:
1. Create a deployment for MySQL:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: mysql-deployment
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
           image: mysql:5.7
           env:
           - name: MYSQL_ROOT_PASSWORD
             value: "password"
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f mysql-deployment.yaml
   ```

2. Create a deployment for WordPress:
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: wordpress-deployment
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
           image: wordpress:latest
           env:
           - name: WORDPRESS_DB_HOST
             value: mysql-service
           - name: WORDPRESS_DB_USER
             value: "username"
           - name: WORDPRESS_DB_PASSWORD
             value: "password"
           - name: WORDPRESS_DB_NAME
             value: "database"
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f wordpress-deployment.yaml
   ```

#### **Task 2: Creating and Verifying the Service**
##### Description:
Expose the WordPress and MySQL deployments using Kubernetes Services.

##### Steps:
1. Create a Service for MySQL:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: mysql-service
   spec:
     selector:
       app: mysql
     ports:
       - protocol: TCP
         port: 3306
         targetPort: 3306
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f mysql-service.yaml
   ```

2. Create a Service for WordPress:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: wordpress-service
   spec:
     selector:
       app: wordpress
     ports:
       - protocol: TCP
         port: 80
         targetPort: 80
         nodePort: 30008
     type: NodePort
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f wordpress-service.yaml
   ```

3. Verify the Services:
   ```bash
   kubectl get services
   ```

4. Access the WordPress site using `http://<node-ip>:30008`.

#### **Task 3: Creating a Token and Working on the Dashboard**
##### Description:
Enable the Kubernetes dashboard and create a token for accessing it.

##### Steps:
1. Install the Kubernetes dashboard:
   ```bash
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.6.1/aio/deploy/recommended.yaml
   ```
2. Create a service account and token:
   ```yaml
   apiVersion: v1
   kind: ServiceAccount
   metadata:
     name: dashboard-admin-sa
     namespace: kube-system
   ---
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRoleBinding
   metadata:
     name: dashboard-admin-sa
   subjects:
   - kind: ServiceAccount
     name: dashboard-admin-sa
     namespace: kube-system
   roleRef:
     kind: ClusterRole
     name: cluster-admin
     apiGroup: rbac.authorization.k8s.io
   ```
   Apply the configuration and retrieve the token:
   ```bash
   kubectl apply -f dashboard-access.yaml
   kubectl -n kube-system describe secret $(kubectl -n kube-system get secret | grep dashboard-admin-sa | awk '{print $1}')
   ```

#### **Task 4: Deploying WordPress with MySQL Integration and Persistent Storage**
##### Description:
Replace the PHP deployment with a WordPress deployment. Configure WordPress to connect to the MySQL database by passing database credentials through environment variables. Ensure persistent storage for WordPress and verify that the application and storage are functional.

##### Underlying Kubernetes Concepts:
- **Persistent Volumes (PVs) and Persistent Volume Claims (PVCs):** Provide persistent storage for the WordPress application.
- **Secrets:** Securely manage sensitive data like database credentials.
- **Environment Variables:** Pass configuration data to the application.

##### Steps:

1. **Create the Persistent Volume and Claim for WordPress:**
   ```yaml
   apiVersion: v1
   kind: PersistentVolume
   metadata:
     name: wordpress-pv
   spec:
     capacity:
       storage: 10Gi
     accessModes:
       - ReadWriteOnce
     nfs:
       path: /path/to/wordpress
       server: <nfs-server-ip>
   ---
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: wordpress-pvc
   spec:
     accessModes:
       - ReadWriteOnce
     resources:
       requests:
         storage: 10Gi
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f wordpress-pv.yaml
   ```

2. **Create a Secret for MySQL Credentials:**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: mysql-secret
   type: Opaque
   data:
     mysql-root-password: cGFzc3dvcmQ= # Base64 encoded value of "password"
     mysql-user: dXNlcm5hbWU=          # Base64 encoded value of "username"
     mysql-password: cGFzc3dvcmQ=      # Base64 encoded value of "password"
     mysql-database: ZGF0YWJhc2U=      # Base64 encoded value of "database"
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f mysql-secret.yaml
   ```

3. **Create the WordPress Deployment:**
   ```yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
      name: wordpress
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
           image: wordpress:latest
           env:
           - name: WORDPRESS_DB_HOST
             value: mysql-service
           - name: WORDPRESS_DB_USER
             valueFrom:
               secretKeyRef:
                 name: mysql-secret
                 key: mysql-user
           - name: WORDPRESS_DB_PASSWORD
             valueFrom:
               secretKeyRef:
                 name: mysql-secret
                 key: mysql-password
           - name: WORDPRESS_DB_NAME
             valueFrom:
               secretKeyRef:
                 name: mysql-secret
                 key: mysql-database
           volumeMounts:
           - mountPath: /var/www/html
             name: wordpress-storage
         volumes:
         - name: wordpress-storage
           persistentVolumeClaim:
             claimName: wordpress-pvc
   ```
   Apply the configuration:
   ```bash
   kubectl apply -f wordpress-deployment.yaml
   ```

4. **Verify Persistent Storage and Application Functionality:**
   - Verify that the Persistent Volume Claim is bound:
     ```bash
     kubectl get pvc
     ```
   - Access the WordPress site using the exposed NodePort:
     ```bash
     http://<node-ip>:<node-port>
     ```
   - Create a test post in WordPress and ensure it persists even after restarting the Pod:
     ```bash
     kubectl delete pod <wordpress-pod-name>
     ```
     Reload the WordPress site and confirm the data is still present.

---

### **Summary**

This project demonstrates the deployment of a multi-tier application (WordPress with MySQL) on Kubernetes using robust features like Persistent Volumes, Secrets, and environment variables. It covers the implementation of various Kubernetes resources, including Deployments, Services, and Persistent Volume Claims. By completing this project, you gain practical experience with:

- Configuring Kubernetes clusters for real-world multi-tier applications.
- Managing sensitive data using Kubernetes Secrets.
- Ensuring data persistence using Persistent Volumes and Claims.
- Exposing services for external access and verifying application functionality.

Such projects enhance your ability to work as a Kubernetes Administrator and help organizations optimize their deployment strategies for modern containerized applications.


   
