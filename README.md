PANOPTES Network
================

- [PANOPTES Network](#panoptes-network)
- [Services](#services)
  - [Deploying services](#deploying-services)


Software related to the wider PANOPTES network that ties the individual units together.
This is a repository to host the various Google Cloud Platform services.

Each subfolder defines a different service. 

Each service is either a [Cloud Function](https://cloud.google.com/functions) or a [Cloud Run](https://cloud.google.com/run) instance, however all services are defined as web services that respond to HTTP JSON requests.

Most services do not allow unauthenticated requests. Services largely communicate with each other via [PubSub](https://cloud.google.com/pubsub/) messages.

See the README for a specific service for more details. See the [Services](#services) section for a list of services.

# Services
<a href="#" id="services"></a>

There are a few different categories of services that are in use on the panoptes-network.

| Service                                        | Trigger | Description                                                     |
| ---------------------------------------------- | ------- | --------------------------------------------------------------- |
| [`image-uploaded`](image-uploaded/README.md)   | Bucket  | Simple foward to next service based on file type.               |
| [`compress-fits`](compress-fits/README.md)     | PubSub  | Compresses all `.fits` to `.fits.fz`.                           |
| [`make-rgb-fits`](make-rgb-fits/README.md)     | PubSub  | Makes interpolated RGB `.fits` from `.CR2` file.                |
| [`record-image`](record-image/README.md)       | PubSub  | Records header and metadata from `.fits.fz` files.              |
| [`lookup-field`](lookup-field/README.md)       | Http    | A simple service to lookup astronomical sources by search term. |
| [`get-fits-header`](get-fits-header/README.md) | Http    | Returns the FITS headers for a given file.                      |

## Deploying services
<a href="#" id="deploying-services"></a>
<a href="#" id="deploy"></a>

You can deploy any service using `bin/deploy` from the top level directory. The
command takes the service name as a parameter:

```bash
$ bin/deploy record-image
```