
from dash import Dash, html, dash_table, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output,State

import pandas as pd

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import numpy as np
from pandas.api.types import CategoricalDtype

## Global
day = {'Monday':0, 'Tuesday':1, 'Wednesday':2, 'Thursday':3,'Friday':4, 'Saturday':5, 'Sunday':6}

month = {'January':0, 'February':1, 'March':2, 'April':3,'May':4, 'June':5, 'July':6, 'August':7, 'September':8, 'October':9, 'November':10, 'December':11}
shortHand = reverse_month = {key[:3]:month[key] for key in month}
reverse_month = {month[key]:key for key in month}

sales = pd.read_csv("Coffee Shop Sales.csv")
sales["transaction_date"] = pd.to_datetime(sales["transaction_date"], format="%d/%m/%Y")

stores = sales["store_location"].unique()
years = sorted(sales["transaction_date"].apply(lambda x: x.year).unique())
months =  list(map((lambda x: reverse_month[x-1][:3]), sorted(sales["transaction_date"].apply(lambda x: x.month).unique())))

SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',
    'padding': '20px 10px',
    'background-color': '#f8f9fa'
}

TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#191970'
}

CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'
}

CARD_CONTENT_STYLE = {
    'textAlign': 'center',
    'fontSize': '50px',
}

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',
    'margin-right': '5%',
    'padding': '20px 10p'
}

controls = dbc.Col(
    [
        html.P('Store', style={
            'textAlign': 'center'
        }),
        
        dcc.Dropdown(stores, value=stores[0], id="store"),
        html.Br(),
        html.P('Year', style={
            'textAlign': 'center'
        }),
        
        dbc.Row([dbc.Col([], md=2), dbc.Col(dcc.Dropdown(years, value=years[0], id="year")), dbc.Col([], md=2)]),
        
        html.Br(),
        html.P('Range', style={'textAlign': 'center'}),
        
        dbc.Row(
            [
                dbc.Col([html.P('Start:', style={'textAlign': 'center'})], md=2),
                dbc.Col([dcc.Dropdown(months, value=months[0], id="start_month")], md=4),
                dbc.Col([html.P('End:', style={'textAlign': 'center'})], md=2),
                dbc.Col([dcc.Dropdown(months, value=months[-1], id="end_month")], md=4)
            ]
        ),
        
        html.Br(),
        html.Div(
            [
                dbc.Button(
                    id='submit_button',
                    n_clicks=0,
                    children='Submit',
                )
            ],
            className="d-grid gap-2"
        )
    ]
)

sidebar = html.Div(
    [html.H2('Parameters', style=TEXT_STYLE),
     html.Hr(),
     controls],
    style=SIDEBAR_STYLE
)

cards = dbc.Row([
    
    dbc.Col([],md=3),
    
    dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.H4(children=['Total Revenue'], className='card-title',
                        style=CARD_TEXT_STYLE),
                html.P(id='total_revenue', style=CARD_CONTENT_STYLE)]
            )
            
        ]),
        md=3
    ),
    
    dbc.Col(
        dbc.Card([
            dbc.CardBody([
                html.H4("Total Transactions", className='card-title',
                        style=CARD_TEXT_STYLE),
                html.P(id='total_transactions', style=CARD_CONTENT_STYLE)]
            )]
        ),
        md=3
    ),
    dbc.Col([],md=3)
])

monthly_rev = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id="monthly_refresh"), md=12
        )
    ]
)

transactions = dbc.Row(
    [
        dbc.Col(dcc.Graph(id="hourly_refresh"), md=6),
        dbc.Col(dcc.Graph(id="weekly_refresh"), md=6)
    ]
)

products = dbc.Row(
    [   
        dbc.Col(html.Div([html.Label("Top 10 Products by Revenue"), dash_table.DataTable(id='product_refresh')]),md=5),
        dbc.Col(dcc.Graph(id="category_refresh"), md=7)
    ]
)

main = html.Div(
    [
        html.H2('Coffee Sales Dashboard', style=TEXT_STYLE),
        html.Hr(),
        cards,
        monthly_rev,
        transactions,
        products
    ],
    style=CONTENT_STYLE
)

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

revenue = sales
revenue["revenue"] = revenue["unit_price"]*revenue["transaction_qty"]

layout = go.Layout(title='Revenue and Qty Sold by Product',
        yaxis=dict(title='Revenue'),
        yaxis2=dict(title='Quantity Sold',
                    overlaying='y',
                    side='right'))

app.layout = html.Div([sidebar,main])

@callback(
    Output(component_id="hourly_refresh", component_property="figure"),
    [Input('submit_button', 'n_clicks')],
    [State('store', 'value'), 
     State('year','value'), 
     State('start_month', 'value'),
     State('end_month', 'value')]
)
def update_hourly_transactions(n_clicks, store, year, start_month, end_month):
    filtered = sales[sales["store_location"] == store]
    filtered = filtered[filtered["transaction_date"].dt.year == year]
    filtered = filtered[(shortHand[start_month]+1 <= filtered["transaction_date"].dt.month ) & (filtered["transaction_date"].dt.month <= shortHand[end_month]+1)]
    
    # Hourly Transactions
    hourlyTransactions = filtered.groupby(["transaction_date", pd.to_datetime(sales["transaction_time"], format="%H:%M:%S").dt.hour])["transaction_id"].count().reset_index()
    #hourlyTransactions = hourlyTransactions.groupby("transaction_time")["transaction_id"].mean().reset_index()
    hourlyTransactions = hourlyTransactions.groupby("transaction_time")["transaction_id"].sum().reset_index()
    hourlyTransactions.columns = ["Time", "No. Transactions"]

    return px.bar(hourlyTransactions , x="Time", y="No. Transactions", title="Hourly Transactions")

@callback(
    Output(component_id="weekly_refresh", component_property="figure"),
    [Input('submit_button', 'n_clicks')],
    [State('store', 'value'), 
     State('year','value'), 
     State('start_month', 'value'),
     State('end_month', 'value')]
)
def update_weekly_transactions(n_clicks, store, year, start_month, end_month):
    filtered = sales[sales["store_location"] == store]
    filtered = filtered[filtered["transaction_date"].dt.year == year]
    filtered = filtered[(shortHand[start_month]+1 <= filtered["transaction_date"].dt.month ) & (filtered["transaction_date"].dt.month <= shortHand[end_month]+1)]
    
    weeklyTransactions = filtered.groupby("transaction_date")["transaction_id"].count().reset_index()
    weeklyTransactions = weeklyTransactions.groupby(weeklyTransactions["transaction_date"].dt.day_name())["transaction_id"].sum().reset_index()
    #weeklyTransactions = weeklyTransactions.groupby(weeklyTransactions["transaction_date"].dt.day_name())["transaction_id"].mean().reset_index()
    weeklyTransactions.columns = ["Day", "No. Transactions"]
    weeklyTransactions = weeklyTransactions.sort_values(by=["Day"], key=lambda x: [day[record] for record in x])
    return px.line(weeklyTransactions ,x="Day", y="No. Transactions", title="Weekday Transactions")

@callback(
    Output(component_id="monthly_refresh", component_property="figure"),
    [Input('submit_button', 'n_clicks')],
    [State('store', 'value'), 
     State('year','value'), 
     State('start_month', 'value'),
     State('end_month', 'value')]
)
def update_monthly_revenue(n_clicks, store, year, start_month, end_month):
    filtered = revenue[revenue["store_location"] == store]
    filtered = filtered[filtered["transaction_date"].dt.year == year]
    filtered = filtered[(shortHand[start_month]+1 <= filtered["transaction_date"].dt.month ) & (filtered["transaction_date"].dt.month <= shortHand[end_month]+1)]
    
    # Monthly Revenue
    monthlyRevenue = filtered.groupby(filtered["transaction_date"])["revenue"].sum().reset_index()
    monthlyRevenue = monthlyRevenue.groupby(monthlyRevenue["transaction_date"].dt.month_name())["revenue"].sum().reset_index()
    monthlyRevenue.columns = ["Month", "Revenue"]
    monthlyRevenue = monthlyRevenue.sort_values(by=["Month"], key=lambda x: [month[record] for record in x])
    
    if(start_month != end_month):
        fig = px.line(monthlyRevenue ,x="Month", y="Revenue", title="Monthly Revenue")
    
    else:
        fig = px.bar(monthlyRevenue ,x="Month", y="Revenue", title="Monthly Revenue")
    
    return fig

@callback(
    Output(component_id="category_refresh", component_property="figure"),
    [Input('submit_button', 'n_clicks')],
    [State('store', 'value'), 
     State('year','value'), 
     State('start_month', 'value'),
     State('end_month', 'value')]
)
def update_category(n_clicks, store, year, start_month, end_month):
    filtered = revenue[revenue["store_location"] == store]
    filtered = filtered[filtered["transaction_date"].dt.year == year]
    filtered = filtered[(shortHand[start_month]+1 <= filtered["transaction_date"].dt.month ) & (filtered["transaction_date"].dt.month <= shortHand[end_month]+1)]
    
    # Revenue by category
    revenueByCategory = filtered.groupby("product_category").agg({"transaction_qty":'sum', "revenue": "sum"}).reset_index().sort_values(by=["revenue"], ascending=False)
    revenueByCategory.columns = ["Category", "Total Quantity Sold", "Revenue"]
    trace1 = go.Scatter(x=revenueByCategory["Category"], y=revenueByCategory["Total Quantity Sold"], name='Quantity Sold', mode='lines+markers', yaxis='y2')
    trace2 = go.Bar(x=revenueByCategory["Category"],y=revenueByCategory["Revenue"], name='Revenue', yaxis='y1')
    return go.Figure(data=[trace2, trace1], layout=layout)

@callback(
    Output(component_id="product_refresh", component_property="data"),
    [Input('submit_button', 'n_clicks')],
    [State('store', 'value'), 
     State('year','value'), 
     State('start_month', 'value'),
     State('end_month', 'value')]
)
def update_products(n_clicks, store, year, start_month, end_month):
    filtered = revenue[revenue["store_location"] == store]
    filtered = filtered[filtered["transaction_date"].dt.year == year]
    filtered = filtered[(shortHand[start_month]+1 <= filtered["transaction_date"].dt.month ) & (filtered["transaction_date"].dt.month <= shortHand[end_month]+1)]
    
    revenueByProduct = filtered.groupby("product_type").agg({"transaction_qty":'sum', "revenue": "sum"}).reset_index().sort_values(by=["revenue"], ascending=False)
    revenueByProduct.columns = ["Product", "Total Quantity Sold", "Revenue"]
    revenueByProduct["Revenue"] = revenueByProduct["Revenue"].apply(lambda x: "$" +f'{round(x,2):,}')
    revenueByProduct["Total Quantity Sold"] = revenueByProduct["Total Quantity Sold"].apply(lambda x: f'{round(x,2):,}')
    return revenueByProduct.head(10).to_dict("records")

@callback(
    Output('total_revenue', 'children'),
    [Input('submit_button', 'n_clicks')],
    [State('store', 'value'), 
     State('year','value'), 
     State('start_month', 'value'),
     State('end_month', 'value')]
)
def update_revenue(n_clicks, store, year, start_month, end_month):
    filtered = revenue[revenue["store_location"] == store]
    filtered = filtered[filtered["transaction_date"].dt.year == year]
    filtered = filtered[(shortHand[start_month]+1 <= filtered["transaction_date"].dt.month ) & (filtered["transaction_date"].dt.month <= shortHand[end_month]+1)]
    return "$" + f'{round(filtered['revenue'].sum(),2):,}'

@callback(
    Output('total_transactions', 'children'),
    [Input('submit_button', 'n_clicks')],
    [State('store', 'value'), 
     State('year','value'), 
     State('start_month', 'value'),
     State('end_month', 'value')]
)
def update_transactions(n_clicks, store, year, start_month, end_month):
    filtered = revenue[revenue["store_location"] == store]
    filtered = filtered[filtered["transaction_date"].dt.year == year]
    filtered = filtered[(shortHand[start_month]+1 <= filtered["transaction_date"].dt.month ) & (filtered["transaction_date"].dt.month <= shortHand[end_month]+1)]
    return f'{round(filtered['transaction_qty'].sum(),0):,}'

if __name__ == '__main__':
    
    app.run(debug=True)
