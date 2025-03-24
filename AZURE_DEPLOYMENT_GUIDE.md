# Azure Container Service Deployment Guide

This guide provides comprehensive instructions for deploying the Supply Chain Management application to Azure Container Service (ACS).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Container Registry Setup](#container-registry-setup)
4. [Application Containerization](#application-containerization)
5. [Azure Container Service Configuration](#azure-container-service-configuration)
6. [Deployment Process](#deployment-process)
7. [Security Configuration](#security-configuration)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

- Azure subscription
- Azure CLI installed
- Docker Desktop installed
- kubectl command-line tool
- Git

## Environment Setup

1. Install Azure CLI:
   ```bash
   # Windows (PowerShell)
   winget install Microsoft.AzureCLI
   # Verify installation
   az --version
   ```

2. Login to Azure:
   ```bash
   az login
   ```

3. Create Resource Group:
   ```bash
   az group create --name scm-resource-group --location eastus
   ```

## Container Registry Setup

1. Create Azure Container Registry:
   ```bash
   az acr create --resource-group scm-resource-group \
                 --name scmcontainerregistry \
                 --sku Basic
   ```

2. Login to Container Registry:
   ```bash
   az acr login --name scmcontainerregistry
   ```

## Application Containerization

### Frontend Service

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Build Docker image:
   ```bash
   docker build -t scmcontainerregistry.azurecr.io/frontend:latest .
   ```

3. Push to Azure Container Registry:
   ```bash
   docker push scmcontainerregistry.azurecr.io/frontend:latest
   ```

### Backend Service

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Build Docker image:
   ```bash
   docker build -t scmcontainerregistry.azurecr.io/backend:latest .
   ```

3. Push to Azure Container Registry:
   ```bash
   docker push scmcontainerregistry.azurecr.io/backend:latest
   ```

## Azure Container Service Configuration

1. Create AKS cluster:
   ```bash
   az aks create \
       --resource-group scm-resource-group \
       --name scm-aks-cluster \
       --node-count 2 \
       --generate-ssh-keys \
       --attach-acr scmcontainerregistry
   ```

2. Get credentials:
   ```bash
   az aks get-credentials --resource-group scm-resource-group --name scm-aks-cluster
   ```

## Deployment Process

1. Apply Kubernetes configurations:
   ```bash
   # Create namespace
   kubectl create namespace scm

   # Apply configurations
   kubectl apply -f k8s/
   ```

2. Verify deployment:
   ```bash
   kubectl get pods -n scm
   kubectl get services -n scm
   ```

## Security Configuration

1. Enable Azure AD integration:
   ```bash
   az aks update -g scm-resource-group -n scm-aks-cluster --enable-aad
   ```

2. Configure network policies:
   ```bash
   az aks update \
       --resource-group scm-resource-group \
       --name scm-aks-cluster \
       --network-policy azure
   ```

3. Enable encryption at rest:
   ```bash
   az aks update \
       --resource-group scm-resource-group \
       --name scm-aks-cluster \
       --enable-encryption-at-host
   ```

## Monitoring and Maintenance

1. Enable monitoring:
   ```bash
   az aks enable-addons \
       --resource-group scm-resource-group \
       --name scm-aks-cluster \
       --addons monitoring
   ```

2. View monitoring data:
   ```bash
   az aks show \
       --resource-group scm-resource-group \
       --name scm-aks-cluster
   ```

3. Set up alerts:
   - Navigate to Azure Portal
   - Go to your AKS cluster
   - Select 'Alerts' under Monitoring
   - Configure alert rules for:
     - CPU usage
     - Memory usage
     - Pod status
     - Node status

## Troubleshooting

1. Check pod logs:
   ```bash
   kubectl logs <pod-name> -n scm
   ```

2. Check pod status:
   ```bash
   kubectl describe pod <pod-name> -n scm
   ```

3. Common issues:
   - Image pull errors: Check ACR credentials
   - Pod pending: Check resource constraints
   - Service unreachable: Check service configuration

## Scaling

1. Manual scaling:
   ```bash
   kubectl scale deployment <deployment-name> --replicas=3 -n scm
   ```

2. Auto-scaling:
   ```bash
   kubectl autoscale deployment <deployment-name> \
       --min=2 \
       --max=5 \
       --cpu-percent=80 \
       -n scm
   ```

## Backup and Disaster Recovery

1. Enable backup:
   ```bash
   az aks update \
       --resource-group scm-resource-group \
       --name scm-aks-cluster \
       --enable-managed-identity
   ```

2. Configure backup policy:
   - Navigate to Azure Portal
   - Go to your AKS cluster
   - Select 'Backup' under Operations
   - Configure backup frequency and retention

## Cost Management

1. View current costs:
   ```bash
   az consumption usage list \
       --subscription <subscription-id> \
       --start-date <start-date> \
       --end-date <end-date>
   ```

2. Set up budget alerts in Azure Portal:
   - Go to Cost Management + Billing
   - Select your subscription
   - Create budget and alerts

## Best Practices

1. Resource Management
   - Use resource quotas
   - Implement auto-scaling
   - Regular monitoring of resource usage

2. Security
   - Regular security updates
   - Network policy implementation
   - Secret management

3. Maintenance
   - Regular backups
   - Update strategy
   - Monitoring and alerting

## Support and Resources

- [Azure Documentation](https://docs.microsoft.com/azure)
- [AKS Documentation](https://docs.microsoft.com/azure/aks)
- [Kubernetes Documentation](https://kubernetes.io/docs)
- [Container Registry Documentation](https://docs.microsoft.com/azure/container-registry)