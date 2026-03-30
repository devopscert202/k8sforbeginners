# Lab Material: AWS CloudFormation and EKS Deployment

## Introduction
AWS CloudFormation is an Infrastructure as Code (IaC) service that allows users to define and provision AWS resources in a consistent manner. It enables automated deployment and management of infrastructure by using templates written in JSON or YAML.

## Advantages of CloudFormation
- **Automation**: Reduces manual configuration and provisioning time.
- **Consistency**: Ensures the same infrastructure is deployed across multiple environments.
- **Version Control**: Facilitates tracking changes and rollbacks.
- **Dependency Management**: Automatically manages resource dependencies.
- **Cost Optimization**: Identifies unused or unnecessary resources.

## Basic Elements of CloudFormation
1. **Templates**: YAML or JSON files that define AWS resources.
2. **Stacks**: A collection of AWS resources created from a CloudFormation template.
3. **Change Sets**: Preview changes before applying them.
4. **Resources**: Individual AWS components such as EC2, VPCs, IAM roles, and EKS clusters.
5. **Parameters**: Input values provided at runtime to customize templates.
6. **Outputs**: Key information retrieved from created resources.

## Working with Stacks
### Stack Creation
1. Write a CloudFormation template (YAML or JSON).
2. Upload the template to AWS CloudFormation.
3. Define parameters and configurations.
4. Deploy the stack to create resources.

### Stack Updates
- Modify the CloudFormation template.
- Use **Change Sets** to preview changes before applying.
- Deploy the updated stack.

### Stack Deletion
- Delete the stack to remove associated resources.
- Be cautious of dependencies, such as manually created resources that CloudFormation does not manage.

### Rollbacks
- Automatic rollback occurs when a stack creation/update fails.
- Use **stack policies** to protect critical resources from unintended updates.

## Deploying an AWS EKS Cluster using CloudFormation

### Template Overview
The provided CloudFormation template provisions an AWS EKS cluster with two worker nodes. It includes:
- **EKS Cluster**: The Kubernetes control plane.
- **IAM Roles**: Permissions for the cluster and worker nodes.
- **Worker Node Group**: A managed group of EC2 instances running Kubernetes workloads.
- **Networking Components**: VPC and subnets for deployment.

### Breakdown of the CloudFormation Template
#### **Parameters**
Defines user-configurable inputs such as cluster name, Kubernetes version, instance types, and networking details.

```yaml
Parameters:
  ClusterName:
    Type: String
    Default: "eksdemo"

  KubernetesVersion:
    Type: String
    Default: "1.30"

  NodeInstanceType:
    Type: String
    Default: "t3.medium"

  KeyName:
    Type: AWS::EC2::KeyPair::KeyName
    Description: "SSH KeyPair for the worker nodes"

  VpcId:
    Type: AWS::EC2::VPC::Id
    Description: "VPC where EKS will be deployed"

  Subnet1:
    Type: AWS::EC2::Subnet::Id
    Description: "Subnet in us-east-1a"

  Subnet2:
    Type: AWS::EC2::Subnet::Id
    Description: "Subnet in us-east-1b"
```

#### **Resources**
1. **EKSCluster**: Provisions the Kubernetes control plane.

```yaml
Resources:
  EKSCluster:
    Type: "AWS::EKS::Cluster"
    Properties:
      Name: !Ref ClusterName
      Version: !Ref KubernetesVersion
      RoleArn: !GetAtt EKSClusterRole.Arn
      ResourcesVpcConfig:
        SubnetIds:
          - !Ref Subnet1
          - !Ref Subnet2
```

2. **EKSClusterRole**: IAM role for EKS cluster permissions.

```yaml
  EKSClusterRole:
    Type: "AWS::IAM::Role"
    Properties:
      RoleName: !Sub "${ClusterName}-EKS-Role"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: "Allow"
            Principal:
              Service: "eks.amazonaws.com"
            Action: "sts:AssumeRole"
      ManagedPolicyArns:
        - "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
```

3. **NodeGroup**: Manages EC2 worker nodes within the EKS cluster.

```yaml
  NodeGroup:
    Type: "AWS::EKS::Nodegroup"
    Properties:
      ClusterName: !Ref EKSCluster
      NodeRole: !GetAtt NodeInstanceRole.Arn
      Subnets:
        - !Ref Subnet1
        - !Ref Subnet2
      InstanceTypes:
        - !Ref NodeInstanceType
      ScalingConfig:
        MinSize: 2
        MaxSize: 2
        DesiredSize: 2
      AmiType: "AL2_x86_64"
      DiskSize: 20
```

4. **NodeInstanceRole**: IAM role for worker nodes with necessary permissions.

```yaml
  NodeInstanceRole:
    Type: "AWS::IAM::Role"
    Properties:
      RoleName: !Sub "${ClusterName}-Node-Role"
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: "Allow"
            Principal:
              Service: "ec2.amazonaws.com"
            Action: "sts:AssumeRole"
      ManagedPolicyArns:
        - "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
        - "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
        - "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
```

#### **Outputs**
Provides useful information about the created resources.

```yaml
Outputs:
  ClusterName:
    Description: "Name of the EKS Cluster"
    Value: !Ref EKSCluster

  ClusterEndpoint:
    Description: "API Server Endpoint"
    Value: !GetAtt EKSCluster.Endpoint
```

### Handling Errors in CloudFormation
1. **Syntax Errors**: Validate the YAML template before deployment using `aws cloudformation validate-template`.
2. **Insufficient IAM Permissions**: Ensure the IAM roles have required permissions.
3. **Resource Conflicts**: Verify existing resources to prevent conflicts.
4. **Rollback Triggers**: Monitor event logs for failures and resolve them before re-deploying.

### Checking Stack Outputs
- Use AWS Management Console or AWS CLI (`aws cloudformation describe-stacks`) to fetch outputs like cluster endpoints.

## Conclusion and Further Learning
- **Next Steps**: Explore advanced topics like nested stacks, stack sets, and cross-region deployments.
- **Recommended Reading**: AWS CloudFormation documentation and AWS EKS best practices.
- **Hands-on Labs**: Deploy a full Kubernetes application on the provisioned EKS cluster.

By mastering AWS CloudFormation, users can automate infrastructure deployment efficiently, ensuring consistency, scalability, and security in AWS environments.

