import backtrader as bt
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.io as pio

class EarningsSurpriseStrategy(bt.Strategy):
    params = (
        ('take_profit_pct', 0.20),
        ('stop_loss_pct', 0.20),
        ('max_holding_days', 45),
    )

    def __init__(self):
        self.entry_price = {}
        self.entry_date = {}
        self.buy_signals = pd.DataFrame(columns=['date', 'close'])
        self.sell_signals = pd.DataFrame(columns=['date', 'close'])

    def next(self):
        for data in self.datas:
            symbol = data._name

            if not self.getposition(data).size:  
                if data.close[0] > data.close[-1]:  
                    self.buy(data=data)
                    self.entry_price[symbol] = data.close[0]
                    self.entry_date[symbol] = self.datas[0].datetime.date(0)

                    self.buy_signals = pd.concat(
                        [self.buy_signals, pd.DataFrame({'date': [data.datetime.date(0)], 'close': [data.close[0]]})],
                        ignore_index=True
                    )

            if self.getposition(data).size:
                pnl = (data.close[0] - self.entry_price[symbol]) / self.entry_price[symbol]
                days_held = (self.datas[0].datetime.date(0) - self.entry_date[symbol]).days

                if pnl >= self.params.take_profit_pct or pnl <= -self.params.stop_loss_pct or days_held >= self.params.max_holding_days:
                    self.sell(data=data)

                    self.sell_signals = pd.concat(
                        [self.sell_signals, pd.DataFrame({'date': [data.datetime.date(0)], 'close': [data.close[0]]})],
                        ignore_index=True
                    )
                    del self.entry_price[symbol]
                    del self.entry_date[symbol]

df = yf.download('SPY', start='2022-01-01', end='2023-01-01')

print("Columns in DataFrame:", df.columns)

if isinstance(df.columns, pd.MultiIndex):
    df = df.xs('SPY', axis=1, level=1) 
    df.columns = [col.lower() for col in df.columns]  

if 'close' in df.columns:
    df['close_selected'] = df['close']
else:
    raise KeyError("No 'close' column found in the DataFrame.")

df['MA50'] = df['close_selected'].rolling(window=50).mean()
df['MA200'] = df['close_selected'].rolling(window=200).mean()

df.index = pd.to_datetime(df.index)

data_feed = bt.feeds.PandasData(dataname=df, name='SPY')

cerebro = bt.Cerebro()
cerebro.addstrategy(EarningsSurpriseStrategy)
cerebro.adddata(data_feed)

results = cerebro.run()
strategy_instance = results[0]

buy_signals = strategy_instance.buy_signals
sell_signals = strategy_instance.sell_signals

fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close_selected'],
    name='SPY',
    increasing_line_color='limegreen',
    decreasing_line_color='crimson',
    opacity=0.9
)])

fig.add_trace(go.Scatter(
    x=df.index,
    y=df['MA50'],
    mode='lines',
    line=dict(color='dodgerblue', width=2, dash='dot'),
    name='50-Day MA'
))

fig.add_trace(go.Scatter(
    x=df.index,
    y=df['MA200'],
    mode='lines',
    line=dict(color='gold', width=2, dash='dash'),
    name='200-Day MA'
))

fig.add_trace(go.Scatter(
    x=buy_signals['date'],
    y=buy_signals['close'],
    mode='markers',
    marker=dict(color='green', symbol='triangle-up', size=12, line=dict(color='black', width=1)),
    name='Buy Signal'
))

fig.add_trace(go.Scatter(
    x=sell_signals['date'],
    y=sell_signals['close'],
    mode='markers',
    marker=dict(color='red', symbol='triangle-down', size=12, line=dict(color='black', width=1)),
    name='Sell Signal'
))

fig.update_layout(
    title={
        'text': 'Advanced Trading Strategy Visualization with Buy/Sell Signals and Moving Averages',
        'y': 0.8865,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top',
        'font': {
            'size': 14,  
            'family': 'Arial, sans-serif',  
            'color': 'white',
        }
    },
    xaxis_title='Date',
    yaxis_title='Price',
    template='plotly_dark',
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", x=0.5, xanchor="center", y=1.1),
    height=700,
    plot_bgcolor='black',
    paper_bgcolor='black',
    font=dict(color='white'),
    hovermode='x unified'
)

fig.update_xaxes(
    rangeslider_visible=False,
    showline=True,
    linewidth=2,
    linecolor='white',
    mirror=True
)
fig.update_yaxes(
    showline=True,
    linewidth=2,
    linecolor='white',
    mirror=True
)

pio.show(fig)

fig.write_html("advanced_trading_strategy_chart.html", auto_open=True)
