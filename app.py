from flask import Flask, request, render_template
from sqlalchemy import create_engine
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
import plotly
import subprocess
import os


app = Flask(__name__)

commands_exe = []

@app.route("/")
def home_page():
    
        db = create_engine("postgresql://postgres:1999@localhost:5432/telegraf")
        conn = db.connect()
        smtp = '''select time,db,avg(tup_fetched) as tup_fetched from postgresql
        group by "time","db" order by time desc
        '''
        res = conn.execute(smtp)

        postgres_ = pd.DataFrame(res.fetchall(), columns=res.keys())
        fig = px.line(postgres_, x='time', y='tup_fetched', color='db', template="plotly_white",
                    title="Line chart avg fetched data")
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        fig2 = px.bar(postgres_, x='db', y='tup_fetched', color='db', template="plotly_white",
                    title="bar chart for average fetched data",color_discrete_sequence=['red','blue','yellow','orange','grey','green','brown'])
        graph2JSON = json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder)
        table_query = "select time,db,tup_fetched from postgresql"
        result = conn.execute(table_query)
        tot = pd.DataFrame(result.fetchall(), columns=result.keys())
        tot['time'] = tot['time'].astype(str)
        tab= tot.to_json(orient='records')
        fig_table = go.Figure(data=[go.Table(
        header=dict(values=list(tot.columns),
                    align='left'),
        cells=dict(values=tot.transpose().values.tolist(),
                align='left'))
            ])
        table_plot = json.dumps(fig_table, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template("index.html", data=graphJSON, data2=graph2JSON,table = table_plot,tabulator_data = tab)
    

@app.route("/connection",methods=['GET', 'POST'])
def connection():
    if request.method == 'GET':
        return render_template("connection.html")
    if request.method == 'POST' :
        connection_string = request.form.get('command')
        connection_database = request.form.get('database')
        connection_name = request.form.get('connection_name')
        out = f"""
[[outputs.postgresql]]
  connection = "postgresql://postgres:1999@127.0.0.1:5432/telegraf"
[[inputs.{connection_database}]]
#   ## specify address via a url matching:
address = "{connection_string}"
        """
        with open(f'{connection_name}.conf', 'w') as f:
             f.write(out)
        telegraf_out = os.popen(f'telegraf --config {connection_name}.conf').read()  
        # commands_exe.append(command)
        return render_template("connection.html",output=out,telegraf_out=telegraf_out)
        
