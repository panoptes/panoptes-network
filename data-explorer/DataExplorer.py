#!/usr/bin/env python

import panel as pn

from modules.observations import ObservationsExplorer

pn.extension()

template = """
{% extends base %}

<!-- goes in body -->
{% block postamble %}
<link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
{% endblock %}

<!-- goes in body -->
{% block contents %}
{{ app_title }}
<br>
<div class="container-fluid">
  <div class="row">
    <div class="col-sm">
      {{ embed(roots.obsExplorer) }}
    </div>
    <div class="col-sm">
        <div class="card" style="width: 20rem;">
          <img src="https://projectpanoptes.org/uploads/2018/12/17/pan-head.png" class="card-img-top" alt="PANOPTES Logo">
          <div class="card-body">
            <h5 class="card-title">Cool Feature!</h5>
            <p class="card-text">Could show a random image from last night.</p>
          </div>
        </div>  
    </div>
  </div>
</div>
{% endblock %}
"""

tmpl = pn.Template(template)
obs_explorer = ObservationsExplorer(name='Observations Explorer')

tmpl.add_variable('app_title', '<h1>PANOPTES Data Explorer</h1>')

tmpl.add_panel('obsExplorer',
               pn.Column(
                   pn.Row(
                       obs_explorer.widget_box,
                       obs_explorer.table)
               )
               )

tmpl.servable()
