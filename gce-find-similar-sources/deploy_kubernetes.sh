#!/bin/bash -e

echo "Deploying to Kubernetes cluster"
kubectl apply -f similar-source-finder-deployment.yaml

echo "Listing current deployments:"
kubectl get deployments
