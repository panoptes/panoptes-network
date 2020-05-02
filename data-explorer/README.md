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

The web service is prepared as a docker image. By default this will launch the `bokeh`
server with 4 processes. 

The service is based upon the Google [BigQuery Bokeh Dashboard](https://cloud.google.com/solutions/bokeh-and-bigquery-dashboards)
tutorial.

### Development

For developing locally, the Firestore emulator should be installed rather than using
real network access. Read the [setup instructions](https://firebase.google.com/docs/rules/emulator-setup) for details.