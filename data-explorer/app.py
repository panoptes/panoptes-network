import os
from threading import Thread

import panel as pn
from bokeh.embed import server_document
from bokeh.server.server import Server
from flask import Flask, render_template
from tornado.ioloop import IOLoop

from .modules.observations import ObservationsExplorer
from .modules.stats import Stats

public_app_url = os.getenv('PUBLIC_APP_URL', 'https://www.panoptes-data.net/')

app = Flask(__name__)


def data_explorer_app(doc):
    tmpl = pn.Template('')

    # Load the modules we want.
    obs_explorer = ObservationsExplorer(name='Search Observations')
    stats = Stats(name='Overall Stats')

    def _stat_card(label, value):
        return pn.pane.HTML(f'''
        <div class="card">
            <div class="card-body">
                <h1><span class="badge badge-info">{value}</span></h1>
                <h3>{label}</h3>
            </div>
        </div>
        ''')

    stats_row = pn.Row(
        pn.Column(
            pn.Row(
                _stat_card('Hours Exptime', int(stats.df['Total Hours'].sum())),
                _stat_card('Total Images', int(stats.df['Images'].sum())),
            ),
            pn.Row(
                _stat_card('Observations', int(stats.df['Observations'].sum())),
                _stat_card('Contributing Units', len(stats.df['Unit'].unique())),
            )
        ),
        stats.widget_box,
        stats.plot,
        sizing_mode='stretch_both',
    )

    observations_row = pn.Row(
        obs_explorer.widget_box,
        obs_explorer.table,
        # pn.Column(
        #     obs_explorer.selected_title,
        #     obs_explorer.image_preview,
        #     obs_explorer.table_download_button,
        #     obs_explorer.sources_download_button
        # ),
        sizing_mode='stretch_both',
    )

    main_layout = pn.Column(
        stats_row,
        observations_row
    )

    tmpl.add_panel('mainArea', main_layout)

    return tmpl.server_doc(doc=doc)


@app.route('/', methods=['GET'])
def bkapp_page():
    base_app_url = os.getenv('BOKEH_APP_URL', 'https://www.panoptes-data.net/app')

    bokeh_script = server_document(base_app_url, relative_urls=True)
    return render_template("main.html", bokeh_script=bokeh_script, template="Flask")


@app.route('/ping')
def ping():
    return 'pong'


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/app': data_explorer_app},
                    io_loop=IOLoop(),
                    allow_websocket_origin=[
                        '127.0.0.1:5000',
                        '127.0.0.1:8080',
                        'www.panoptes-data.net',
                    ])
    server.start()
    server.io_loop.start()


Thread(target=bk_worker).start()

if __name__ == '__main__':
    print('Opening single process Flask app with embedded Bokeh application on http://127.0.0.1:5000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run(port=8000)
