# Lab 41: Deploying WordPress on Kubernetes - Multi-Tier Application

## Overview
In this comprehensive lab, you will deploy a production-like multi-tier WordPress application on Kubernetes. You'll learn how to configure a MySQL database backend, deploy WordPress frontend, secure sensitive data with Secrets, manage configuration with ConfigMaps, and enable service discovery between application tiers.

## Prerequisites
- A running Kubernetes cluster (Minikube, Kind, or any K8s cluster)
- `kubectl` CLI tool installed and configured
- Completion of Lab 09 (ConfigMaps) is recommended
- Basic understanding of Deployments, Services, ConfigMaps, and Secrets
- At least 2GB of available cluster memory

## Learning Objectives
By the end of this lab, you will be able to:
- Deploy a complete multi-tier application (frontend + backend)
- Configure MySQL database with ConfigMaps and Secrets
- Deploy WordPress and connect it to the MySQL backend
- Understand service discovery mechanisms in Kubernetes
- Secure sensitive data using Kubernetes Secrets
- Troubleshoot common multi-tier application issues
- Verify connectivity between application tiers
- Access and configure WordPress through a browser

---

## What is a Multi-Tier Application?

A **multi-tier application** separates different concerns into distinct layers:

1. **Presentation Tier (Frontend)**: WordPress - User interface and web server
2. **Data Tier (Backend)**: MySQL - Database for storing application data

**Benefits of Multi-Tier Architecture:**
- **Separation of Concerns**: Each tier has a specific responsibility
- **Scalability**: Scale frontend and backend independently
- **Maintainability**: Update one tier without affecting others
- **Security**: Database not directly exposed to the internet
- **Flexibility**: Replace components without complete rewrite

**Kubernetes Advantages for Multi-Tier Apps:**
- Automated service discovery through DNS
- Built-in load balancing
- Declarative configuration management
- Secrets management for sensitive data
- Easy horizontal scaling of tiers

---

## Architecture Overview

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  User Browser ──> NodePort Service (30000+)     │
│                           │                      │
│                           ▼                      │
│                   WordPress Pod                  │
│                  (Frontend Tier)                 │
│                           │                      │
│                           │ Service Discovery    │
│                           │ (mysql:3306)         │
│                           ▼                      │
│                    MySQL Service                 │
│                           │                      │
│                           ▼                      │
│                      MySQL Pod                   │
│                   (Database Tier)                │
│                           │                      │
│                           ▼                      │
│            [ConfigMap]  [Secret]                 │
│         (mysql-config) (mysql-secret)            │
│                                                  │
└──────────────────────────────────────────────────┘
```

**Key Communication Flow:**
1. User accesses WordPress via NodePort service
2. WordPress Pod connects to MySQL using service name "mysql"
3. Kubernetes DNS resolves "mysql" to MySQL Service ClusterIP
4. MySQL Service routes traffic to MySQL Pod
5. MySQL Pod uses ConfigMap for database name and Secret for password

---

## Part 1: Understanding the Application Components

Before deploying, let's understand each component in our multi-tier application.

### MySQL Backend Components

**1. MySQL ConfigMap** (`mysql-config.yaml`)
- Stores non-sensitive MySQL configuration
- Defines database name to create
- Can be updated without rebuilding images

**2. MySQL Secret** (`mysql-secret.yaml`)
- Stores sensitive MySQL root password
- Base64 encoded for basic obfuscation
- Should be protected with RBAC in production

**3. MySQL Deployment** (`mysql.yaml`)
- Runs MySQL 5.6 container
- Injects configuration from ConfigMap and Secret
- Single replica (not suitable for production HA)

**4. MySQL Service** (`mysql-service.yaml`)
- Exposes MySQL on port 3306
- Provides stable DNS name "mysql"
- Enables service discovery for WordPress

### WordPress Frontend Components

**1. WordPress ConfigMap** (`wordpress-configmap.yaml`)
- Stores WordPress database connection settings
- References MySQL service name for connectivity
- Defines database user and database name

**2. WordPress Secret** (`wordpress-secret.yaml`)
- Stores WordPress database password
- Must match MySQL root password
- Enables secure authentication

**3. WordPress Deployment** (`wordpress.yaml`)
- Runs WordPress container
- Injects configuration from ConfigMap and Secret
- Connects to MySQL using service discovery

**4. WordPress Service** (`wordpress-service.yaml`)
- Exposes WordPress on port 80
- NodePort type for external access
- Routes traffic to WordPress Pods

---

## Part 2: Deploying the MySQL Database (Backend Tier)

### Exercise 1: Create MySQL ConfigMap

#### Step 1: Review the MySQL ConfigMap

Navigate to the WordPress lab directory:
```bash
cd k8s/labs/workloads/wordpress
```

View the MySQL ConfigMap:
```bash
cat mysql-config.yaml
```

**Expected content:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-config
data:
  MYSQL_DATABASE: "database1"
```

**Understanding the configuration:**
- `MYSQL_DATABASE`: Name of the database MySQL will create on startup
- This database will be used by WordPress to store posts, users, and settings
- Non-sensitive information, suitable for ConfigMap

#### Step 2: Create the ConfigMap

```bash
kubectl apply -f mysql-config.yaml
```

Expected output:
```
configmap/mysql-config created
```

#### Step 3: Verify the ConfigMap

```bash
kubectl get configmap mysql-config
```

Expected output:
```
NAME           DATA   AGE
mysql-config   1      5s
```

View detailed ConfigMap information:
```bash
kubectl describe configmap mysql-config
```

**Why use ConfigMap here?**
- Database name is not sensitive
- Can be changed per environment (dev, staging, prod)
- Decouples configuration from container image
- Easy to update without rebuilding containers

---

### Exercise 2: Create MySQL Secret

#### Step 1: Review the MySQL Secret

View the MySQL Secret:
```bash
cat mysql-secret.yaml
```

**Expected content:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mysql-secret
type: Opaque
data:
  MYSQL_ROOT_PASSWORD: c2ltcGxpZGVhcm4=  # "k8slearning" base64 encoded
```

**Understanding the secret:**
- `MYSQL_ROOT_PASSWORD`: Root password for MySQL database
- Value is base64 encoded (not encrypted!)
- Type `Opaque` indicates arbitrary user-defined data

#### Step 2: Decode and Understand the Password

Decode the password to understand it:
```bash
echo "c2ltcGxpZGVhcm4=" | base64 --decode
```

Expected output:
```
k8slearning
```

**Important Security Notes:**
- Base64 is encoding, NOT encryption
- Anyone with access to the Secret can decode it
- In production, use additional security measures:
  - RBAC to restrict Secret access
  - Encryption at rest
  - External secret managers (HashiCorp Vault, AWS Secrets Manager)

#### Step 3: Create the Secret

```bash
kubectl apply -f mysql-secret.yaml
```

Expected output:
```
secret/mysql-secret created
```

#### Step 4: Verify the Secret

```bash
kubectl get secret mysql-secret
```

Expected output:
```
NAME           TYPE     DATA   AGE
mysql-secret   Opaque   1      5s
```

View secret details (note: data values are hidden by default):
```bash
kubectl describe secret mysql-secret
```

Expected output:
```
Name:         mysql-secret
Namespace:    default
Labels:       <none>
Annotations:  <none>

Type:  Opaque

Data
====
MYSQL_ROOT_PASSWORD:  11 bytes
```

**Alternative: Create Secret from Command Line**

You can also create secrets imperatively:
```bash
kubectl create secret generic mysql-secret-cli \
  --from-literal=MYSQL_ROOT_PASSWORD=k8slearning
```

Compare both methods:
```bash
kubectl get secret mysql-secret -o yaml
kubectl get secret mysql-secret-cli -o yaml
```

---

### Exercise 3: Deploy MySQL Database

#### Step 1: Review the MySQL Deployment

View the MySQL Deployment manifest:
```bash
cat mysql.yaml
```

**Expected content:**
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
        envFrom:
        - configMapRef:
            name: mysql-config
        env:
        - name: MYSQL_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mysql-secret
              key: MYSQL_ROOT_PASSWORD
```

**Understanding the manifest:**
- `envFrom.configMapRef`: Injects ALL keys from mysql-config as environment variables
- `env[].valueFrom.secretKeyRef`: Injects specific key from mysql-secret
- `MYSQL_DATABASE` comes from ConfigMap
- `MYSQL_ROOT_PASSWORD` comes from Secret
- Both are required for MySQL initialization

**Why this approach?**
- Separates sensitive (Secret) from non-sensitive (ConfigMap) data
- ConfigMap provides all non-sensitive environment variables at once
- Secret provides only specific sensitive values
- More secure and maintainable than hardcoding values

#### Step 2: Deploy MySQL

```bash
kubectl apply -f mysql.yaml
```

Expected output:
```
deployment.apps/mysql created
```

#### Step 3: Monitor MySQL Deployment

Watch the Pod creation:
```bash
kubectl get pods -l app=mysql --watch
```

Expected progression:
```
NAME                     READY   STATUS              RESTARTS   AGE
mysql-5d8f9c4b7d-x7k2p   0/1     ContainerCreating   0          5s
mysql-5d8f9c4b7d-x7k2p   1/1     Running             0          15s
```

Press `Ctrl+C` to stop watching.

#### Step 4: Verify MySQL is Running

Check deployment status:
```bash
kubectl get deployment mysql
```

Expected output:
```
NAME    READY   UP-TO-DATE   AVAILABLE   AGE
mysql   1/1     1            1           30s
```

Check Pod details:
```bash
kubectl get pod -l app=mysql
```

View Pod logs to confirm MySQL started successfully:
```bash
kubectl logs -l app=mysql
```

Look for these key log entries:
```
[Note] Server socket created on IP: '::'.
[Note] mysqld: ready for connections.
Version: '5.6.51'  socket: '/var/run/mysqld/mysqld.sock'  port: 3306
```

#### Step 5: Verify Environment Variables in MySQL Pod

Check that ConfigMap and Secret values were injected:
```bash
kubectl exec -l app=mysql -- env | grep MYSQL
```

Expected output:
```
MYSQL_DATABASE=database1
MYSQL_ROOT_PASSWORD=k8slearning
```

**What happened here?**
- `MYSQL_DATABASE` came from mysql-config ConfigMap
- `MYSQL_ROOT_PASSWORD` came from mysql-secret Secret
- MySQL container used these to initialize the database

---

### Exercise 4: Create MySQL Service

#### Step 1: Review the MySQL Service

View the service manifest:
```bash
cat mysql-service.yaml
```

**Expected content:**
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

**Understanding the service:**
- `name: mysql`: This is the DNS name other Pods will use
- `selector.app: mysql`: Routes traffic to Pods with this label
- `port: 3306`: Port the service listens on
- `targetPort: 3306`: Port on the Pod container
- `type: NodePort`: Exposes service outside the cluster (usually for testing)

**Service Discovery:**
- WordPress will connect to "mysql:3306"
- Kubernetes DNS resolves "mysql" to this service's ClusterIP
- Service load balances to healthy MySQL Pods

#### Step 2: Create the Service

```bash
kubectl apply -f mysql-service.yaml
```

Expected output:
```
service/mysql created
```

#### Step 3: Verify the Service

```bash
kubectl get service mysql
```

Expected output:
```
NAME    TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
mysql   NodePort   10.96.123.45    <none>        3306:32123/TCP   10s
```

**Understanding the output:**
- `CLUSTER-IP`: Internal IP (e.g., 10.96.123.45)
- `PORT(S)`: 3306 (internal) mapped to 32123 (NodePort)
- Other Pods use `mysql:3306` to connect

Get detailed service information:
```bash
kubectl describe service mysql
```

Expected output includes:
```
Name:                     mysql
Namespace:                default
Labels:                   <none>
Selector:                 app=mysql
Type:                     NodePort
IP:                       10.96.123.45
Port:                     <unset>  3306/TCP
TargetPort:               3306/TCP
NodePort:                 <unset>  32123/TCP
Endpoints:                172.17.0.4:3306
```

**Key field: Endpoints**
- Shows the actual Pod IP(s) the service routes to
- Should match your MySQL Pod IP
- Verify with: `kubectl get pod -l app=mysql -o wide`

#### Step 4: Test MySQL Service (Optional)

Test connectivity from within the cluster:
```bash
kubectl run mysql-client --image=mysql:5.6 -it --rm --restart=Never -- \
  mysql -h mysql -p
```

When prompted, enter password: `k8slearning`

You should see:
```
mysql>
```

List databases:
```sql
SHOW DATABASES;
```

Expected output:
```
+--------------------+
| Database           |
+--------------------+
| information_schema |
| database1          |
| mysql              |
| performance_schema |
+--------------------+
```

Exit MySQL client:
```sql
EXIT;
```

**Congratulations!** Your MySQL backend tier is fully operational and accessible via Kubernetes service discovery.

---

## Part 3: Deploying WordPress (Frontend Tier)

### Exercise 5: Create WordPress ConfigMap

#### Step 1: Review the WordPress ConfigMap

View the WordPress ConfigMap:
```bash
cat wordpress-configmap.yaml
```

**Expected content:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: wordpress-config
data:
  WORDPRESS_DB_HOST: "mysql"
  WORDPRESS_DB_USER: "root"
  WORDPRESS_DB_NAME: "database1"
```

**Understanding the configuration:**
- `WORDPRESS_DB_HOST`: MySQL service name - enables service discovery!
- `WORDPRESS_DB_USER`: Database user (root)
- `WORDPRESS_DB_NAME`: Database name (must match MySQL ConfigMap)

**Critical: Service Discovery**
- `WORDPRESS_DB_HOST: "mysql"` is NOT a hostname or IP
- It's the NAME of the MySQL Service we created
- Kubernetes DNS automatically resolves "mysql" to the service ClusterIP
- This works because both Pods are in the same namespace

#### Step 2: Create the ConfigMap

```bash
kubectl apply -f wordpress-configmap.yaml
```

Expected output:
```
configmap/wordpress-config created
```

#### Step 3: Verify the ConfigMap

```bash
kubectl get configmap wordpress-config
```

View the data:
```bash
kubectl describe configmap wordpress-config
```

Expected output:
```
Name:         wordpress-config
Namespace:    default
Labels:       <none>
Annotations:  <none>

Data
====
WORDPRESS_DB_HOST:
----
mysql
WORDPRESS_DB_NAME:
----
database1
WORDPRESS_DB_USER:
----
root
```

---

### Exercise 6: Create WordPress Secret

#### Step 1: Review the WordPress Secret

View the WordPress Secret:
```bash
cat wordpress-secret.yaml
```

**Expected content:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: wordpress-secret
type: Opaque
data:
  WORDPRESS_DB_PASSWORD: c2ltcGxpZGVhcm4=  # "k8slearning" base64 encoded
```

**Important:** This password MUST match the MySQL root password!

#### Step 2: Create the Secret

```bash
kubectl apply -f wordpress-secret.yaml
```

Expected output:
```
secret/wordpress-secret created
```

#### Step 3: Verify the Secret

```bash
kubectl get secret wordpress-secret
kubectl describe secret wordpress-secret
```

Verify it matches MySQL secret:
```bash
kubectl get secret mysql-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' && echo
kubectl get secret wordpress-secret -o jsonpath='{.data.WORDPRESS_DB_PASSWORD}' && echo
```

Both should output: `c2ltcGxpZGVhcm4=`

---

### Exercise 7: Deploy WordPress Application

#### Step 1: Review the WordPress Deployment

View the WordPress Deployment:
```bash
cat wordpress.yaml
```

**Expected content:**
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
        envFrom:
        - configMapRef:
            name: wordpress-config
        env:
        - name: WORDPRESS_DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: wordpress-secret
              key: WORDPRESS_DB_PASSWORD
```

**Understanding the configuration:**
- Uses official WordPress image (latest)
- Injects all wordpress-config keys as environment variables
- Separately injects password from wordpress-secret
- WordPress will automatically connect to MySQL on startup

#### Step 2: Deploy WordPress

```bash
kubectl apply -f wordpress.yaml
```

Expected output:
```
deployment.apps/wordpress created
```

#### Step 3: Monitor WordPress Deployment

Watch the Pod creation:
```bash
kubectl get pods -l app=wordpress --watch
```

Expected progression:
```
NAME                         READY   STATUS              RESTARTS   AGE
wordpress-6c5f8d9b7d-z9x4m   0/1     ContainerCreating   0          5s
wordpress-6c5f8d9b7d-z9x4m   1/1     Running             0          25s
```

Press `Ctrl+C` to stop watching.

**Note:** WordPress may take 20-30 seconds to start as it:
1. Pulls the WordPress image (if not cached)
2. Connects to MySQL
3. Initializes the WordPress database schema
4. Starts the Apache web server

#### Step 4: Verify WordPress is Running

Check deployment status:
```bash
kubectl get deployment wordpress
```

Expected output:
```
NAME        READY   UP-TO-DATE   AVAILABLE   AGE
wordpress   1/1     1            1           45s
```

Check Pod logs:
```bash
kubectl logs -l app=wordpress
```

Look for successful startup messages:
```
WordPress not found in /var/www/html - copying now...
Complete! WordPress has been successfully copied to /var/www/html
[core:notice] [pid 1] AH00094: Command line: 'apache2 -D FOREGROUND'
```

#### Step 5: Verify WordPress Can Connect to MySQL

Check WordPress environment variables:
```bash
kubectl exec -l app=wordpress -- env | grep WORDPRESS_DB
```

Expected output:
```
WORDPRESS_DB_HOST=mysql
WORDPRESS_DB_USER=root
WORDPRESS_DB_NAME=database1
WORDPRESS_DB_PASSWORD=k8slearning
```

**Connection test:**
Test WordPress to MySQL connectivity:
```bash
kubectl exec -l app=wordpress -- \
  mysql -h mysql -u root -pk8slearning database1 -e "SHOW TABLES;"
```

Expected output (initially empty):
```
Empty set (0.00 sec)
```

After WordPress setup completes, you'll see WordPress tables created:
```
Tables_in_database1
wp_commentmeta
wp_comments
wp_links
wp_options
wp_postmeta
wp_posts
wp_term_relationships
wp_term_taxonomy
wp_termmeta
wp_terms
wp_usermeta
wp_users
```

---

### Exercise 8: Create WordPress Service

#### Step 1: Review the WordPress Service

View the service manifest:
```bash
cat wordpress-service.yaml
```

**Expected content:**
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

**Understanding the service:**
- `type: NodePort`: Exposes service externally for browser access
- `port: 80`: Service listens on HTTP port 80
- `targetPort: 80`: WordPress container listens on port 80
- `selector.app: wordpress`: Routes to WordPress Pods

#### Step 2: Create the Service

```bash
kubectl apply -f wordpress-service.yaml
```

Expected output:
```
service/wordpress-service created
```

#### Step 3: Verify the Service

```bash
kubectl get service wordpress-service
```

Expected output:
```
NAME                TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
wordpress-service   NodePort   10.96.234.56    <none>        80:30123/TCP   10s
```

Note the NodePort (e.g., 30123) - this is how we'll access WordPress.

Get detailed service information:
```bash
kubectl describe service wordpress-service
```

Verify endpoints are populated:
```bash
kubectl get endpoints wordpress-service
```

Expected output:
```
NAME                ENDPOINTS         AGE
wordpress-service   172.17.0.5:80     15s
```

---

## Part 4: Accessing and Configuring WordPress

### Exercise 9: Access WordPress Installation

#### Step 1: Get the WordPress URL

Find the NodePort:
```bash
kubectl get service wordpress-service -o jsonpath='{.spec.ports[0].nodePort}' && echo
```

Example output: `30123`

Get your node IP (method depends on your cluster):

**For Minikube:**
```bash
minikube ip
```

**For Kind:**
```bash
kubectl get nodes -o wide
```
Use the INTERNAL-IP of any node.

**For Docker Desktop:**
Use `localhost` or `127.0.0.1`

**For cloud providers:**
Use the external IP of any worker node.

#### Step 2: Open WordPress in Browser

Construct the URL:
```
http://<NODE-IP>:<NODE-PORT>
```

Example:
```
http://192.168.49.2:30123
```

Open this URL in your web browser.

#### Step 3: Complete WordPress Setup

You should see the WordPress installation page with a language selection.

1. **Select Language**: Choose your preferred language (e.g., English)
2. **Click "Continue"**
3. **Welcome Screen**: You'll see "Welcome" screen
4. **Click "Let's go!"**
5. **Database Connection**: This should already be configured! Click "Submit"
6. **Run Installation**: Click "Run the installation"

7. **Site Information**:
   - **Site Title**: "My Kubernetes Blog"
   - **Username**: "admin" (or your choice)
   - **Password**: Choose a strong password
   - **Email**: Your email address
   - **Search Engine Visibility**: Check/uncheck as desired
   - **Click "Install WordPress"**

8. **Success!** You should see "Success!" message

9. **Log In**: Click "Log In" and use your credentials

**Congratulations!** You've successfully deployed and configured WordPress on Kubernetes!

---

## Part 5: Understanding Service Discovery

### Exercise 10: Deep Dive into Service Discovery

Service discovery is how WordPress found MySQL without knowing its IP address.

#### Step 1: Examine Kubernetes DNS

Check the DNS service:
```bash
kubectl get service -n kube-system | grep dns
```

Expected output:
```
kube-dns   ClusterIP   10.96.0.10   <none>        53/UDP,53/TCP   1d
```

#### Step 2: Test DNS Resolution from WordPress Pod

Get a shell in the WordPress Pod:
```bash
kubectl exec -it -l app=wordpress -- /bin/bash
```

Inside the WordPress Pod, test DNS resolution:

**1. Resolve the MySQL service:**
```bash
nslookup mysql
```

Expected output:
```
Server:     10.96.0.10
Address:    10.96.0.10#53

Name:   mysql.default.svc.cluster.local
Address: 10.96.123.45
```

**2. Check the full DNS name:**
```bash
nslookup mysql.default.svc.cluster.local
```

**3. Test connectivity:**
```bash
nc -zv mysql 3306
```

Expected output:
```
mysql [10.96.123.45] 3306 (mysql) open
```

**4. Examine /etc/resolv.conf:**
```bash
cat /etc/resolv.conf
```

Expected output:
```
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

Exit the Pod:
```bash
exit
```

#### Step 3: Understand DNS Resolution Flow

**When WordPress connects to "mysql:3306":**

1. WordPress container queries Kubernetes DNS (10.96.0.10)
2. DNS checks search domains:
   - `mysql.default.svc.cluster.local` (MATCH!)
3. DNS returns the MySQL service ClusterIP (e.g., 10.96.123.45)
4. WordPress connects to ClusterIP:3306
5. Service forwards traffic to MySQL Pod

**DNS Naming Convention:**
```
<service-name>.<namespace>.svc.cluster.local
```

**Short forms that work (in same namespace):**
- `mysql`
- `mysql.default`
- `mysql.default.svc`
- `mysql.default.svc.cluster.local`

#### Step 4: View All Cluster Services

```bash
kubectl get services --all-namespaces
```

This shows all services that are registered in Kubernetes DNS.

---

## Part 6: Verification and Testing

### Exercise 11: Verify Multi-Tier Communication

#### Step 1: Check All Resources

View all resources created in this lab:
```bash
kubectl get all -l 'app in (mysql,wordpress)'
```

Expected output:
```
NAME                             READY   STATUS    RESTARTS   AGE
pod/mysql-5d8f9c4b7d-x7k2p       1/1     Running   0          10m
pod/wordpress-6c5f8d9b7d-z9x4m   1/1     Running   0          5m

NAME                        TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/mysql               NodePort   10.96.123.45    <none>        3306:32123/TCP   9m
service/wordpress-service   NodePort   10.96.234.56    <none>        80:30123/TCP     4m

NAME                        READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/mysql       1/1     1            1           10m
deployment.apps/wordpress   1/1     1            1           5m

NAME                                   DESIRED   CURRENT   READY   AGE
replicaset.apps/mysql-5d8f9c4b7d       1         1         1       10m
replicaset.apps/wordpress-6c5f8d9b7d   1         1         1       5m
```

#### Step 2: Verify ConfigMaps and Secrets

```bash
kubectl get configmaps | grep -E '(mysql|wordpress)'
kubectl get secrets | grep -E '(mysql|wordpress)'
```

Expected output:
```
mysql-config       1      12m
wordpress-config   3      7m

mysql-secret       Opaque   1      11m
wordpress-secret   Opaque   1      6m
```

#### Step 3: Test WordPress Functionality

Access WordPress in your browser and:

1. **Create a Post**:
   - Dashboard → Posts → Add New
   - Title: "Hello Kubernetes!"
   - Content: "This post is stored in MySQL running on Kubernetes"
   - Click "Publish"

2. **View the Post**:
   - Visit your WordPress site (homepage)
   - You should see your post

3. **Verify in Database**:
```bash
kubectl exec -l app=mysql -- \
  mysql -u root -pk8slearning database1 \
  -e "SELECT post_title FROM wp_posts WHERE post_type='post';"
```

Expected output:
```
post_title
Hello Kubernetes!
```

This confirms data is flowing from WordPress → MySQL!

#### Step 4: Test Persistence

Simulate a WordPress Pod failure:
```bash
kubectl delete pod -l app=wordpress
```

Wait for new Pod to start:
```bash
kubectl get pods -l app=wordpress --watch
```

Access WordPress again - your post should still be there!

**Why?** Because:
- Data is stored in MySQL, not WordPress Pod
- MySQL Pod was not deleted
- New WordPress Pod connects to same MySQL database

---

## Part 7: Troubleshooting Common Issues

### Exercise 12: Troubleshooting Multi-Tier Applications

#### Issue 1: WordPress Cannot Connect to MySQL

**Symptoms:**
- "Error establishing database connection" in browser
- WordPress Pod in CrashLoopBackOff

**Diagnosis:**
```bash
kubectl logs -l app=wordpress
```

Look for:
```
Warning: mysqli::__construct(): (HY000/2002): Connection refused
```

**Common Causes and Solutions:**

**A. MySQL Service Not Running**
```bash
kubectl get service mysql
kubectl get pods -l app=mysql
```
Solution: Ensure MySQL Pod and Service are running.

**B. Wrong Service Name in WordPress ConfigMap**
```bash
kubectl get configmap wordpress-config -o yaml | grep WORDPRESS_DB_HOST
```
Should be: `WORDPRESS_DB_HOST: mysql`
Solution: Fix ConfigMap and recreate WordPress Pod.

**C. Password Mismatch**
```bash
kubectl get secret mysql-secret -o jsonpath='{.data.MYSQL_ROOT_PASSWORD}' | base64 --decode && echo
kubectl get secret wordpress-secret -o jsonpath='{.data.WORDPRESS_DB_PASSWORD}' | base64 --decode && echo
```
Solution: Ensure both secrets have the same password.

**D. Different Namespaces**
```bash
kubectl get pods -A | grep -E '(mysql|wordpress)'
```
Solution: Ensure both Pods are in the same namespace, or use FQDN (e.g., `mysql.default.svc.cluster.local`).

#### Issue 2: Cannot Access WordPress in Browser

**Symptoms:**
- Connection timeout or connection refused
- "This site can't be reached"

**Diagnosis:**

**A. Service Not Created**
```bash
kubectl get service wordpress-service
```
Solution: Apply the wordpress-service.yaml file.

**B. Pod Not Ready**
```bash
kubectl get pods -l app=wordpress
```
Wait until STATUS is "Running" and READY is "1/1".

**C. Wrong NodePort**
```bash
kubectl get service wordpress-service -o jsonpath='{.spec.ports[0].nodePort}' && echo
```
Verify you're using the correct port in your browser.

**D. Firewall/Security Group**
- Cloud providers may block NodePorts by default
- Check firewall rules allow traffic on the NodePort
- For production, use LoadBalancer or Ingress

#### Issue 3: ConfigMap or Secret Not Found

**Symptoms:**
- Pod stuck in "CreateContainerConfigError"
- Error: "configmap not found" or "secret not found"

**Diagnosis:**
```bash
kubectl describe pod -l app=wordpress
```

Look for:
```
Error: configmap "wordpress-config" not found
```

**Solution:**
```bash
# List resources
kubectl get configmaps
kubectl get secrets

# Create missing resources
kubectl apply -f wordpress-configmap.yaml
kubectl apply -f wordpress-secret.yaml

# Restart Pod to pick up resources
kubectl delete pod -l app=wordpress
```

#### Issue 4: Pod Stuck in Pending

**Symptoms:**
- Pod STATUS shows "Pending" for extended time

**Diagnosis:**
```bash
kubectl describe pod -l app=wordpress
```

Look in Events section for:
```
Warning  FailedScheduling  Insufficient memory
```

**Common Causes:**
- Not enough resources (CPU/memory) in cluster
- No nodes available
- Resource limits/requests too high

**Solution:**
```bash
# Check node resources
kubectl describe nodes

# For Minikube, increase resources:
minikube delete
minikube start --memory=4096 --cpus=2

# For production: Add nodes or reduce resource requests
```

#### Issue 5: Database Tables Not Created

**Symptoms:**
- WordPress shows database connection error
- Tables missing in MySQL

**Diagnosis:**
```bash
kubectl exec -l app=mysql -- \
  mysql -u root -pk8slearning database1 -e "SHOW TABLES;"
```

If empty or error:
```bash
kubectl logs -l app=mysql
```

**Solution:**
- Delete and recreate MySQL Pod to re-initialize database
- Ensure MYSQL_DATABASE environment variable is set correctly

---

## Part 8: Advanced Concepts

### Exercise 13: Scale WordPress (Optional)

WordPress frontend can be scaled horizontally:

```bash
kubectl scale deployment wordpress --replicas=3
```

Check the Pods:
```bash
kubectl get pods -l app=wordpress
```

Expected output:
```
NAME                         READY   STATUS    RESTARTS   AGE
wordpress-6c5f8d9b7d-abc123   1/1     Running   0          5m
wordpress-6c5f8d9b7d-def456   1/1     Running   0          10s
wordpress-6c5f8d9b7d-ghi789   1/1     Running   0          10s
```

The wordpress-service automatically load balances across all 3 Pods!

**Why scale WordPress but not MySQL?**
- WordPress is stateless (stores data in MySQL)
- Multiple WordPress Pods can safely share one MySQL database
- MySQL is stateful and requires special handling for high availability (StatefulSets, replication)

Scale back down:
```bash
kubectl scale deployment wordpress --replicas=1
```

---

### Exercise 14: View Resource Consumption

Check resource usage:
```bash
kubectl top pods -l 'app in (mysql,wordpress)'
```

Expected output:
```
NAME                         CPU(cores)   MEMORY(bytes)
mysql-5d8f9c4b7d-x7k2p       10m          250Mi
wordpress-6c5f8d9b7d-z9x4m   5m           150Mi
```

This helps you understand resource requirements for capacity planning.

---

### Exercise 15: Examine Network Communication

#### Step 1: Deploy a Network Debug Pod

```bash
kubectl run netshoot --image=nicolaka/netshoot -it --rm --restart=Never -- /bin/bash
```

Inside the debug Pod:

**Test DNS:**
```bash
nslookup mysql
nslookup wordpress-service
```

**Test MySQL connectivity:**
```bash
nc -zv mysql 3306
```

**Test WordPress connectivity:**
```bash
curl -I http://wordpress-service
```

Expected output:
```
HTTP/1.1 200 OK
Server: Apache/2.4.x
X-Powered-By: PHP/8.x
```

**View network policies (if any):**
```bash
exit
kubectl get networkpolicies
```

---

## Lab Cleanup

### Exercise 16: Clean Up Resources

Remove all resources created in this lab:

```bash
# Navigate to the lab directory
cd k8s/labs/workloads/wordpress

# Delete WordPress resources
kubectl delete -f wordpress-service.yaml
kubectl delete -f wordpress.yaml
kubectl delete -f wordpress-secret.yaml
kubectl delete -f wordpress-configmap.yaml

# Delete MySQL resources
kubectl delete -f mysql-service.yaml
kubectl delete -f mysql.yaml
kubectl delete -f mysql-secret.yaml
kubectl delete -f mysql-config.yaml
```

**Alternative: Delete all at once:**
```bash
kubectl delete -f k8s/labs/workloads/wordpress/
```

**Or delete by label:**
```bash
kubectl delete all -l 'app in (mysql,wordpress)'
kubectl delete configmap -l 'app in (mysql,wordpress)'
kubectl delete secret -l 'app in (mysql,wordpress)'
```

**Note:** Secrets and ConfigMaps don't have app labels by default, so individual deletion is safer:
```bash
kubectl delete configmap mysql-config wordpress-config
kubectl delete secret mysql-secret wordpress-secret
```

Verify cleanup:
```bash
kubectl get all,configmaps,secrets | grep -E '(mysql|wordpress)'
```

Should return no results.

---

## Key Takeaways

1. **Multi-Tier Architecture**:
   - Separates concerns into frontend (WordPress) and backend (MySQL) tiers
   - Each tier can be scaled, updated, and managed independently

2. **Service Discovery**:
   - Kubernetes DNS automatically resolves service names to ClusterIPs
   - Services provide stable network identities for Pods
   - Pods can communicate using service names instead of IPs

3. **Configuration Management**:
   - **ConfigMaps** store non-sensitive configuration (database names, hostnames, ports)
   - **Secrets** store sensitive data (passwords, tokens, keys)
   - Both decouple configuration from container images

4. **Environment Variable Injection**:
   - `envFrom`: Injects all ConfigMap/Secret keys as environment variables
   - `env[].valueFrom`: Injects specific keys with custom names
   - Containers receive configuration at startup

5. **Service Types**:
   - **ClusterIP**: Internal communication (MySQL)
   - **NodePort**: External access for testing (WordPress)
   - Production should use LoadBalancer or Ingress

6. **Communication Flow**:
   - User → NodePort → WordPress Service → WordPress Pod
   - WordPress Pod → MySQL Service (DNS) → MySQL Pod
   - MySQL Pod → Persistent Database Storage

7. **Troubleshooting**:
   - Check Pod logs with `kubectl logs`
   - Verify service endpoints with `kubectl describe service`
   - Test connectivity with `kubectl exec` and networking tools
   - Ensure resources exist in the same namespace

8. **Scaling Considerations**:
   - Stateless tiers (WordPress) can scale horizontally
   - Stateful tiers (MySQL) require special handling
   - Services automatically load balance across replicas

---

## Production Considerations

For production WordPress on Kubernetes, consider:

1. **Persistent Storage**:
   - Current setup loses data when MySQL Pod restarts
   - Use **PersistentVolumeClaims** for MySQL data
   - Mount volumes to `/var/lib/mysql` in MySQL Pod

2. **High Availability**:
   - Run multiple WordPress replicas behind LoadBalancer
   - Use StatefulSet for MySQL or managed database (RDS, Cloud SQL)
   - Implement database replication

3. **Security**:
   - Use **NetworkPolicies** to restrict traffic
   - Implement RBAC for Secret access
   - Use external secret managers (Vault, AWS Secrets Manager)
   - Enable TLS/SSL with Ingress
   - Run as non-root user

4. **Resource Management**:
   - Set resource requests and limits
   - Implement HorizontalPodAutoscaler for WordPress
   - Monitor with Prometheus/Grafana

5. **Backup and Recovery**:
   - Regular database backups
   - Snapshot PersistentVolumes
   - Test restore procedures

6. **Ingress**:
   - Use Ingress instead of NodePort
   - Implement TLS termination
   - Configure domain names

7. **Monitoring and Logging**:
   - Aggregate logs with ELK or Loki
   - Monitor metrics with Prometheus
   - Set up alerts for downtime

8. **Update Strategy**:
   - Use RollingUpdate for zero-downtime deployments
   - Implement health checks (readiness/liveness probes)
   - Version control all Kubernetes manifests

---

## Additional Exercises (Challenge)

### Challenge 1: Add Persistent Storage
Modify the MySQL Deployment to use a PersistentVolumeClaim. Data should survive Pod restarts.

**Hint:**
```yaml
volumes:
  - name: mysql-storage
    persistentVolumeClaim:
      claimName: mysql-pvc
volumeMounts:
  - name: mysql-storage
    mountPath: /var/lib/mysql
```

### Challenge 2: Implement Health Checks
Add readiness and liveness probes to both MySQL and WordPress deployments.

**Hint for MySQL:**
```yaml
livenessProbe:
  exec:
    command: ["mysqladmin", "ping"]
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Challenge 3: Use Environment-Specific ConfigMaps
Create separate ConfigMaps for dev, staging, and prod environments with different database names.

### Challenge 4: Implement Network Policies
Create a NetworkPolicy that only allows WordPress Pods to communicate with MySQL on port 3306.

### Challenge 5: Add Redis Cache
Deploy Redis as a caching layer and configure WordPress to use it with the Redis Object Cache plugin.

---

## Additional Commands Reference

```bash
# View all resources for WordPress stack
kubectl get all,configmaps,secrets -l 'app in (mysql,wordpress)'

# Port-forward to MySQL for debugging
kubectl port-forward service/mysql 3306:3306

# Port-forward to WordPress (alternative to NodePort)
kubectl port-forward service/wordpress-service 8080:80

# Execute MySQL queries
kubectl exec -l app=mysql -- mysql -u root -pk8slearning -e "QUERY"

# View real-time logs
kubectl logs -f -l app=wordpress

# Get service endpoint details
kubectl get endpoints

# Describe networking for debugging
kubectl describe service mysql
kubectl describe service wordpress-service

# Check DNS from any Pod
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup mysql

# View resource requests/limits
kubectl describe deployment mysql
kubectl describe deployment wordpress
```

---

## Best Practices Summary

1. **Always use Secrets for sensitive data** (passwords, API keys)
2. **Use ConfigMaps for non-sensitive configuration** (URLs, database names)
3. **Leverage service discovery** with service names, not IPs
4. **Label everything** for easy filtering and management
5. **Use namespaces** to separate environments (dev, staging, prod)
6. **Implement health checks** for reliable deployments
7. **Set resource limits** to prevent resource starvation
8. **Version control manifests** for infrastructure as code
9. **Test in non-production** before deploying to production
10. **Monitor and log** for observability and debugging

---

## Troubleshooting Checklist

Use this checklist when things go wrong:

- [ ] Are all Pods running? `kubectl get pods`
- [ ] Are all Services created? `kubectl get services`
- [ ] Do Services have endpoints? `kubectl get endpoints`
- [ ] Are ConfigMaps and Secrets present? `kubectl get configmaps,secrets`
- [ ] Do ConfigMap/Secret names match Pod specifications?
- [ ] Are Pods in the same namespace?
- [ ] Can Pods resolve DNS? `kubectl exec POD -- nslookup mysql`
- [ ] Can Pods connect to MySQL? `kubectl exec POD -- nc -zv mysql 3306`
- [ ] Are passwords matching in both Secrets?
- [ ] Check Pod logs for errors: `kubectl logs POD`
- [ ] Check Pod events: `kubectl describe pod POD`
- [ ] Are there enough cluster resources? `kubectl describe nodes`

---

## Next Steps

Now that you've deployed a multi-tier application, you can:

1. **Explore Ingress**: Learn how to expose WordPress with a domain name
2. **Add Persistent Storage**: Make MySQL data persistent across Pod restarts
3. **Implement StatefulSets**: Deploy MySQL as a StatefulSet for better data management
4. **Set Up Monitoring**: Add Prometheus and Grafana for observability
5. **Implement CI/CD**: Automate WordPress deployments with GitOps
6. **Learn Helm**: Package this application as a Helm chart for easy deployment

---

## Additional Resources

- [Kubernetes ConfigMaps Documentation](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Kubernetes Secrets Documentation](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Kubernetes Services Documentation](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes DNS Documentation](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [WordPress Docker Image](https://hub.docker.com/_/wordpress)
- [MySQL Docker Image](https://hub.docker.com/_/mysql)
- [Example: Deploying WordPress and MySQL with Persistent Volumes](https://kubernetes.io/docs/tutorials/stateful-application/mysql-wordpress-persistent-volume/)

---

**Lab Created**: March 2026
**Compatible with**: Kubernetes 1.24+
**Estimated Completion Time**: 90-120 minutes
**Difficulty Level**: Intermediate

---

**Congratulations!** You have successfully completed Lab 41: Deploying WordPress on Kubernetes. You've learned how to deploy a complete multi-tier application, manage configuration with ConfigMaps and Secrets, enable service discovery, and troubleshoot common issues. These skills are fundamental for deploying production applications on Kubernetes.
