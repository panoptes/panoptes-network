#!/bin/bash -e

gcloud container node-pools create \
	similar-source-finder-pool \
	--cluster solve-and-extract-cluster \
	--zone us-central1-a \
	--enable-autorepair \
	--enable-autoupgrade \
	--machine-type n1-standard-16 \
	--preemptible \
	--node-labels=for=similar-sources \
	--num-nodes 2 \
	--enable-autoscaling  \
	--max-nodes=3 \
	--min-nodes=1 \
	--scopes=storage-rw,logging-write,pubsub
