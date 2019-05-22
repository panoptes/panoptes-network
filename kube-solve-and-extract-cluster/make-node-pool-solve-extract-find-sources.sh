#!/bin/bash -e

gcloud beta container \
	--project "panoptes-survey" clusters create "solve-extract-find-cluster" \
	--zone "us-central1-a" \
	--no-enable-basic-auth \
	--cluster-version "1.12.7-gke.10" \
	--machine-type "n1-standard-1" \
	--image-type "COS_CONTAINERD" \
	--disk-type "pd-standard" \
	--disk-size "100" \
	--node-labels stage=solve-extract,use=piaa \
	--metadata disable-legacy-endpoints=true,google-logging-enabled=true \
	--scopes "https://www.googleapis.com/auth/devstorage.read_write","https://www.googleapis.com/auth/sqlservice.admin","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/pubsub","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
	--preemptible \
	--num-nodes "3" \
	--enable-stackdriver-kubernetes \
	--no-enable-ip-alias \
	--network "projects/panoptes-survey/global/networks/default" \
	--enable-autoscaling \
	--min-nodes "1" \
	--max-nodes "5" \
	--addons HorizontalPodAutoscaling,HttpLoadBalancing \
	--enable-autoupgrade \
	--enable-autorepair \
	--labels use=piaa \
	--enable-vertical-pod-autoscaling

gcloud beta container \
	--project "panoptes-survey" node-pools create "find-similar-sources-pool" \
	--cluster "solve-extract-find-cluster" \
	--zone "us-central1-a" \
	--node-version "1.12.7-gke.10" \
	--machine-type "n1-standard-2" \
	--image-type "COS_CONTAINERD" \
	--disk-type "pd-standard" \
	--disk-size "100" \
	--node-labels stage=find-similar-sources,use=piaa \
	--metadata disable-legacy-endpoints=true,google-logging-enabled=true \
	--scopes "https://www.googleapis.com/auth/devstorage.read_write","https://www.googleapis.com/auth/sqlservice.admin","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/pubsub","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
	--preemptible \
	--num-nodes "3" \
	--enable-autoscaling \
	--min-nodes "1" \
	--max-nodes "5" \
	--enable-autoupgrade \
	--enable-autorepair
