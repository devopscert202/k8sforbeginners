### **ConfigMaps in Kubernetes: A Brief Overview**

#### **What is a ConfigMap?**
A **ConfigMap** is a Kubernetes object used to decouple application configuration from the containerized application code. It stores configuration data as key-value pairs, which can be injected into Pods as environment variables, command-line arguments, or mounted as files.

#### **Use Cases**
1. **Application Configuration:**
   - Storing database connection strings, feature flags, or API endpoints.
2. **Environment Management:**
   - Changing configuration values without rebuilding or redeploying containers.
3. **Shared Configuration:**
   - Sharing common configuration data across multiple Pods.

#### **Benefits**
- **Separation of Concerns:** Keeps application configuration separate from the code.
- **Flexibility:** Supports dynamic updates without requiring Pod restarts (when mounted as files).
- **Portability:** Simplifies application deployment across environments (e.g., development, staging, production).

---

### **Commands Extracted from the PDF**

#### **Step 1: Creating a ConfigMap**
1. **Create a YAML file for ConfigMap:**
   ```bash
   nano configmap.yaml
   ```
   Add the following content:
   ```yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: example-configmap
   data:
     database: mongodb
     database_uri: mongodb://localhost:27017
   ```

2. **Create the ConfigMap:**
   ```bash
   kubectl create -f configmap.yaml
   ```

3. **Verify the ConfigMap:**
   ```bash
   kubectl get configmap
   ```

#### **Step 2: Using ConfigMap in Pods**
1. **Create a Pod referencing the ConfigMap as environment variables:**
   ```bash
   nano configpod.yaml
   ```
   Add the following content:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: pod-env-var
   spec:
     containers:
     - name: env-var-configmap
       image: nginx:1.7.9
       envFrom:
       - configMapRef:
           name: example-configmap
   ```

2. **Create the Pod:**
   ```bash
   kubectl create -f configpod.yaml
   ```

3. **Verify the Pod state:**
   ```bash
   kubectl get pods
   ```

4. **Access the Pod and view environment variables:**
   ```bash
   kubectl exec -it pod-env-var -- env
   ```

#### **Step 3: Using Specific Keys in ConfigMap**
1. **Create a Pod referencing a specific key in the ConfigMap:**
   ```bash
   nano config-svc.yaml
   ```
   Add the following content:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: pod-env12
   spec:
     containers:
     - name: env-var-configmap
       image: nginx:1.7.9
       env:
       - name: testenv
         valueFrom:
           configMapKeyRef:
             name: example-configmap
             key: database
   ```

2. **Create the Pod:**
   ```bash
   kubectl create -f config-svc.yaml
   ```

3. **Verify the Pod state:**
   ```bash
   kubectl get pods
   ```

4. **Access the Pod and check specific environment variables:**
   ```bash
   kubectl exec -it pod-env12 -- bash
   env | grep database
   ```

#### **Step 4: Mounting ConfigMap as a Volume**
1. **Create a Pod that mounts the ConfigMap as a volume:**
   ```bash
   nano configfile.yaml
   ```
   Add the following content:
   ```yaml
   apiVersion: v1
   kind: Pod
   metadata:
     name: testconfig
   spec:
     containers:
     - name: test
       image: docker.io/httpd
       volumeMounts:
       - name: config-volume
         mountPath: /tmp/myenvs/
     volumes:
     - name: config-volume
       configMap:
         name: example-configmap
   restartPolicy: Never
   ```

2. **Create the Pod:**
   ```bash
   kubectl create -f configfile.yaml
   ```

3. **Verify the Pod state:**
   ```bash
   kubectl get pods
   ```

4. **Access the Pod and view mounted files:**
   ```bash
   kubectl exec -it testconfig -- bash
   ls /tmp/myenvs/
   cat /tmp/myenvs/database
   ```

---

### **Outputs of Commands**

1. **`kubectl get configmap`**
   Example Output:
   ```
   NAME               DATA   AGE
   example-configmap  2      5m
   ```

2. **`kubectl get pods`**
   Example Output:
   ```
   NAME           READY   STATUS    RESTARTS   AGE
   pod-env-var    1/1     Running   0          2m
   pod-env12      1/1     Running   0          1m
   testconfig     1/1     Running   0          30s
   ```

3. **`kubectl exec -it pod-env-var -- env`**
   Example Output:
   ```
   DATABASE=mongodb
   DATABASE_URI=mongodb://localhost:27017
   ```

4. **`kubectl exec -it testconfig -- bash`**
   Inside the Pod:
   ```
   # ls /tmp/myenvs/
   database
   database_uri
   # cat /tmp/myenvs/database
   mongodb
   ```

---

### **Summary**
ConfigMaps in Kubernetes provide a clean way to manage application configuration separate from the application code. They are versatile, allowing you to:
1. Pass environment variables to Pods.
2. Reference specific configuration keys.
3. Mount configuration data as files within Pods.

**Benefits of ConfigMaps:**
- Decouples configuration from application code.
- Simplifies updates across multiple environments.
- Avoids hardcoding configuration values in containers.

By following the examples and commands extracted from the PDF, you can effectively create, use, and verify ConfigMaps in your Kubernetes cluster. This approach enhances the flexibility, security, and manageability of your containerized applications.
