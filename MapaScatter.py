import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go
from collections import OrderedDict
from metpy.interpolate import interpolate_to_grid, remove_nan_observations,remove_repeat_coordinates

    
app = dash.Dash(__name__)

dfcities = pd.read_csv('BRAZIL_CITIES_REV2022.csv', usecols = ['CITY', 'STATE', 'LONG', 'LAT'])

dfmask = dfcities['STATE'] == 'SP'

dfsp = dfcities[dfmask]

dfsp.rename(columns={'CITY': 'Munic', 'LAT':'lon', 'LONG':'lat'}, inplace = True)

colnames = ['Munic','code','uf','nome_est','lat','lon','data','preci','nan']
df=pd.read_csv("data.csv", sep=';', names=colnames) 
df = df.iloc[1: , :].reset_index(drop=True)
df = df.replace({',':'.'}, regex = True)
del df['nan']
df['data'], df['hora'] = df['data'].str.split(' ', 1).str
df['data'] = df['data'].astype(str, errors = 'raise')
df['preci'] = df['preci'].astype(float, errors = 'raise')
df['lat'] = df['lat'].astype(float, errors = 'raise')
df['lon'] = df['lon'].astype(float, errors = 'raise')
df['Munic'] = df['Munic'].str.capitalize()
df = df.groupby(['Munic', 'code', 'uf', 'nome_est', 'lat', 'lon', 'data']).agg({'preci':'sum'}).reset_index()
datalist = list(OrderedDict.fromkeys(df['data'].tolist()))

app.layout = html.Div([
    html.H1('Web Application Dashboards with Dash', style = {'text-align':'center'}),
    dcc.Dropdown(id = 'slct_day',
                options = datalist,
                multi = False,
                value = '2022-02-01',
                style = {'width':'40%'}
                ),
    html.Div(id = 'output_container', children = []),
    html.Br(),
    dcc.Graph(id = 'Rain_Map', figure = {})
    
])

@app.callback(
    [Output(component_id = 'output_container', component_property = 'children'),
     Output(component_id = 'Rain_Map', component_property = 'figure')],
    [Input(component_id = 'slct_day', component_property = 'value')]
)
def update_graph(option_slctd):
    print(option_slctd)
    print(type(option_slctd))
     
    container = 'O dia escolhido pelo usuário é: {}'.format(option_slctd)
     
    dff = df.copy()
    dff = dff[dff['data'] == option_slctd]
    dff = pd.concat([dff, dfsp]).sort_values(by = 'Munic')
    dff['preci'] = dff['preci'].fillna(0)
    
    lat=dff.lat.tolist()
    lon=dff.lon.tolist()
    pre=dff.preci.tolist()
    la=[]
    lo=[]
    pr =[]
    for i in range(0,len(dff)):
        la.append(lat[i])
        lo.append(lon[i])
        pr.append(pre[i])
        
    x, y, z = remove_repeat_coordinates(la, lo, pr)
        
    gx, gy, img = interpolate_to_grid(x, y, z, interp_type= 'rbf', 
                                              rbf_smooth = 10,
                                              hres=0.01)
    
    for i in range(0, len(img)):
        for j in range(0, len(img[0])):
            if img[i, j] < 0:
                img[i, j] = 0
    
    gx1 = gx.ravel().tolist()
    gy1 = gy.ravel().tolist()
    img1 = img.ravel().tolist()
    
    dicionário = {
    'lat': gx1,
    'lon': gy1, 
    'valor':img1
    }
     
    fig = go.Figure(go.Scattermapbox(
        lat=gy1, 
        lon=gx1,
        mode='markers',
        marker=go.scattermapbox.Marker(
            size=8,
            color=img1,
            opacity=0.7
        ),
    ))
    
    
    fig.update_layout(mapbox_style="carto-positron",
                  mapbox_center_lon=-46.635,
                  mapbox_center_lat=-23.547,
                  mapbox_zoom=5)

    
    return container, fig

if __name__ == '__main__':
    app.run_server(port = 3060, debug=True, use_reloader=True)