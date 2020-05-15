Data Explorer
-------------

https://panoptes-data.net

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
docker run --rm --name data-explorer -p 8080:80 -d data-explorer:develop
```

This will make the service available at https://127.0.0.1:8080.

There are two environment variables that can route the traffic depending on your needs.

`BOKEH_APP_URL=127.0.0.1:5006`: Defines the link between the Flask app and the Bokeh app.
This should rarely need to be changed as the two services should be running on the same
server local to each other.

`PUBLIC_APP_URL=www.panoptes-data.net`: Defines the actual link to use. If developing
locally you should change this to `127.0.0.1:8080` where 8080 is mapped to the port in
the `docker run` command above.

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.

Basically, you can:

```python
./deploy.sh
```