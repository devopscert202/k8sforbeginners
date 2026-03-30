# Kuberentes RBAC Demo

Go through the RBAC concepts before trying this exercise to understand the basics.

# Create a namespace named 'role'
kubectl create namespace role

# Create a directory for role-related files and navigate into it
mkdir role && cd role


# Generate an RSA private key
sudo openssl genrsa -out user3.key 2048

# Create a certificate signing request (CSR) using the private key
sudo openssl req -new -key user3.key -out user3.csr
```
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank.
For some fields, there will be a default value.

-----
Country Name (2 letter code) [AU]:US
State or Province Name (full name) [Some-State]:California
Locality Name (eg, city) []:San Francisco
Organization Name (eg, company) [Internet Widgits Pty Ltd]:dev-team
Organizational Unit Name (eg, section) []:development
**Common Name (e.g., your name or your server's hostname) []:user3**
Email Address []:user3@example.com

Please enter the following 'extra' attributes
to be sent with your certificate request
A challenge password []:
An optional company name []:

```

# Sign the CSR to generate a certificate (linked with Kubernetes CA)
sudo openssl x509 -req -in user3.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out user3.crt -days 500

# Role and RoleBinding Setup

# Edit or create a Role YAML file
vi role.yaml
#use the role.yaml from git repo

# Create the role from the YAML file
kubectl create -f role.yaml

# Verify the created role
kubectl get roles -n role

# Edit or create a RoleBinding YAML file
vi rolebinding.yaml

#use the rolebinding .yaml from git repo

# Create the RoleBinding from the YAML file
kubectl create -f rolebinding.yaml

# Verify the created RoleBinding
kubectl get rolebinding -n role


# Set Up User Credentials

## Assign credentials to user3 using the certificate and key
kubectl config set-credentials user3 --client-certificate=/home/labsuser/role/user3.crt --client-key=/home/labsuser/role/user3.key

## Set up a context for user3 in the 'role' namespace
kubectl config set-context user3-context --cluster=kubernetes --namespace=role --user=user3

## Display all contexts
kubectl config get-contexts

## Output
```
labsuser@master:~/role$ kubectl config get-contexts
CURRENT   NAME                          CLUSTER      AUTHINFO           NAMESPACE
*         kubernetes-admin@kubernetes   kubernetes   kubernetes-admin   
          user3-context                 kubernetes   user3              role
```

## View the current kubeconfig file for user3 context
	
cd .. ; 
cat .kube/config

# Role Verification and Testing

### change the context to user3-context

kubectl config use-context user3-context

### change the permissions for the user3 certificates

cd /home/labsuser/role ; 
sudo chmod 666 user3.key user3.crt

### List pods in the 'role' namespace with the user-specific kubeconfig
kubectl get pods 

# Deploy a test application in the 'role' namespace
kubectl create deployment test --image=docker.io/httpd -n role

# Verify the created deployment and its pods
kubectl get deployment ; 
kubectl delete pods

# Create a ConfigMap in the 'role' namespace

kubectl create configmap my-config --from-literal=key1=config1 --kubeconfig=config

## Above command would fail due to the permission assigned to user3
error: failed to create configmap: configmaps is forbidden: User "user3" cannot create resource "configmaps" in API group "" in the namespace "role"

# View the created ConfigMap
kubectl get configmaps

## Above command would fail due to the permission assigned to user3
error: failed to create configmap: configmaps is forbidden: User "user3" cannot create resource "configmaps" in API group "" in the namespace "role"

# File Management and Key Distribution (OPTIONAL steps to distribute to the worker nodes for kubectl to work for user3)

## Navigate back to the home directory
cd ..

## View the certificate and key files
cat user3.crt
cat user3.key

## Copy files to the worker node (example commands for manual steps)
scp user3.crt worker-node-1:/role/
scp user3.key worker-node-1:/role/

## On the worker node, create a directory and add files
mkdir -p /role && cd /role
vi user3.crt  # Paste the certificate content
vi user3.key  # Paste the key content

---
