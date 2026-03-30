### **Azure Kubernetes Service (AKS) Lab Tutorial - Part 1**

---

### **1. Introduction to AKS**

Azure Kubernetes Service (AKS) is a fully managed Kubernetes service provided by Microsoft Azure. It abstracts the complexities of Kubernetes setup and maintenance, enabling developers to focus on deploying and managing containerized applications. 

#### **Features of AKS:**

1. **Managed Kubernetes Control Plane**: Azure handles upgrades, patches, and scaling of the Kubernetes control plane.
2. **Integration with Azure Services**: Native integration with Azure Monitor, Azure Active Directory (AAD), and other Azure services for enhanced observability and security.
3. **Networking Options**: 
   - **Kubenet**: Simple, default network configuration.
   - **Azure CNI**: Advanced network configuration for enterprise-level requirements.
4. **Scaling**: Supports manual scaling and cluster autoscaler.
5. **Multi-Zone Availability**: Deploy applications across availability zones to increase reliability.

---

### **2. Comparison: AKS vs Other Cloud Kubernetes Offerings**

| Feature                  | **Azure AKS**                   | **Amazon EKS**                  | **Google GKE**                  |
|--------------------------|----------------------------------|----------------------------------|----------------------------------|
| **Control Plane Cost**    | Free (pay for worker nodes only) | ~$74/month for control plane     | Free for basic cluster, $0.10/hour for autopilot/control plane |
| **Networking**            | Azure CNI, Kubenet              | VPC CNI                          | VPC-native, Alias IPs           |
| **Autoscaling**           | Supported                       | Supported                        | Supported                       |
| **Integrated Monitoring** | Azure Monitor                   | CloudWatch                       | Cloud Monitoring                |
| **Hybrid Options**        | Azure Arc                       | EKS Anywhere                     | Anthos                          |
| **Multi-Zone Clusters**   | Supported                       | Supported                        | Supported                       |

**Why Choose AKS?**  
- Strong integration with Azure services.  
- Free managed control plane.  
- Advanced security options like AAD integration and Azure Policy for Kubernetes.  

---

### **3. Step-by-Step AKS Lab**

Launch Bash Shell.

#### **Step 1: Create a Resource Group**

If the resource group is already created during the Cloud Shell filestore process, skip this step.

```bash
az group create \
    --name Regroup_3etcnCVxcbW6UKd52_7oNl \
    --location eastus
```
To list the available group, 

```
az group list
```
---

#### **Step 2: Create a Virtual Network (VNet) and Subnet**

Replace the resource group name with the correct name.  

```bash
az network vnet create \
    --resource-group Regroup_3etcnCVxcbW6UKd52_7oNl \
    --name MyVNet \
    --address-prefix 10.0.0.0/16 \
    --location eastus \
    --subnet-name MySubnet \
    --subnet-prefix 10.0.1.0/24
```

---

#### **Step 3: Retrieve the Subnet ID**

```bash
az network vnet subnet show \
    --resource-group Regroup_3etcnCVxcbW6UKd52_7oNl \
    --vnet-name MyVNet \
    --name MySubnet \
    --query id --output tsv
```

---

#### **Step 4: Create the AKS Cluster**

Replace the resource group name with the correct name.  Replace the vnet-subnet-id name with the correct name from Step 3.


```bash
az aks create \
    --resource-group Regroup_3etcnCVxcbW6UKd52_7oNl \
    --name MyAKSCluster \
    --node-count 2 \
    --network-plugin azure \
    --vnet-subnet-id "/subscriptions/2f02f8ca-866d-410a-bfed-32876b28bc58/resourceGroups/Regroup_3etcnCVxcbW6UKd52_7oNl/providers/Microsoft.Network/virtualNetworks/MyVNet/subnets/MySubnet" \
    --location eastus \
    --service-cidr 10.1.0.0/16 \
    --dns-service-ip 10.1.0.10 \
    --enable-managed-identity \
    --generate-ssh-keys
```

---

### **4. Connect to the AKS Cluster**

To manage your AKS cluster, you need to authenticate and connect using `kubectl`. This can be done via the Azure CLI on your local machine or through the **Azure Cloud Shell** (a browser-based terminal accessible in the Azure portal).

#### **Authentication and Credential Retrieval**

1. **Authenticate to Azure**:
   Log in to your Azure account using the CLI. If you're using the **Azure Cloud Shell**, you can skip this step as you're already authenticated.

   ```bash
   az login
   ```
   - This will open a browser window to sign in with your Azure credentials.
   - After successful authentication, your subscriptions will be listed.

   Alternatively, you can specify your subscription directly:
   ```bash
   az account set --subscription <SUBSCRIPTION_ID>
   ```

2. **Retrieve AKS Cluster Credentials**:
   Use the `az aks get-credentials` command to configure access to your cluster:
   Replace the resource group name with the correct name.
   
   ```bash
   az aks get-credentials \
       --resource-group Regroup_3etcnCVxcbW6UKd52_7oNl \
       --name MyAKSCluster
   ```
   - This command downloads the kubeconfig file and configures `kubectl` to use it for cluster access.

   If you want to merge the cluster's configuration with an existing kubeconfig file:
   ```bash
   az aks get-credentials \
       --resource-group Regroup_3etcnCVxcbW6UKd52_7oNl \
       --name MyAKSCluster \
       --overwrite-existing
   ```

---

#### **Connecting Through Azure Cloud Shell**

- The **Azure Cloud Shell** is an in-browser terminal provided by Azure, with the Azure CLI and `kubectl` pre-installed.
- You can launch it from the Azure portal by clicking the **Cloud Shell** icon on the top-right corner of the Azure portal.

   Once in the Cloud Shell:
   - Skip the `az login` step (as it uses your portal authentication).
   - Run the same `az aks get-credentials` command to fetch cluster credentials.

---

#### **Verify Connection**

Once authenticated, verify your connection to the AKS cluster by running:

```bash
kubectl get nodes
```

If successful, this command will display a list of nodes in your cluster, similar to the following output:

```
NAME                                STATUS   ROLES   AGE     VERSION
aks-nodepool1-12345678-vmss000000   Ready    agent   10m     v1.24.9
aks-nodepool1-12345678-vmss000001   Ready    agent   10m     v1.24.9
```

> **Note**: If `kubectl` is not installed locally, you can install it using the command:
> ```bash
> az aks install-cli
> ```

---

#### **Will the Master Node Appear in the Node List?**

No, the **master node** (control plane) will **not** be shown when you run the `kubectl get nodes` command.

In Azure Kubernetes Service (AKS), the **master node** is fully managed by Azure. The control plane is abstracted away, meaning you do not need to manage it directly. You will only see the **worker nodes** in the `kubectl get nodes` output.

Note: Kubernetes version will be different on the lab session when cluster is created and thats okay.

Example output:
```
NAME                                STATUS   ROLES   AGE     VERSION
aks-nodepool1-12345678-vmss000000   Ready    agent   10m     v1.24.9
aks-nodepool1-12345678-vmss000001   Ready    agent   10m     v1.24.9
```

- **Control Plane**: Azure manages it and ensures it's always running with high availability, but you cannot interact with it directly or see it via `kubectl`.
- **Worker Nodes**: These are listed, and you can manage them directly (scale, upgrade, etc.).

If you need to interact with the control plane, you would typically use Azure CLI or other management tools rather than `kubectl`.

---

#### **5. Delete the AKS Cluster**

When the lab is complete, delete the cluster to avoid incurring unnecessary costs:

```bash
az aks delete \
    --resource-group Regroup_3etcnCVxcbW6UKd52_7oNl \
    --name MyAKSCluster \
    --yes \
    --no-wait
```
