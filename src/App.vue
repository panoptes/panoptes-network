<template>
  <v-app id="inspire">
    <v-navigation-drawer
      v-model="drawer"
      :clipped="$vuetify.breakpoint.lgAndUp"
      app
    >
      <v-list dense>
        <template v-for="item in items">
          <v-list-item
            :key="item.text"
            link
          >
            <v-list-item-action>
              <v-icon>{{ item.icon }}</v-icon>
            </v-list-item-action>
            <v-list-item-content>
              <v-list-item-title>
                <router-link
                  :to="{ name: item.link }">
                  {{ item.text }}
                </router-link>
              </v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </template>
      </v-list>
    </v-navigation-drawer>

    <v-app-bar
      :clipped-left="$vuetify.breakpoint.lgAndUp"
      app
      color="blue darken-3"
      dark
    >
      <v-app-bar-nav-icon @click.stop="drawer = !drawer" />
      <v-toolbar-title
        style="width: 300px"
        class="ml-0 pl-4"
      >
        <span class="hidden-sm-and-down">{{ title }}</span>
      </v-toolbar-title>
      <v-text-field
        flat
        solo-inverted
        hide-details
        prepend-inner-icon="mdi-magnify"
        label="Enter PICID, Observation ID, Image ID, RA/Dec, etc."
        class="hidden-sm-and-down"
      />
      <v-spacer />
      <v-btn
        icon
        large
      >
        <v-avatar
          size="32px"
          item
        >
          <v-img
            src="https://projectpanoptes.org/img/logo-white.png"
            :alt="title"
          /></v-avatar>
      </v-btn>
    </v-app-bar>
    <v-content>
      <v-container
        fluid
      >
        <v-row
          align="center"
          justify="center"
        >
        <router-view></router-view>
        </v-row>
      </v-container>
    </v-content>
  </v-app>
</template>

<script>
  export default {
    props: {
      source: String,
    },
    data: () => ({
      title: 'PANOPTES Data Explorer',
      drawer: true,
      items: [
        // { icon: 'mdi-robot', text: 'Units', link: 'units' },
        { icon: 'mdi-star-box-multiple-outline', text: 'Observations', link: 'observations' },
        { icon: 'mdi-star-face', text: 'Stars', link: 'stars' },
      ],
    }),
  }
</script>
