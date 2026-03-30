# 3. Creating a Deployment with ConfigMap as Volume

## 3.1 Overview
Kubernetes ConfigMaps allow you to store configuration data as key-value pairs. You can use ConfigMaps to separate configuration from application code. One of the ways to make this configuration available to your applications is by mounting the ConfigMap as a volume in a Pod. This allows your application to read configuration values directly from the file system as if they were regular files, making it easier to update configuration values dynamically without having to rebuild or restart your containers.

## 3.2 Concept
A ConfigMap can be mounted into a Pod as a volume, allowing containers to access its data as files. Each key in the ConfigMap is turned into a file, and the value of that key becomes the content of the file. When the ConfigMap changes, the volume automatically updates, which is useful for managing configuration that changes over time.

## 3.3 Benefits
- **Separation of Config and Code**: Keeps configuration data separate from application code, improving modularity and making it easier to manage.
- **Dynamic Updates**: ConfigMap volumes automatically reflect changes to the configuration, avoiding manual intervention.
- **Simplifies Configuration Management**: Easier to manage environment-specific configurations for applications running in Kubernetes clusters.

## 3.4 Use Cases
- **Storing Application Configurations**: Manage and store configuration files that are needed by the application at runtime.
- **Environment-Specific Settings**: Use ConfigMaps for storing different settings for staging, development, and production environments.
- **Seamless Updates**: When the ConfigMap is updated, the changes will be reflected in the containers without needing a restart, making it easy to manage application configuration.

## 3.5 Real-World Scenario
Consider a microservice-based application where each service requires a different configuration (such as database URLs, API keys, etc.). Using ConfigMap volumes, you can mount the appropriate configuration files into each container, making the process of updating configurations as easy as updating the ConfigMap.

## 3.6 Implementation Example

Below is an example YAML configuration for creating a Deployment where the ConfigMap is used as a volume in a Pod:

### 3.6.1 Step 1: Create the ConfigMap
First, we create a ConfigMap with two key-value pairs that will be used as configuration.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  database_url: "jdbc:mysql://localhost:3306/mydb"
  api_key: "your-api-key-here"
```

### 3.6.2 Step 2: Create the Deployment Using the ConfigMap as Volume

Now, we define a Deployment that uses the ConfigMap as a volume.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: configmap-deployment
spec:
  replicas: 1
  selector:
    matchLabels:
      app: configmap-app
  template:
    metadata:
      labels:
        app: configmap-app
    spec:
      containers:
      - name: configmap-container
        image: nginx
        volumeMounts:
        - name: config-volume
          mountPath: /etc/config
      volumes:
      - name: config-volume
        configMap:
          name: app-config
```

### Explanation of the YAML:
- **ConfigMap**: The first part creates a `ConfigMap` named `app-config`, containing two key-value pairs: `database_url` and `api_key`.
- **Deployment**: In the second part, we define a `Deployment` where the `ConfigMap` is mounted into the container under the `/etc/config` directory. Kubernetes automatically creates files for each key in the ConfigMap (e.g., `database_url` and `api_key` will be stored as files).

## 3.7 Verification Steps

1. **Create the ConfigMap**:
   Apply the ConfigMap YAML to your Kubernetes cluster:
   ```bash
   kubectl apply -f configmap.yaml
   ```

2. **Create the Deployment**:
   Apply the Deployment YAML to create the Pod with the ConfigMap mounted as a volume:
   ```bash
   kubectl apply -f deployment.yaml
   ```

3. **Verify the Pod is Running**:
   Check if the Deployment is running:
   ```bash
   kubectl get pods
   ```

4. **Check the Mounted Files in the Pod**:
   Once the Pod is running, enter the container and check the `/etc/config` directory to see the files created from the ConfigMap:
   ```bash
   kubectl exec -it <pod-name> -- /bin/bash
   ls /etc/config
   cat /etc/config/database_url
   cat /etc/config/api_key
   ```

The files `database_url` and `api_key` will contain the values that were stored in the ConfigMap (`jdbc:mysql://localhost:3306/mydb` and `your-api-key-here`).
