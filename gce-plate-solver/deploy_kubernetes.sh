#!/bin/bash -e

echo "Deploying plate-solver to Kubernetes cluster"
kubectl apply -f solve-extract-deployment.yaml

echo "Listing current deployments:"
kubectl get deployments
