# PANOPTES Network

Software related to the wider PANOPTES network that ties the individual units together.
This is a repository to host the various Google Cloud Platform services.

Each subfolder defines a different service. Services communicate with each other
via [PubSub](https://cloud.google.com/pubsub/) messages. See the README for a
specific service for more details.

## Pipeline

Any file that is uploaded to the Google storage bucket will automatically trigger
a series of of basic cleaning and reduction steps to prepare for submitting to
the PANOPTES pipeline, as well as to make available for public consumption.

The services defined in this repo control the different "nodes" of the pipeline,
which is currently spread across a variety of technologies.

![PIAA Diagram](resources/PIAA_diagram.png)

### Services

| Service                                      | Trigger | Description |
|----------------------------------------------|---------|--------------|
| [`image-uploaded`](image-uploaded/README.md) | Bucket Upload | Simple foward to next service based on file type.
| [`compress-fits`](compress-fits/README.md)   | PubSub | Compresses all `.fits` to `.fits.fz`.
| [`make-rgb-fits`](make-rgb-fits/README.md)   | PubSub | Makes interpolated RGB images from `.CR2` file.
| [`record-image`](record-image/README.md)     | PubSub |  Records header and metadata from `.fits.fz` files.

#### Deploying services

You can deploy any service using `bin/deploy` from the top level directory. The
command takes the service name as a parameter:

```bash
$ bin/deploy record-image
```
