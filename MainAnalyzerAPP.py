import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import requests
import datetime
import time
from ta.momentum import StochasticOscillator,StochRSIIndicator,RSIIndicator,WilliamsRIndicator
from ta.volatility import AverageTrueRange,BollingerBands,KeltnerChannel
from ta.trend import MACD
from ta.trend import IchimokuIndicator,EMAIndicator,SMAIndicator
import numpy as np

####################### Corporate css formatting
corporate_colors = {
    'dark-blue-grey' : 'rgb(62, 64, 76)',
    'medium-blue-grey' : 'rgb(77, 79, 91)',
    'superdark-green' : 'rgb(41, 56, 55)',
    'dark-green' : 'rgb(57, 81, 85)',
    'mod-dark-green' : 'rgb(57, 90, 85)',
    'medium-green' : 'rgb(93, 113, 120)',
    'light-green' : 'rgb(186, 218, 212)',
    'pink-red' : 'rgb(255, 101, 131)',
    'dark-pink-red' : 'rgb(247, 80, 99)',
    'white' : 'rgb(251, 251, 252)',
    'light-grey' : 'rgb(208, 206, 206)'
}



style_for_heading = {'font-size':'32px','color':corporate_colors['white'],'font-family':'Dosis','text-align':'center','margin-top':'5px','margin-left':'20px','margin-bottom':'2px'}
style_for_sub_heading = {'font-size':'18px','color':corporate_colors['white'],'text-align':'center','font-weight': 'italic','margin-top':'5px','margin-left':'20px'}
style_for_dropdown = {'width': '25%','box-sizing': 'border-box','display': 'inline-block','padding-left':'20px','color':'black','font-size':'14px', 'optionHeight':'16px','text-align':'left'}
index_options={'NONE','NEPSE_index','BANKING_index','MICROFINANCE_index','FINANCE_index','HYDROPOWER_index','LIFE INSURANCE_index','NON LIFE INSURANCE_index','DEVELOPMENT BANK_index','OTHERS_index'}

def import_data(scrip,adjust):
    if (adjust=='ADJUSTED'):
        scripadj='_adj'
    else:
        scripadj=''
    fromdate_origin = datetime.datetime(2000, 1, 1, 0, 0).timestamp()
    todate_origin = datetime.datetime(2021, int(time.strftime("%m")), int(time.strftime("%d")), 23, 59).timestamp()
    url = "https://backendtradingview.systemxlite.com/tradingviewsystemxlite/history"
    payload = {"symbol": scrip+scripadj, "resolution": "1d", "from": fromdate_origin, "to": todate_origin,
               "currencycode": "nrs"}

    page = requests.get(url, params=payload)
    df = pd.DataFrame(page.json())
    df.columns = ['status', 'date', 'adjclose', 'open', 'high', 'low', 'volume']  # for systemxlite
    del df['status']
    df['date'] = df['date'].map(lambda val: datetime.datetime.fromtimestamp(val).strftime('%d/%m/20%y'))
    timewindow = 14
    df = df.replace(0, np.nan)

    # df['rsi'] = calcrsi(df['adjclose'],timewindow)

    rsi_data = RSIIndicator(close=df['adjclose'], window=timewindow)
    df['rsi'] = rsi_data.rsi()

    stochosc_data = StochasticOscillator(high=df['high'], low=df['low'], close=df['adjclose'])
    df['stoch'] = stochosc_data.stoch()
    # df['stochsignal']=stochosc_data.stoch_signal()

    stochrsi_data = StochRSIIndicator(close=df['adjclose'])
    df['momentum_stoch_rsi'] = stochrsi_data.stochrsi()
    df['momentum_stoch_rsi_k'] = stochrsi_data.stochrsi_k()
    df['momentum_stoch_rsi_d'] = stochrsi_data.stochrsi_d()

    macd_data = MACD(window_slow=17, window_fast=8, close=df['adjclose'])
    df['macd'] = macd_data.macd()
    df['macddiff'] = macd_data.macd_diff()

    volatility_data = AverageTrueRange(close=df['adjclose'], high=df['high'], low=df['low'], window=10)
    df['volatility_atr'] = volatility_data.average_true_range()

    bollingerdata = BollingerBands(close=df['adjclose'], window=20)
    df['volatility_bbm'] = bollingerdata.bollinger_mavg()
    df['volatility_bbl'] = bollingerdata.bollinger_lband()
    df['volatility_bbh'] = bollingerdata.bollinger_hband()
    df['volatility_bbw'] = bollingerdata.bollinger_wband()

    keltner_data = KeltnerChannel(close=df['adjclose'], high=df['high'], low=df['low'], window=20)
    df['volatility_kch'] = keltner_data.keltner_channel_hband()
    df['volatility_kcl'] = keltner_data.keltner_channel_lband()
    df['volatility_kcw'] = keltner_data.keltner_channel_wband()

    williamsr_data = WilliamsRIndicator(high=df['high'], low=df['low'], close=df['adjclose'], lbp=14)
    df['williamr'] = williamsr_data.williams_r()

    ichimoku_data = IchimokuIndicator(high=df['high'], low=df['low'])
    df['ichibaseline'] = ichimoku_data.ichimoku_base_line()
    df['ichiconversionline'] = ichimoku_data.ichimoku_conversion_line()
    df['ichilinea'] = ichimoku_data.ichimoku_b()
    df['ichilineb'] = ichimoku_data.ichimoku_a()

    ema_data = EMAIndicator(close=df['adjclose'], window=200)
    df['ema200'] = ema_data.ema_indicator()

    ema_data20 = EMAIndicator(close=df['adjclose'], window=20)
    df['ema20'] = ema_data20.ema_indicator()

    upperBB = df['volatility_bbh']
    lowerBB = df['volatility_bbl']
    lowerKC = df['volatility_kch']
    upperKC = df['volatility_kcl']

    df['sqzOn'] = (lowerBB > lowerKC) & (upperBB < upperKC)
    df['sqzOff'] = (lowerBB < lowerKC) & (upperBB > upperKC)
    df['noSqz'] = (df['sqzOn'] == False) & (df['sqzOff'] == False)

    #df['high'].rolling(20).sum()
    df['highest']=df['high'].rolling(20).max()
    df['lowest'] = df['low'].rolling(20).max()
    df['avg']=(df['highest']+df['lowest'])/2

    sma_data= SMAIndicator(close=df['adjclose'], window=20)
    df['sma20']=sma_data.sma_indicator()

    df['new_avg_source']=(df['adjclose']-((df['avg']+df['sma20'])/2))

    ema_squeeze=EMAIndicator(close=df['new_avg_source'],window=5)
    df['SqueezeMom5']=ema_squeeze.ema_indicator()
    ema_squeeze2 = EMAIndicator(close=df['new_avg_source'], window=2)
    df['SqueezeMom2'] = ema_squeeze2.ema_indicator()
    ema_squeeze20 = EMAIndicator(close=df['new_avg_source'], window=20)
    df['SqueezeMom20'] = ema_squeeze20.ema_indicator()

    return df

def FloorsheetData(script):
    url = "http://nepalstock.com/floorsheet"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }
    payload = {"stock-symbol": script, "_limit": "10000"}
    page = requests.get(url, headers=headers, params=payload)
    table_MN = pd.read_html(page.text, skiprows=1, header=0)
    #print(f'Total tables: {len(table_MN)}')
    df_floorsheet = table_MN[0]
    #print(df_floorsheet)

    df_floorsheet = df_floorsheet.iloc[0:-3, :-2]
    df_floorsheet['Rate'] = df_floorsheet['Rate'].astype(float)
    df_floorsheet['Quantity'] = df_floorsheet['Quantity'].astype(float)

    #print(df_floorsheet['Quantity'])

    return df_floorsheet

def EPSData(script):
    url = "https://merolagani.com/CompanyDetail.aspx"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }

    payload = {"symbol": script}
    # print (url)
    page = requests.get(url, headers=headers, params=payload)
    table_MN = pd.read_html(page.text, skiprows=7, header=0)
    df_EPS = table_MN[0]

    #print(df_EPS)
    EPS_Value = df_EPS.iat[0, 1]
    PE_Value= df_EPS.iat[1, 1]
    BookValue= df_EPS.iat[2, 1]
    #CashDiv = df_EPS.iat[4, 1]
    #BonusDiv = df_EPS.iat[6, 1]
    #MarketCap= df_EPS.iat[10, 1]
    return script,EPS_Value,PE_Value,BookValue

def GetCompanyScript():
    url = "http://www.nepalstock.com/company"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    }

    payload = {"_limit": 500}
    page = requests.get(url, headers=headers, params=payload)
    table_MN = pd.read_html(page.text, skiprows=1, header=0)
    df_CompanyListed = table_MN[0]

    return df_CompanyListed['Stock Symbol']

stock_options=GetCompanyScript()

app = dash.Dash(__name__, title='Stock Analytics Prasanna')
config = dict({'scrollZoom': True ,'showAxisDragHandles':True,'displaylogo': False, 'modeBarButtonsToAdd':['drawline',
                                        'drawopenpath',
                                        'drawclosedpath',
                                        'drawcircle',
                                        'drawrect',
                                        'eraseshape'
                                       ]})
config_floorsheet= dict({'scrollZoom': True})


app.layout = html.Div([
    html.H2("STOCK ANALYSIS",style=style_for_heading,id='STOCKID'),
    html.Br(),
    html.Div(
        [
            html.Label(["Choose_Stock"],style={'color':corporate_colors['white'],'text-align': 'center','font-size':22,'display': 'flex','align-items': 'center'}),
            dcc.Dropdown(
                id="STOCK",
                options=[{
                    'label': i,
                    'value': i
                } for i in stock_options],
                value='ACLBSL',style={'width':'33%','font-size': '14px', 'display': 'inline-block','color' : 'grey','white-space': 'nowrap', 'text-overflow': 'ellipsis'}),
            dcc.Dropdown(
                id="ADJUST",
                options=[{
                    'label': i,
                    'value': i
                } for i in ['ADJUSTED','UNADJUSTED']],
                value='ADJUSTED',style={'width':'33%','display': 'inline-block','font-size': '14px', 'color' : 'BLACK', 'white-space': 'nowrap', 'text-overflow': 'ellipsis'}),
            dcc.Dropdown(
                id="INDEX",
                options=[{
                    'label': i,
                    'value': i
                } for i in index_options],
                value='NONE',style={'width':'33%','font-size': '14px', 'display': 'inline-block','color' : 'grey','white-space': 'nowrap', 'text-overflow': 'ellipsis'}),

        ],style={'width':'64%','border-style' : 'solid',
    'border-width' : '1px',
    'border-color' : corporate_colors['superdark-green'],
    'background-color' : corporate_colors['superdark-green'],
    'box-shadow' : '0px 0px 17px 0px rgba(146, 251, 142, 1)'}),




    html.Br(),
    html.Div([
    html.Div(children=[html.H2('STOCK NAME'), html.H2(id='StockName')],
                 style={'width': '15%','color':corporate_colors['white'], 'display': 'inline-block', 'border': '1px solid white', 'text-align': 'center', 'font-size': 10,'font-weight': 'bold', 'font-family': 'Century Gothic'}),
    html.Div(children=[html.H2('EPS'), html.H2(id='Finance_data')],
                 style={'width': '28%', 'color':corporate_colors['white'],'display': 'inline-block', 'border': '1px solid grey', 'text-align': 'center','font-size':8, 'font-family': 'Century Gothic'}),
    html.Div(children=[html.H2('PE value'), html.H2(id='Finance_data_PE')],
                 style={'width': '28%', 'color':corporate_colors['white'],'display': 'inline-block', 'border': '1px solid grey', 'text-align': 'center','font-size':8, 'font-family': 'Century Gothic'}),
    html.Div(children=[html.H2('Book Value'),html.H2(id='Finance_data_BookVal')],
                 style={'width': '28%','color':corporate_colors['white'],'display': 'inline-block', 'border': '1px solid white', 'text-align': 'center', 'font-size':8,  'font-family': 'Century Gothic','bgcolor':'white'}),
    ],style={'color':'#5d5s6e','border-style' : 'solid',
    'border-width' : '1px',
    'border-color' : corporate_colors['superdark-green'],
    'background-color' : corporate_colors['superdark-green'],
    'box-shadow' : '0px 0px 17px 0px rgba(246, 168, 242, .5)',}),
    #html.Div(children=[html.H2('Latest Cash Dividend'),html.H2(id='Finance_data_CashDiv')],
    #             style={'width': '15%','display': 'inline-block', 'border': '1px solid black', 'text-align': 'center', 'font-family': 'Century Gothic'}),
    #html.Div(children=[html.H2('Latest Bonus Dividend'),html.H2(id='Finance_data_BonusDiv')],
    #             style={'width': '15%','display': 'inline-block', 'border': '1px solid black', 'text-align': 'center', 'font-family': 'Century Gothic'}),
    #html.Div(children=[html.H2('Market Cap.'),html.H2(id='Finance_data_MKTCap')],
    #             style={'width': '15%','display': 'inline-block', 'border': '1px solid black', 'text-align': 'center', 'font-family': 'Century Gothic'}),

    html.Br(),

    html.Div([

        dcc.Graph(id='stock_graph', figure={'layout': {'height': 950}},config=config)],
             style={'height': '100%','width': '95%', 'display': 'inline-block', 'padding': '20 20 20 20','border-radius' : '10px',
    'border-style' : 'solid',
    'border-width' : '1px',
    'border-color' : corporate_colors['superdark-green'],
    'background-color' : corporate_colors['superdark-green'],
    'box-shadow' : '0px 0px 17px 0px rgba(186, 218, 212, .5)',
    'padding-top' : '12px','padding-left' : '20px','padding-right' : '20px'}),

    html.Br(),
    html.Br(),html.Br(),html.Br(),
    html.H1("FLOORSHEET ANALYSIS",style=style_for_heading),
    html.H2("(Rate VS Quantity)",style=style_for_heading),
    html.Div([dcc.Graph(id='floorsheet_graph', figure={'layout': {'height': 700}},config=config_floorsheet)],
             style={'height': '100%', 'width': '95%', 'display': 'inline-block', 'padding': '20 20 20 20','border-style' : 'solid',
    'border-width' : '1px','border-radius' : '10px','background-color' : corporate_colors['superdark-green'],
    'border-color' : corporate_colors['superdark-green'],'box-shadow': '2px 5px 5px 1px rgba(255, 101, 131, .5)','padding-top' : '12px','padding-left' : '20px','padding-right' : '20px'}),

    html.H4("Copyright @ Prasanna Man Rajbanshi",style=style_for_sub_heading),
],style={'background-color' : corporate_colors['dark-green'], 'padding-left':'2%','fontcolor':'white'})

@app.callback(
    dash.dependencies.Output('stock_graph', 'figure'),
[dash.dependencies.Input('STOCK', 'value')],
[dash.dependencies.Input('ADJUST', 'value')])

def update_value(STOCK,ADJUST):


    SUBINDICATOR = 'SqueezeMom5'
    SUBINDICATOR2 = 'SqueezeMom2'
    SUBINDICATOR3 = 'SqueezeMom20'



    df= import_data(STOCK,ADJUST)

    #df = pd.read_csv(f'{STOCK}_adj.csv', parse_dates=True)
    dataTypeObj = df.dtypes['date']
    #print(dataTypeObj)

    df = df.set_index('date')
    #floorsheet_data_df=FloorsheetData()

    c_candlestick = make_subplots(rows=2, cols=1,
                                  shared_xaxes=True,
                                  vertical_spacing=0.05, row_heights=[1000, 600],
                                  subplot_titles=('', 'SQUEEZE_MOMENTUM_INDICATOR[TRADING VIEW INTERNATIONAL]'))

    #c_candlestick.add_trace(go.Candlestick(x=df.index,<==changed
    c_candlestick.add_trace(go.Candlestick(x=df.index,
                                           open=df['open'],
                                           high=df['high'],
                                           low=df['low'],
                                           close=df['adjclose'], name="Candle", increasing_line_color='white',
                                           decreasing_line_color='black'), row=1, col=1)

    c_candlestick.add_trace(go.Scatter(x=df.index, y=df['ema20'], name='EMA20', marker=dict(color='RED')), row=1, col=1)

    c_candlestick.add_trace(
        go.Scatter(x=df.index, y=df[SUBINDICATOR], name=SUBINDICATOR, fill='tonexty', marker=dict(color='YELLOW')),
        row=2, col=1)
    c_candlestick.add_trace(
        go.Scatter(x=df.index, y=df[SUBINDICATOR2], name=SUBINDICATOR2, fill='tonexty', marker=dict(color='BLUE')),
        row=2, col=1)
    c_candlestick.add_trace(
        go.Scatter(x=df.index, y=df[SUBINDICATOR3], name=SUBINDICATOR3, fill='tonexty', marker=dict(color='RED')),
        row=2, col=1)

    #c_candlestick.add_trace(go.Histogram2dContour(x=floorsheet_data_df['Rate'],y=floorsheet_data_df['Quantity']),row=3, col=1)


    c_candlestick.update_xaxes(
        # use below rangebreaks code if rangeslector is needed. ELSE rangebreaks is too slow to load chart
        # rangebreaks= [dict(values=dataf2[STOCK].dropna(axis=0))],# hide unavailable days date

        # title_text='Date',
        rangeslider_visible=False,
        rangeselector=dict(
            buttons=list([

                dict(count=3, label='3D', step='day', stepmode='todate'),
                dict(count=1, label='1D', step='day', stepmode='backward'),
                dict(count=1, label='1M', step='month', stepmode='backward'),
                dict(count=6, label='6M', step='month', stepmode='backward'),
                dict(count=1, label='YTD', step='year', stepmode='todate'),
                dict(count=1, label='1Y', step='year', stepmode='backward'),
                dict(step='all')])))
#darkslategrey
    c_candlestick.update_layout(font_family="Dosis",
    font_color="white",
    title_font_family="Dosis",
    title_font_color="white",
    legend_title_font_color="white", plot_bgcolor=corporate_colors['superdark-green'], paper_bgcolor=corporate_colors['mod-dark-green'],dragmode='pan',newshape_line_color='cyan')
    c_candlestick.update_layout(xaxis={'showgrid': False})

    return c_candlestick


#Fundamental Graph
@app.callback(
    dash.dependencies.Output('floorsheet_graph', 'figure'),
    [dash.dependencies.Input('STOCK', 'value')])

def update_fundamental(STOCK):
    floorsheet_data_df = FloorsheetData(STOCK)
    x = floorsheet_data_df['Quantity']
    #y = floorsheet_data_df['Quantity']
    y = floorsheet_data_df['Rate']


    fig = go.Figure()
    fig.add_trace(go.Histogram2dContour(
        x=x,
        y=y,
        colorscale='greys',
        reversescale=True,
        xaxis='x',
        yaxis='y',
        contours = dict(
            showlabels = True,
            labelfont = dict(
                family = 'Raleway',
                color = 'white'
            )
        )
    ))
    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        xaxis='x',
        yaxis='y',
        mode='markers',
        marker=dict(
            color='white',
            size=3
        )
    ))
    fig.add_trace(go.Histogram(
        y=y,
        xaxis='x2',
        marker=dict(
            color='rgba(0,0,0,1)'
        )
    ))
    fig.add_trace(go.Histogram(
        x=x,
        yaxis='y2',
        marker=dict(
            color='rgba(0,0,0,1)'
        )#,histnorm="density"
    ))

    fig.update_layout(
        autosize=False,
        xaxis=dict(
            zeroline=False,
            domain=[0, 0.85],
            showgrid=False
        ),
        yaxis=dict(
            zeroline=False,
            domain=[0, 0.85],
            showgrid=False
        ),
        xaxis2=dict(
            zeroline=False,
            domain=[0.85, 1],
            showgrid=False
        ),
        yaxis2=dict(
            zeroline=False,
            domain=[0.85, 1],
            showgrid=False
        ),
        #height=800,
        #width=1800,
        bargap=0,
        hovermode='closest',
        showlegend=False,dragmode='pan',paper_bgcolor=corporate_colors['mod-dark-green'],font_family="Courier New",
    font_color="white",
    title_font_family="Dosis",
    title_font_color="white",
    legend_title_font_color="white"
    )


    return fig


@app.callback(
    dash.dependencies.Output('StockName', 'children'),
    dash.dependencies.Output('Finance_data', 'children'),
    dash.dependencies.Output('Finance_data_PE', 'children'),
    dash.dependencies.Output('Finance_data_BookVal', 'children'),
    #dash.dependencies.Output('Finance_data_CashDiv', 'children'),
    #dash.dependencies.Output('Finance_data_BonusDiv', 'children'),
    #dash.dependencies.Output('Finance_data_MKTCap', 'children'),
    [dash.dependencies.Input('STOCK', 'value')])

def update_financedata(STOCK):
    return EPSData(STOCK)





if __name__ == "__main__":
    app.run_server(debug=True)
