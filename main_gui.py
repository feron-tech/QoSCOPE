import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import dash
from dash import Input, Output, State, html, dcc, callback , dash_table
import plotly.express as px
import gparams
import plotly.graph_objects as go
from helper import Helper
import zipfile
import zlib
import os
import shutil
# Initialize the app - constructor
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

# App layout
app.layout = html.Div(children=[

    html.Div([

    html.Div(id='hidden-div', style={'display': 'none'}),

    html.Div(children=[

        # Row 1: Title of UI
        dbc.Row(
            dbc.Col(
                html.Div([
                    html.Label('Golden Unit Monitoring', style={'color': 'Black', 'font-size': 55}),
                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center', 'justify-content': 'center'}),

                width={"size": 6, "offset": 3},
            )
        ),

        # Row 2: Settings overall
        dbc.Row(
            [
                # Col 1 - NETWORK SETTINGS & MEASUREMENT SETUP
                dbc.Col(
                    [
                        # Network settings
                        dbc.Row(
                            [
                                html.Div([
                                    html.Label('Network settings', style={'color': 'Black', 'font-size': 45}),
                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                          'justify-content': 'center'}),

                                html.Hr(style={'borderWidth':'0.3vh','width':'100%','borderColor':'#000000','opacity':'unset'}),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('Client IP',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='ntw_client_ip', type='text', value='10.1.1.2',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('Server IP',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='ntw_server_ip', type='text', value='172.25.2.172',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('APN',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='ntw_apn', type='text', value='internet',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('Modem port',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='ntw_modem_port', type='text', value='/dev/ttyUSB3',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('Baud rate (bps)',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='ntw_baud_rate', type='text', value='115200',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        # Measurement setup
                        dbc.Row(
                            [
                                html.Div([
                                    html.Label('Measurement setup', style={'color': 'Black', 'font-size': 45}),
                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                          'justify-content': 'center'}),

                                html.Hr(style={'borderWidth':'0.3vh','width':'100%','borderColor':'#000000','opacity':'unset'}),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('Campaign name',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='mes_name', type='text', value='Test01',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('# experiments per campaign',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='mes_exps', type='text', value='5000',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('# repetitions per campaign',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='mes_repet', type='text', value='1',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div([
                                            html.Label('Repetition time gap (hours)',
                                                       style={'color': 'Black', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),

                                dbc.Col(
                                    [
                                        html.Div([
                                            dcc.Input(id='mes_gap', type='text', value='0.010',
                                                      style={'width': '100%', 'font-size': 20}),
                                        ], style={'width': '100%', 'display': 'flex',
                                                  'align-items': 'left',
                                                  'justify-content': 'left'}),
                                    ]
                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                        ),

                    ]
                    ,width=3,style={'margin-right': '0px', 'margin-left': '10px'}
                ),

                # Col 2 - EXPERIMENT SETTINGS
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                html.Div([
                                    html.Label('Experiment settings', style={'color': 'Black', 'font-size': 45}),
                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                          'justify-content': 'center'}),

                                html.Hr(style={'borderWidth': '0.3vh', 'width': '100%', 'borderColor': '#000000',
                                               'opacity': 'unset'}),
                            ]
                        ),

                        dbc.Row(
                            [
                                # Column: Baseline Measurements
                                dbc.Col(
                                    [
                                        # title
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('Baseline measurements (UL/DL)', style={'color': 'Black', 'font-size': 40}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                          'justify-content': 'center'}),

                                                html.Hr(style={'borderWidth': '0.2vh', 'width': '100%',
                                                               'borderColor': '#000000', 'opacity': 'unset'}),
                                            ]
                                        ),

                                        ##### 01 iperf3 test BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('Iperf3 test', style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr(style={'width': '100%'})
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Enable',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['True', 'False'], 'True', id='exp_base_perf_enable',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Protocol(s)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['TCP', 'UDP', 'All'], 'All', id='exp_base_perf_protocol',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Payload size (bytes)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_perf_payload_bytes', type='text', value='64',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Target bitrate (Mbps)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_perf_rate_mbps', type='text', value='2000',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Probe duration (sec)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_perf_duration_sec', type='text',
                                                                      value='10',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 01 iperf3 test END

                                        ##### 02 ICMP ping test BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('ICMP Ping test',
                                                               style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr()
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Enable',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['True', 'False'], 'True', id='exp_base_icmp_enable',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Packet size (bytes)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_icmp_payload_bytes', type='text', value='128',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Packet interval (ms)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_icmp_interval_ms', type='text',
                                                                      value='10',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('# packets',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_icmp_packets', type='text',
                                                                      value='100',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 02 ICMP ping test END

                                        ##### 03 UDP ping test BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('UDP Ping test',
                                                               style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr()
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Enable',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['True', 'False'], 'True', id='exp_base_udpping_enable',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Packet size (bytes)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_udpping_payload_bytes', type='text', value='256',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Packet interval (ms)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_udpping_interval_ms', type='text',
                                                                      value='15',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('# packets',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_udpping_packets', type='text',
                                                                      value='100',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 03 UDP ping test END

                                        ##### 04 OWAMP/TWAMP test BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('OWAMP/TWAMP test',
                                                               style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr()
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Enable',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['True', 'False'], 'True', id='exp_base_wamp_enable',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Packet size (bytes)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_wamp_payload_bytes', type='text', value='88',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Packet interval (ms)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_wamp_interval_ms', type='text',
                                                                      value='17',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('# packets',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_base_wamp_packets', type='text',
                                                                      value='100',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 04 OWAMP/TWAMP test END

                                    ]
                                    , width=5, style={'margin-right': '0px', 'margin-left': '100px'}
                                ),

                                # Column: Application-specific Measurements
                                dbc.Col(
                                    [
                                        # title
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('Application-specific measurements', style={'color': 'Black', 'font-size': 40}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                          'justify-content': 'center'}),

                                                html.Hr(style={'borderWidth': '0.2vh', 'width': '100%',
                                                               'borderColor': '#000000', 'opacity': 'unset'}),
                                            ]
                                        ),

                                        ##### 00 wireshark BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('Wireshark capture settings',
                                                               style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr()
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Max capture time (sec)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_app_shark_captime_sec', type='text', value='30',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Max captured packets',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_app_shark_maxpacks', type='text', value='150',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 00 wireshark END

                                        ##### 01 mqtt BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('App: MQTT publisher (UL)', style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr()
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Enable',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['True', 'False'], 'True', id='exp_app_mqtt_enable',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Max payload size (bytes)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_app_mqtt_payload_bytes', type='text', value='10000',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Publish interval (ms)',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_app_mqtt_interval_ms', type='text', value='20',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 01 mqtt END

                                        ##### 02 videostream BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('App: Video streamer (UL)',
                                                               style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr()
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Enable',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['True', 'False'], 'True', id='exp_app_video_enable',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('FPS',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_app_video_fps', type='text',
                                                                      value='30',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Frame width',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_app_video_width', type='text',
                                                                      value='400',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Frame height',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Input(id='exp_app_video_height', type='text',
                                                                      value='400',
                                                                      style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 02 videostream END

                                        ##### 03 profinet BEGIN
                                        dbc.Row(
                                            [
                                                html.Div([
                                                    html.Label('App: Profinet client (UL)',
                                                               style={'color': 'Black', 'font-size': 30}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'left',
                                                          'justify-content': 'left'}),

                                                html.Hr()
                                            ]
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            html.Label('Enable',
                                                                       style={'color': 'Black', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),

                                                dbc.Col(
                                                    [
                                                        html.Div([
                                                            dcc.Dropdown(['True', 'False'], 'False', id='exp_app_profinet_enable',
                                                                         style={'width': '100%', 'font-size': 20}),
                                                        ], style={'width': '100%', 'display': 'flex',
                                                                  'align-items': 'left',
                                                                  'justify-content': 'left'}),
                                                    ]
                                                    , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                ),
                                            ]
                                        ),

                                        ##### 03 profinet END

                                        ##### placeholders
                                        dbc.Row(
                                            [
                                                html.Br(),
                                                html.Br(),
                                                html.Br(),
                                                html.Br(),
                                            ]
                                        ),
                                        ##### 04 button start
                                        dbc.Row(
                                            [
                                                html.Div(children=[

                                                    html.Button(id='button_start', n_clicks=0, children='Start!',
                                                                style={'font-size': '55px', 'width': '200px',
                                                                       'display': 'inline-block',
                                                                       'margin-bottom': '40px',
                                                                       'margin-right': '5px', 'height': '100px',
                                                                       'verticalAlign': 'top',
                                                                       'color': 'rgb(255,215,0)',
                                                                       'background-color': 'rgb(0,0,0)'}),

                                                ], style={'padding': 10, 'flex': 1}),
                                            ]
                                        ),


                                    ]
                                    , width=5, style={'margin-right': '0px', 'margin-left': '100px'}
                                ),

                            ]
                        ),

                    ]
                    , width=8, style={'margin-right': '0px', 'margin-left': '50px'}
                ),

            ]
        ),

    ], style={'padding': 10, 'flex': 1, 'width': '10%',"border-left":"2px black solid"}),

    dbc.Modal(
        [
            html.Div(children=[

                # Row 1: Title of UI
                dbc.Row(
                    dbc.Col(
                        html.Div([
                            html.Label('Golden Unit Monitoring', style={'color': 'Black', 'font-size': 55}),
                        ], style={'width': '100%', 'display': 'flex',
                                  'align-items': 'center', 'justify-content': 'center'}
                        ),

                        width={"size": 6, "offset": 3},
                    )
                ),

                # Row 2: Base stats
                dbc.Row(
                            [
                                # Row 2.1: Title
                                dbc.Row(
                                    dbc.Col(
                                                [
                                                    html.Div([
                                                        html.Label('Baseline statistics', style={'color': 'Black', 'font-size': 35}),
                                                    ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                              'justify-content': 'center'}),

                                                    html.Hr(
                                                        style={'borderWidth': '0.3vh', 'width': '100%', 'borderColor': '#000000',
                                                               'opacity': 'unset'}),
                                                ],width={"size": 6, "offset": 3},
                                    )
                                ),

                                # Row 2.2: Graphs
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                html.Div([
                                                    dcc.Graph(id="fig_thru_tcp", style={}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                          'justify-content': 'center'}),
                                            ]
                                        ,width=4,style={'margin-right': '0px', 'margin-left': '0px'}),

                                        dbc.Col(
                                            [
                                                html.Div([
                                                    dcc.Graph(id="fig_thru_udp", style={}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                          'justify-content': 'center'}),
                                            ]
                                        ,width=4,style={'margin-right': '0px', 'margin-left': '0px'}),

                                        dbc.Col(
                                            [
                                                html.Div([
                                                    dcc.Graph(id="fig_delay", style={}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                          'justify-content': 'center'}),
                                            ]
                                        ,width=4,style={'margin-right': '0px', 'margin-left': '0px'}),
                                    ]
                                ),
                            ],
                        ),

                dbc.Row(
                    [
                        html.Hr(style={'width': '100%'}),
                        html.Br(),
                    ]
                ),

                # Row 3: App stats and log/buttons
                dbc.Row(
                            [
                                # Left col-> app stats
                                dbc.Col(
                                            [
                                                # Row Title
                                                dbc.Row(
                                                    dbc.Col(
                                                            [
                                                                html.Div([
                                                                    html.Label('Application-specific statistics', style={'color': 'Black', 'font-size': 35}),
                                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                                          'justify-content': 'center'}),

                                                                html.Hr(
                                                                    style={'borderWidth': '0.3vh', 'width': '100%',
                                                                           'borderColor': '#000000',
                                                                           'opacity': 'unset'}),
                                                            ],width={"size": 6, "offset": 3},
                                                    )
                                                ),

                                                # Row 2.2: Graphs
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [

                                                                html.Div([
                                                                    dcc.Graph(id="fig_app_thru", style={}),
                                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                                          'justify-content': 'center'}),

                                                            ]
                                                            , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                        ),

                                                        dbc.Col(
                                                            [

                                                                html.Div([
                                                                    dcc.Graph(id="fig_app_delay", style={}),
                                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                                          'justify-content': 'center'}),

                                                            ]
                                                            , width=6, style={'margin-right': '0px', 'margin-left': '0px'}
                                                        ),
                                                    ]
                                                )
                                            ],width=8,style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                                # Right col-> misc
                                dbc.Col(
                                            [
                                                dbc.Row(
                                                    dbc.Col(
                                                                [
                                                                    html.Div([
                                                                        html.Label('Event log',
                                                                                   style={'color': 'Black', 'font-size': 35}),
                                                                    ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                                              'justify-content': 'center'}),

                                                                    html.Hr(
                                                                        style={'borderWidth': '0.3vh', 'width': '100%',
                                                                               'borderColor': '#000000',
                                                                               'opacity': 'unset'}),
                                                                ],width={"size": 6, "offset": 3},
                                                    )
                                                ),

                                                html.Div([
                                            dash_table.DataTable(id='table_news',
                                                                 style_data={'whiteSpace': 'normal',
                                                                             'backgroundColor': 'rgb(255,215,0)',
                                                                             'color': 'black'},
                                                                 style_header={'backgroundColor': 'black', 'color': 'white'},
                                                                 fill_width=True,
                                                                 css=[{
                                                                     'selector': '.dash-spreadsheet td div',
                                                                     'rule': '''
                                                                        line-height: 15px;
                                                                        max-height: 30px; min-height: 30px; height: 30px;
                                                                        display: block;
                                                                        overflow-y: hidden;
                                                                        '''
                                                                 }],
                                                                 style_cell={'textAlign': 'left',
                                                                             'minWidth': '500px',
                                                                             'width': '500px',
                                                                             'maxWidth': '500px'},
                                                                 style_cell_conditional=[
                                                                     {'if': {'column_id': 'time'},
                                                                      'textAlign': 'left',
                                                                      'minWidth': '150px',
                                                                      'width': '150px',
                                                                      'maxWidth': '150px'},
                                                                     {'if': {'column_id': 'description'},
                                                                      'textAlign': 'left',
                                                                      'minWidth': '500px',
                                                                      'width': '500px',
                                                                      'maxWidth': '500px'},
                                                                 ]
                                                                 ),
                                        ], style={'width': '100%', 'display': 'flex', 'align-items': 'center','justify-content': 'center'}),

                                                dcc.Interval(
                                                    id='interval1',
                                                    interval=1 * 1000,  # in milliseconds
                                                    n_intervals=0
                                                ),

                                                html.Br(),

                                                # Button
                                                html.Div([
                                                    html.Button(id='button_save', n_clicks=0, children='Save stats',
                                                                style={'font-size': '25px', 'width': '300px', 'display': 'inline-block',
                                                                       'margin-bottom': '10px', 'margin-right': '5px', 'height': '60px',
                                                                       'verticalAlign': 'top', 'color': 'rgb(255,215,0)',
                                                                       'background-color': 'rgb(100,100,100)'}),
                                                    dcc.Download(id="download_save"),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center',
                                                          'justify-content': 'center'}),

                                                # Button
                                                html.Div([
                                                    html.Button(id='button_exit', n_clicks=0, children='Exit',
                                                                style={'font-size': '25px', 'width': '300px', 'display': 'inline-block',
                                                                       'margin-bottom': '10px', 'margin-right': '5px', 'height': '60px',
                                                                       'verticalAlign': 'top', 'color': 'rgb(255,215,0)',
                                                                       'background-color': 'rgb(0,0,0)'}),
                                                ], style={'width': '100%', 'display': 'flex', 'align-items': 'center','justify-content': 'center'}),

                                    ], width=4, style={'margin-right': '0px', 'margin-left': '0px'}
                                ),
                            ]
                ),

            ], style={'text-align': 'left','backgroundColor':'rgb(255,215,0)'})

        ],
        id="modal-fs",
        fullscreen=True,
        size="xl",
        backdrop="static",
        keyboard=False,
        centered=False
        #style={'height':'1200px','width':'3500px','text-align': 'left','align_content':'left'}
    )

], style={'display': 'flex', 'flex-direction': 'row'})
], style={'text-align': 'center','backgroundColor':'rgb(255,215,0)'})

@callback(
    Output('hidden-div', 'children'),
    #Output('modal-fs', 'is_open'),
    Input('button_start', 'n_clicks'),

    State('ntw_client_ip', 'value'),
    State('ntw_server_ip', 'value'),
    State('ntw_apn', 'value'),
    State('ntw_modem_port', 'value'),
    State('ntw_baud_rate', 'value'),

    State('mes_name', 'value'),
    State('mes_exps', 'value'),
    State('mes_repet', 'value'),
    State('mes_gap', 'value'),

    State('exp_base_perf_enable', 'value'),
    State('exp_base_perf_protocol', 'value'),
    State('exp_base_perf_payload_bytes', 'value'),
    State('exp_base_perf_rate_mbps', 'value'),
    State('exp_base_perf_duration_sec', 'value'),

    State('exp_base_icmp_enable', 'value'),
    State('exp_base_icmp_payload_bytes', 'value'),
    State('exp_base_icmp_interval_ms', 'value'),
    State('exp_base_icmp_packets', 'value'),

    State('exp_base_udpping_enable', 'value'),
    State('exp_base_udpping_payload_bytes', 'value'),
    State('exp_base_udpping_interval_ms', 'value'),
    State('exp_base_udpping_packets', 'value'),

    State('exp_base_wamp_enable', 'value'),
    State('exp_base_wamp_payload_bytes', 'value'),
    State('exp_base_wamp_interval_ms', 'value'),
    State('exp_base_wamp_packets', 'value'),

    State('exp_app_shark_captime_sec', 'value'),
    State('exp_app_shark_maxpacks', 'value'),

    State('exp_app_mqtt_enable', 'value'),
    State('exp_app_mqtt_payload_bytes', 'value'),
    State('exp_app_mqtt_interval_ms', 'value'),

    State('exp_app_video_enable', 'value'),
    State('exp_app_video_fps', 'value'),
    State('exp_app_video_width', 'value'),
    State('exp_app_video_height', 'value'),


    State('exp_app_profinet_enable', 'value'),
    prevent_initial_call=True

)
def update_output(button_start,
ntw_client_ip,
ntw_server_ip,
ntw_apn,
ntw_modem_port,
ntw_baud_rate,
mes_name,
mes_exps,
mes_repet,
mes_gap,
exp_base_perf_enable,
exp_base_perf_protocol,
exp_base_perf_payload_bytes,
exp_base_perf_rate_mbps,
exp_base_perf_duration_sec,
exp_base_icmp_enable,
exp_base_icmp_payload_bytes,
exp_base_icmp_interval_ms,
exp_base_icmp_packets,
exp_base_udpping_enable,
exp_base_udpping_payload_bytes,
exp_base_udpping_interval_ms,
exp_base_udpping_packets,
exp_base_wamp_enable,
exp_base_wamp_payload_bytes,
exp_base_wamp_interval_ms,
exp_base_wamp_packets,
exp_app_shark_captime_sec,
exp_app_shark_maxpacks,
exp_app_mqtt_enable,
exp_app_mqtt_payload_bytes,
exp_app_mqtt_interval_ms,
exp_app_video_enable,
exp_app_video_fps,
exp_app_video_width,
exp_app_video_height,
exp_app_profinet_enable
):
    mydict={
        'Network':{
            'Client IP':ntw_client_ip,
            'Server IP': ntw_server_ip,
            'APN': ntw_apn,
            'Modem port': ntw_modem_port,
            'Baud rate': ntw_baud_rate
        },
        'Measurement':{
            'Campaign name':mes_name,
            'Experiments per campaign':mes_exps,
            'Repetitions per campaign':mes_repet,
            'Repetition time gap (hours)':mes_gap
        },
        'Experiment': {
            'Baseline':{
                'iperf':{
                    'enable':exp_base_perf_enable,
                    'protocols':exp_base_perf_protocol,
                    'payload (bytes)':exp_base_perf_payload_bytes,
                    'bitrate (Mbps)':exp_base_perf_rate_mbps,
                    'duration (sec)':exp_base_perf_duration_sec
                },
                'icmp':{
                    'enable':exp_base_icmp_enable,
                    'payload (bytes)':exp_base_icmp_payload_bytes,
                    'interval (ms)':exp_base_icmp_interval_ms,
                    'packets':exp_base_icmp_packets
                },
                'udp ping':{
                    'enable': exp_base_udpping_enable,
                    'payload (bytes)': exp_base_udpping_payload_bytes,
                    'interval (ms)': exp_base_udpping_interval_ms,
                    'packets': exp_base_udpping_packets
                },
                'wamp':{
                    'enable': exp_base_wamp_enable,
                    'payload (bytes)': exp_base_wamp_payload_bytes,
                    'interval (ms)': exp_base_wamp_interval_ms,
                    'packets': exp_base_wamp_packets
                }
            },
            'Application':{
                'Wireshark':{
                    'capture time (sec)': exp_app_shark_captime_sec,
                    'max packets': exp_app_shark_maxpacks,
                },
                'MQTT':{
                    'enable': exp_app_mqtt_enable,
                    'payload (bytes)': exp_app_mqtt_payload_bytes,
                    'interval (ms)': exp_app_mqtt_interval_ms
                },
                'Video':{
                    'enable': exp_app_video_enable,
                    'fps':exp_app_video_fps,
                    'width':exp_app_video_width,
                    'height':exp_app_video_height
                },
                'Profinet':{
                    'enable': exp_app_profinet_enable,
                }
            }

        },
    }

    res=helper.write_dict2json(loc=gparams._DB_FILE_LOC_IN_USER,mydict=mydict,clean=True)

    if res is not None:
        print('(DEBUG) DB: Updated db according to new user input - Success')
    else:
        return None

@app.callback(
    Output("modal-fs", "is_open"),
    Input("button_start", "n_clicks"),
    Input("button_exit", "n_clicks"),
    State("modal-fs", "is_open"),
)
def toggle_modal(button_start, button_exit, is_open):
    if button_start or button_exit:
        return not is_open
    return is_open

@callback(
    Output("download_save", "data"),
    Input("button_save", "n_clicks"),
    prevent_initial_call=True
)
def func(n_clicks):
    print('(Frontend) DBG: Downloading exp files...')

    # create the zip file first parameter path/name, second mode
    print('(Frontend) DBG: Zipping...')
    zip_name='zip'+helper.get_folderstr_timestamp()+'.zip'
    zf = zipfile.ZipFile(zip_name, mode="a")
    try:
        for file in os.listdir(gparams._DB_DIR):
            print('(Frontend) DBG: File='+str(file)+'...')
            filename = os.fsdecode(file)
            dir=os.path.join(gparams._DB_DIR,filename)
            if 'git' in str(filename):
                pass
            else:
                zf.write(dir, filename, compress_type=zipfile.ZIP_STORED)
    except Exception as ex:
        print('(Frontend) ERROR: During zip='+str(ex))
    finally:
        # Don't forget to close the file!
        zf.close()

    return dcc.send_file(zip_name)

@callback(
    Output('fig_thru_tcp', 'figure'),
    Output('fig_thru_udp', 'figure'),
    Output('fig_delay', 'figure'),
    Output('fig_app_thru', 'figure'),
    Output('fig_app_delay', 'figure'),
    Output('table_news', 'data'),
    Input('interval1', 'n_intervals'),
)
def update_graph_live(n_intervals):

    # Figure 1 TCP UL/DL
    df_iperf=helper.read_jsonlines2pandas(loc=gparams._RES_FILE_LOC_IPERF)
    df_iperf['TCP Uplink (Mbps)'] = df_iperf['tcp_ul_sent_bps']  * (1e-6)
    df_iperf['TCP Downlink (Mbps)'] = df_iperf['tcp_dl_received_bps'] * (1e-6)

    fig_my_thru_tcp = px.area(df_iperf, x="timestamp", y=['TCP Uplink (Mbps)','TCP Downlink (Mbps)'],markers=False)

    fig_my_thru_tcp.update_xaxes(
        #title_text="Time",
        #title_font={"size": 30,'color':'black'},
        #title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor = 'black',
        color='black',
        linewidth = 3,
        linecolor='black',
        zerolinecolor='black'
    )

    fig_my_thru_tcp.update_yaxes(
        #title_text="Training loss",
        #title_font={"size": 30,'color':'black'},
        #title_standoff=25,
        tickfont={"size": 18,'color':'black'},
        gridcolor = 'black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black',
        visible=True,
        showticklabels=True
    )

    fig_my_thru_tcp.update_layout(
        yaxis_title='TCP Throughput (Mbps)',
        xaxis_title='Timestamp',
        width=600,
        height=300,
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0},
        plot_bgcolor='rgb(255,215,0)',
        paper_bgcolor='rgb(255,215,0)',
        #title={'text':'Global convergence (training loss) w.r.t. time','font':{'color':'black','size':25}}
    )

    fig_my_thru_tcp.update_traces(
        stackgroup=None, fill='tozeroy'
        #marker_size=20,
        #marker_symbol='x',
        #marker_color='black'
    )

    ######### Fig 2 UDP ###########
    df_iperf['UDP Uplink (Mbps)'] = df_iperf['udp_ul_bps']  * (1e-6)
    df_iperf['UDP Downlink (Mbps)'] = df_iperf['udp_dl_bps'] * (1e-6)

    fig_my_thru_udp = px.area(df_iperf, x="timestamp", y=['UDP Uplink (Mbps)','UDP Downlink (Mbps)'],markers=False)

    fig_my_thru_udp.update_xaxes(
        #title_text="Time",
        #title_font={"size": 30,'color':'black'},
        #title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor = 'black',
        color='black',
        linewidth = 3,
        linecolor='black',
        zerolinecolor='black'
    )

    fig_my_thru_udp.update_yaxes(
        #title_text="Training loss",
        #title_font={"size": 30,'color':'black'},
        #title_standoff=25,
        tickfont={"size": 18,'color':'black'},
        gridcolor = 'black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black',
        visible=True,
        showticklabels=True
    )

    fig_my_thru_udp.update_layout(
        yaxis_title='UDP Throughput (Mbps)',
        xaxis_title='Timestamp',
        width=600,
        height=300,
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0},
        plot_bgcolor='rgb(255,215,0)',
        paper_bgcolor='rgb(255,215,0)',
        #title={'text':'Global convergence (training loss) w.r.t. time','font':{'color':'black','size':25}}
    )

    fig_my_thru_udp.update_traces(
        stackgroup=None, fill='tozeroy'
        #marker_size=20,
        #marker_symbol='x',
        #marker_color='black'
    )

    ############## Fig 3 Delay #########
    # Figure 3 ICMP delay
    df_icmp=helper.read_jsonlines2pandas(loc=gparams._RES_FILE_LOC_ICMP)
    df_icmp['Mean RTT (msec)'] = df_icmp['avg_rtt_ms']
    df_icmp['Jitter (msec)'] = df_icmp['jitter_ms']

    fig_my_delay = px.area(df_icmp, x="timestamp", y=['Mean RTT (msec)', 'Jitter (msec)'], markers=False)

    fig_my_delay.update_xaxes(
        # title_text="Time",
        # title_font={"size": 30,'color':'black'},
        # title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor='black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black'
    )

    fig_my_delay.update_yaxes(
        # title_text="Training loss",
        # title_font={"size": 30,'color':'black'},
        # title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor='black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black',
        visible=True,
        showticklabels=True
    )

    fig_my_delay.update_layout(
        yaxis_title='Latency (msec)',
        xaxis_title='Timestamp',
        width=600,
        height=300,
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0},
        plot_bgcolor='rgb(255,215,0)',
        paper_bgcolor='rgb(255,215,0)',
        # title={'text':'Global convergence (training loss) w.r.t. time','font':{'color':'black','size':25}}
    )

    fig_my_delay.update_traces(
        stackgroup=None, fill='tozeroy'
        # marker_size=20,
        # marker_symbol='x',
        # marker_color='black'
    )

    ############## Fig 4 app thru #########
    df_gui_app = helper.read_jsonlines2pandas(loc=gparams._RES_FILE_LOC_GUI_APP)

    # get all apps (filter)
    list_of_apps=df_gui_app['app_name'].unique()

    # plot the data
    fig_my_app_thru = go.Figure()
    fig_my_app_delay=go.Figure()

    for app in list_of_apps:
        app_df=df_gui_app.loc[df_gui_app['app_name'] == app]

        fig_my_app_thru = fig_my_app_thru.add_trace(go.Scatter(x=app_df["timestamp"],
                                       y=app_df["Throughput (Mbps)"],
                                       name=app))
        fig_my_app_delay = fig_my_app_delay.add_trace(go.Scatter(x=app_df["timestamp"],
                                       y=app_df["RTT (msec)"],
                                       name=app))

    fig_my_app_thru.update_xaxes(
        # title_text="Time",
        # title_font={"size": 30,'color':'black'},
        # title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor='black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black'
    )

    fig_my_app_thru.update_yaxes(
        # title_text="Training loss",
        # title_font={"size": 30,'color':'black'},
        # title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor='black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black',
        visible=True,
        showticklabels=True
    )

    fig_my_app_thru.update_layout(
        yaxis_title='Throughput (Mbps)',
        xaxis_title='Timestamp',
        width=600,
        height=300,
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0},
        plot_bgcolor='rgb(255,215,0)',
        paper_bgcolor='rgb(255,215,0)',
        # title={'text':'Global convergence (training loss) w.r.t. time','font':{'color':'black','size':25}}
    )

    # fig_my_delay.update_traces(
        # stackgroup=None, fill='tozeroy'
        # marker_size=20,
        # marker_symbol='x',
        # marker_color='black'
    # )


    fig_my_app_delay.update_xaxes(
        # title_text="Time",
        # title_font={"size": 30,'color':'black'},
        # title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor='black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black'
    )

    fig_my_app_delay.update_yaxes(
        # title_text="Training loss",
        # title_font={"size": 30,'color':'black'},
        # title_standoff=25,
        tickfont={"size": 18, 'color': 'black'},
        gridcolor='black',
        color='black',
        linewidth=3,
        linecolor='black',
        zerolinecolor='black',
        visible=True,
        showticklabels=True
    )

    fig_my_app_delay.update_layout(
        yaxis_title='RTT (msec)',
        xaxis_title='Timestamp',
        width=600,
        height=300,
        margin={'l': 0, 'b': 0, 't': 0, 'r': 0},
        plot_bgcolor='rgb(255,215,0)',
        paper_bgcolor='rgb(255,215,0)',
        # title={'text':'Global convergence (training loss) w.r.t. time','font':{'color':'black','size':25}}
    )


    mydf_news=helper.read_jsonlines2pandas(loc=gparams._DB_FILE_LOC_OUT_LOG)
    mydf_news = mydf_news.tail(6)


    output_news=mydf_news.to_dict('records')

    return fig_my_thru_tcp,fig_my_thru_udp,fig_my_delay,fig_my_app_thru,fig_my_app_delay,output_news


if __name__ == '__main__':
    print('(Frontend) DBG: Frontend initialized')
    helper=Helper()
    app.run(host='0.0.0.0')
