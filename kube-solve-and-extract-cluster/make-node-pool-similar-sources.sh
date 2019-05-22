#!/bin/bash -e

gcloud container node-pools create \
	similar-source-finder-pool \
	--cluster solve-extract-find-cluster \
	--zone us-central1-a \
	--enable-autorepair \
	--enable-autoupgrade \
	--machine-type n1-standard-16 \
	--preemptible \
	--node-labels=use=piaa \
	--num-nodes 2 \
	--enable-autoscaling  \
	--max-nodes=5 \
	--min-nodes=1 \
	--scopes=storage-rw,logging-write,pubsub
