
import os

import dash
import dash_bootstrap_components as dbc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from dash import Dash, Input, Output, dcc, html


def get_accid_description(accid):
    taxid = results_df[results_df["accid"] == accid]["taxid"].unique()[0]
    sample_df = results_df[results_df["accid"] == accid]
    return f"{accid} - {taxid} - {sample_df['description'].unique()[0]}"


def get_accession_drop_down_info(accids):

    accid_description_tuples = [
        (accid, get_accid_description(accid)) for accid in accids]

    return accid_description_tuples


def get_sample_name_from_merged(merged):
    file_name = os.path.basename(merged)
    file_name, ext = os.path.splitext(file_name)
    if ext == ".gz":
        file_name, ext = os.path.splitext(file_name)

    return file_name


def get_sample_runs(sample_name, results_df):
    sample_df = results_df[results_df["sample_name"] == sample_name]
    return sample_df["run_id"].unique()


def get_accid_stats(accid_list, sample_names, results_df):
    # get accid stats by sample

    accid_stats = pd.DataFrame()

    for accid in accid_list:
        for sample_name in sample_names:

            sample_df = results_df[results_df["sample_name"] == sample_name]
            time_elapsed = sample_df["time_elapsed"].unique()[0]
            description = sample_df["description"].unique()[0]
            taxid = sample_df["taxid"].unique()[0]
            sample_df = sample_df[sample_df["accid"] == accid]

            if sample_df.shape[0] == 0:
                sample_stat = pd.DataFrame({"coverage": [np.nan], "depth": [np.nan], "ref_proportion": [
                    np.nan], "taxid": [taxid], "mapped_reads": [np.nan],
                    "description": [description], "time_elapsed": [time_elapsed]})
            else:
                sample_stat = sample_df[
                    [
                        "coverage",
                        "depth",
                        "ref_proportion",
                        "description",
                        "taxid",
                        "mapped_reads",
                        "time_elapsed",
                        "leaf_id"]
                ]

            sample_stat.insert(0, "accid", accid)
            sample_stat.insert(0, "sample_name", sample_name)

            accid_stats = pd.concat([accid_stats, sample_stat])

    return accid_stats


metadir = "/home/bioinf/Desktop/CODE/INSaFLU-TELEVIR_cml_upload/test_new"
processed_file = os.path.join(metadir, "processed.tsv")

results_dir = "/home/bioinf/Desktop/CODE/INSaFLU-TELEVIR_cml_upload/test_new"
results_file = os.path.join(results_dir, "barcode_01_another.tsv")

plots_dir = "/home/bioinf/Desktop/CODE/INSaFLU-TELEVIR_cml_upload/test_new/plots"

if not os.path.exists(plots_dir):
    os.makedirs(plots_dir)

processed_df = pd.read_csv(processed_file, sep="\t")
results_df = pd.read_csv(results_file, sep="\t")


processed_df["sample_name"] = processed_df.apply(
    lambda x: get_sample_name_from_merged(x["merged"]), axis=1)


results_df["time_elapsed"] = results_df["sample_name"].map(
    processed_df.set_index("sample_name")["time"])


stats = ["coverage", "depth", "ref_proportion", "mapped_reads"]
sample_names = results_df["sample_name"].unique()
accids = results_df["accid"].unique()


accid_description_tuples = get_accession_drop_down_info(accids)

accid_stats = get_accid_stats(accids, sample_names, results_df)

print(accid_stats)
first_accid = ""

if len(accids) > 0:
    first_accid = accid_description_tuples[0]
print(first_accid)

###


def plot_run_diversity():

    data_diversity = pd.DataFrame()

    for time_elapsed in results_df["time_elapsed"].unique():
        for leaf_id in results_df["leaf_id"].unique():
            sample_df = results_df[results_df["time_elapsed"] == time_elapsed]
            sample_df = sample_df[sample_df["leaf_id"] == leaf_id]

            count_mean = [df.shape[0]
                          for _, df in sample_df.groupby("taxid")]

            data_diversity = pd.concat(
                [data_diversity, pd.DataFrame({"time_elapsed": [time_elapsed] * len(count_mean), "count_mean": count_mean})])

    print(data_diversity)

    fig = px.box(data_diversity, x="time_elapsed", y="count_mean",
                 points="all", hover_data=data_diversity.columns, template="seaborn")

    fig.update_layout(
        xaxis_title="Time elapsed (seconds)",
        yaxis_title="Number of taxids",
        legend=dict(
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,

        ))

    return fig


fig_diversity = plot_run_diversity()

####


def plot_accid_stats(first_accid, stats, accid_stats):
    app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

    sidebar = html.Div(
        [
            html.P('Sidebar')
        ]
    )

    content = html.Div([

        html.Div(children=[

            html.Label("statistic across taxids"),
            dcc.Dropdown(stats, stats[0], id="stat_global"),

            html.Br(),
            dcc.Graph(id='plot_max'),

            html.Label('global_diversity'),

            dcc.Graph(id='plot_run', figure=fig_diversity),
            html.Label('accid'),
            dcc.Dropdown(options=[{
                'label': x[1],
                'value': x[0]
            } for x in accid_description_tuples], value=first_accid[0], id="accid"),
            html.Br(),

            html.Label('stat'),
            dcc.Dropdown(stats, stats[0], id="stat"),

            html.Br(),
            dcc.Graph(id='plot_run'),
        ], style={'padding': 10, 'flex': 1}),

    ], style={'display': 'flex', 'flex-direction': 'row'})

    @app.callback(
        Output('plot_max', 'figure'),
        Input('stat_global', 'value'))
    def update_figure_global(stat):

        data_max = accid_stats.groupby(["accid", "time_elapsed"])[
            stat].max().reset_index()

        fig = px.line(data_max, x="time_elapsed", y=stat,
                      color="accid", template="seaborn")

        fig.update_layout(transition_duration=500,
                          xaxis_title="Time elapsed (seconds)",
                          yaxis_title=stat,
                          title={
                              'text': f"{stat}",
                              'y': 0.9,
                              'x': 0.5,
                              'xanchor': 'center',
                              'yanchor': 'top'})
        return fig

    @ app.callback(
        Output('plot_run', 'figure'),
        Input('accid', 'value'),
        Input('stat', 'value'))
    def update_figure(accid, stat):

        filtered_df = accid_stats[
            (accid_stats["accid"] == accid)
        ].sort_values("time_elapsed")

        fig = px.line(filtered_df, x="time_elapsed", y=stat,
                      color="leaf_id", template="seaborn")

        fig.update_layout(transition_duration=500,
                          xaxis_title="Time elapsed (seconds)",
                          yaxis_title=stat,
                          title={
                              'text': f"{accid} - {stat}",
                              'y': 0.9,
                              'x': 0.5,
                              'xanchor': 'center',
                              'yanchor': 'top'})

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


if __name__ == '__main__':
    plot_accid_stats(first_accid, stats, accid_stats)
