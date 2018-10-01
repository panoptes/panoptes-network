# POE - PANOPTES Observations Explorer

This folder contains a web appliation that is used for exploring the 
PANOPTES observations. The application can be run locally (see [Build Setup](#build_setup) below) for development or can be built into a single html.

This web application is set up mostly as a [Vuejs](https://vuejs.org/) app.
It requires some knowledge of web technologies for development.

## Build Setup
<a id="build_setup"></a>

```bash
# install dependencies
npm install

# serve with hot reload at localhost:8080
npm run dev

# build for production with minification
npm run build

# build for production and view the bundle analyzer report
npm run build --report
```

For a detailed explanation on how things work, check out the [guide](http://vuejs-templates.github.io/webpack/) and [docs for vue-loader](http://vuejs.github.io/vue-loader).

## Deployment

After building for production above, there will be a `dist` folder that
can be served from a Google Storage Bucket as a single static file. After
uploading the new files the permissions must be changed to make them public:

> See also: [Google documentation](https://cloud.google.com/storage/docs/hosting-static-website)

```bash
# Upload to www.panoptes-data.net bucket
gsutil rsync -R dist gs://www.panoptes-data.net/

# Update permissions
gsutil acl ch -u AllUsers:R -r gs://www.panoptes-data.net/index.html
gsutil acl ch -u AllUsers:R -r gs://www.panoptes-data.net/static/
```