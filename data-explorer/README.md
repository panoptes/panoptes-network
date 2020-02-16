# PANOPTES Data Explorer

- [PANOPTES Data Explorer](#panoptes-data-explorer)
  - [Data Explorer](#data-explorer)
  - [Development](#development)
    - [Setup](#setup)
      - [Environment](#environment)
      - [Web App](#web-app)
    - [Develop](#develop)
    - [Deploy](#deploy)

## Data Explorer

The PANOPTES Data Explorer can be used to find information about PANOPTES data.

The PANOPTES Data Explorer is the main source for public access to the PANOPTES data. This includes science data, both raw and processed data products, as well as metadata about the PANOPTES units, their observations, weather, etc.

The Data Explorer uses the following:

- JavaScript:
  - [Nodejs](https://nodejs.org) (runtime and package management)
  - [TypeScript](https://www.typescriptlang.org/) (language version)
  - [Vue](https://vuejs.org) (web framework)
  - [Nuxt](https://nuxtjs.org/) (Vue scaffolding and project management)
  - [Vuetify](https://vuetifyjs.com/en/getting-started/quick-start) (Vue UI framework)

## Development

For development you need to start the local firebase emulators and the development web server. These need to be started in separate terminals and will stay running while you do development.

```bash
# Run the firebase emulators
npm run emulate
```

The emulator must be populated each time it is started:

```bash
npm run emulate-init
```

In a separate terminal:

```bash
# Run the development server
npm run web-dev
```

This should output a message similar to:

```bash
 READY  Server listening on http://localhost:3000
```

Visit the url in your web browser. There are various plugins for Chrome and Firefox that make debugging Vue applications easier.

### Deploy

See [Deployment](../README.md#deploy) in main README for preferred deployment method.
