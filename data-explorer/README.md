Data Explorer
-------------

https://www.panoptes-data.net

This folder defines a Data Explorer dashboard web service that is main portal for
accessing PANOPTES data.  

This service primarily utilizes the [holoviz.org](https://holoviz.org) ecosystem for
visualization and data interaction.

Each component of the Data Explorer is split into separation "modules", which can be
developed independently of the web service. Modules can be developed, and used, in
jupyter notebooks. 

## Development

### Docker

The web service is prepared as a docker image, which is the service running at
https://www.panoptes-data.net.

To develop and run locally:

```bash
docker build -t data-explorer:develop .
docker run \
    --rm \
    --name data-explorer \
    -p 8080:80 \
    -e BOKEH_APP_URL=http://127.0.0.1:8080/app \
    data-explorer:develop
```

This will make the service available at https://127.0.0.1:8080.

There are two environment variables that can route the traffic depending on your needs.

`BOKEH_APP_URL=127.0.0.1:5006`: Defines the link between the Flask app and the Bokeh app.
This should be entered as an environment variable like in the example above. You need
to include this but probably don't need to change it.

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.

Basically, you can:

```bash
./deploy.sh
```