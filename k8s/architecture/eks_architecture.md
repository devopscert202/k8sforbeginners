# Modernize Applications with Microservices Using Amazon EKS

## Refer this architecture

![image](https://github.com/user-attachments/assets/244b26f8-beb3-4001-b88f-4b6cfcbafa58)

## Architecture Notes

- The Elastic Network Interface is automatically attached to the Amazon Elastic Compute Cloud (Amazon EC2) bare metal (ESXi) hosts in VMware Cloud on AWS during the software-defined data center (SDDC) provisioning.

- Provision fully managed Amazon Elastic Kubernetes Service (Amazon EKS) clusters for different environments (dev/test/production).

- Use tools such as AWS App2Container (App2Container) to accelerate refactoring/rearchitecting applications into containerized microservices.  
  - Use Amazon EKS to manage and automate the testing and deployment of container workloads.

- Transform and containerize legacy systems to modern applications with minimal disruptions.  
  - The existing database tier can keep running on VMware Cloud on AWS to avoid the complexity and delay of database migrations.

- Network Load Balancer integrates with the Kubernetes Ingress Controller, providing a secure and consistent approach for exposing applications.

- Amazon Route 53 resolves incoming requests to Network Load Balancer in the primary AWS Region.

- The dev team commits code to an AWS CodeCommit repository, which initiates AWS CodePipeline to start processing the code changes through the pipeline.

- AWS CodeBuild packages the code changes and dependencies and builds a Docker image.

- The new Docker image is pushed to Amazon Elastic Container Registry (Amazon ECR).

- CodeBuild uses a Kubectl command-line tool to invoke the Kubernetes API and update the image tag for the microservice deployment.

- Kubernetes performs a rolling update of the pods in the application deployment according to the new Docker image specified in Amazon ECR.


### Refer AWS Architecture Center for similar architectures.
