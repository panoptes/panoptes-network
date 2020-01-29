# PANOPTES Data Explorer

- [PANOPTES Data Explorer](#panoptes-data-explorer)
  - [Data Explorer](#data-explorer)
  - [Development](#development)
    - [Setup](#setup)
      - [Environment](#environment)
      - [Web App](#web-app)
    - [Development](#development-1)
    - [Deploy](#deploy)

## Data Explorer

The PANOPTES Data Explorer can be used to find information about PANOPTES data.

The PANOPTES Data Explorer is the main source for public access to the PANOPTES data. This includes science data, both raw and processed data products, as well as metadata about the PANOPTES units, their observations, weather, etc.

The Data Explorer uses the following:

- JavaScript:
  - [Nodejs](https://nodejs.org) (runtime and package management)
  - [TypeScript](https://www.typescriptlang.org/) (language version)
  - [Vue](https://vuejs.org) (web framework)
  - [Vue CLI](https://cli.vuejs.org/guide/) (web framework bootstrap)
  - [Vuetify](https://vuetifyjs.com/en/getting-started/quick-start) (web UI framework)

## Development

### Setup

#### Environment

You must first have an environment that has an appropriate version of nodejs installed.  The easiest way
to do this with an [Anaconda](https://www.anaconda.com/) environment. Assuming you already have `conda` installed (see link for details):

```bash
conda create -n panoptes-data-explorer python=3.7 nodejs=10
```

Then when before working on the Data Explorer:

```bash
conda activate panoptes-data-explorer
```

#### Web App

For an initial setup the package dependencies must be installed from the root directory of the web app:

```bash
# Install dependencies
npm run install
```

### Development

For development you need to start the local firebase emulators and the development web server. These need to be started in separate terminals and will stay running while you do development.

```bash
# Run the firebase emulators
npm run emulate
```

In a separate terminal:

```bash
# Run the development server
npm run serve
```

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
