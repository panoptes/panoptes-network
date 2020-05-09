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

### Docker

The web service is prepared as a docker image, which is the service running at
https://panoptes-data.net.

To develop and run locally:

```bash
docker build -t data-explorer:develop .
docker run --rm --name data-explorer -p 8080:80 -d data-explorer:develop
```

This will make the service available at https://127.0.0.1:8080.

### Development

For developing locally, the Firestore emulator should be installed rather than using
real network access. Read the [setup instructions](https://firebase.google.com/docs/rules/emulator-setup) for details.

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.

Basically, you can:

```python
./deploy.sh
```