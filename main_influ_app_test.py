import argparse
import os
import threading
import time

import dash
import dash_bootstrap_components as dbc
from dash import CeleryManager, DiskcacheManager, Input, Output, dcc, html

from insaflu_upload.connectors import ConnectorDocker, ConnectorParamiko
from insaflu_upload.insaflu_upload import InfluConfig, InsafluPreMain
from insaflu_upload.records import UploadAll, UploadLast
from insaflu_upload.upload_utils import InsafluUploadRemote
from mfmc.records import ProcessActionMergeWithLast


def get_arguments():

    parser = argparse.ArgumentParser(description="Process fastq files.")
    parser.add_argument(
        "-i", "--in_dir", help="Input directory", required=True)
    parser.add_argument("-o", "--out_dir",
                        help="Output directory", required=True)
    parser.add_argument("-t", "--tsv_t_n",
                        help="TSV template name", default="templates_comb.tsv")
    parser.add_argument("-d", "--tsv_t_dir",
                        help="TSV template directory", required=True)
    parser.add_argument("-s", "--sleep", help="Sleep time between checks in monitor mode", default=60,
                        type=int)

    parser.add_argument("-n", "--tag", help="name tag, if given, will be added to the output file names",
                        required=False, type=str, default="")

    parser.add_argument("--config", help="config file",
                        required=False, type=str, default="config.ini")

    parser.add_argument("--merge", help="merge files", action="store_true")

    parser.add_argument('--upload',
                        default='last',
                        choices=['last', 'all'],
                        help='file upload stategy (default: all)',)

    parser.add_argument('--connect',
                        default='docker',
                        choices=['docker', 'ssh'],
                        help='file upload stategy (default: docker)',)

    parser.add_argument(
        "--keep_names", help="keep original file names", action="store_true")

    parser.add_argument(
        "--monitor", help="monitor directory until killed", action="store_true")

    parser.add_argument(
        "--televir", help="deploy televir pathogen identification on each sample", action="store_true"
    )

    return parser.parse_args()


def generate_compressor():

    args = get_arguments()

    # create connector

    if args.connect == 'docker':
        connector = ConnectorDocker(args.config)

    else:
        connector = ConnectorParamiko(args.config)

    insaflu_upload = InsafluUploadRemote(connector, args.config)

    # determine upload strategy
    if args.upload == 'last':
        upload_strategy = UploadLast
    else:
        upload_strategy = UploadAll

    # determine actions
    actions = []
    if args.merge:
        actions.append(ProcessActionMergeWithLast)

    # create run metadata

    run_metadata = InfluConfig(
        output_dir=args.out_dir,
        name_tag=args.tag,
        uploader=insaflu_upload,
        upload_strategy=upload_strategy,
        actions=actions,
        tsv_temp_name=args.tsv_t_n,
        metadata_dir=args.tsv_t_dir,
        keep_name=args.keep_names,
        deploy_televir=args.televir
    )

    # run

    influ_compressor = InsafluPreMain(
        args.in_dir,
        run_metadata,
        args.sleep
    )

    return influ_compressor


if 'REDIS_URL' in os.environ:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery
    celery_app = Celery(
        __name__, broker=os.environ['REDIS_URL'], backend=os.environ['REDIS_URL'])
    background_callback_manager = CeleryManager(celery_app)

else:
    # Diskcache for non-production apps when developing locally
    import diskcache
    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)

####################
compressor = generate_compressor()

lock = threading.Lock()
if __name__ == '__main__':

    global_figure = dict(data=[dict(x=[1, 2, 3], y=[1, 2, 3])])

    app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

    sidebar = html.Div(
        [
            html.P('Sidebar')
        ]
    )

    content = html.Div([

        html.Div(children=[
            html.Button(id="button_id", children="Begin Job!"),
            html.Label("statistic across taxids"),
            html.Br(),
            dcc.Graph(id='plot_max'),
            # dcc.Interval(
            #    id='interval-component',
            #    interval=40 * 1000,  # in milliseconds
            # ),

        ], style={'padding': 10, 'flex': 1}),

    ], style={'display': 'flex', 'flex-direction': 'row'})

    @dash.callback(
        output=Output("plot_max", "figure"),
        inputs=Input("button_id", "n_clicks"),
        background=True,
        manager=background_callback_manager,
        # progress=Output("plot_max", "figure"),
        prevent_initial_call=True

    )
    def update_figure_global(n_intervals):
        # global compressor

        # lock.acquire()
        # set_progress(global_figure)

        #

        # time.sleep(5)
        # return "hello"
        print("hi")
        fig = compressor.run_return_plot()
        print("done")

        # fig = dict(data=[dict(x=[1, 2, 3], y=[1, 2, 3])])

        # print("update_figure_global")
        # lock.release()
        return fig

    app.layout = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(sidebar, width=3, className='bg-light'),
                    dbc.Col(content, width=9)
                ],
                style={"height": "100vh"}
            ),
        ],
        fluid=True
    )

    app.run_server(debug=True)
