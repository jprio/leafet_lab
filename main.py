from flask import Flask, render_template,make_response, redirect, render_template_string, request, session,g, flash, url_for
from flask_cors import CORS, cross_origin
from flask_leaflet import Leaflet
from flask_leaflet import Map
import folium
import requests
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google_auth_oauthlib.flow import InstalledAppFlow
from  oauthlib import oauth2
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from dotenv import load_dotenv
import os
import psycopg_pool
from werkzeug.utils import secure_filename
import gpxpy
import pandas as pd
from folium.map import Marker
from jinja2 import Template
from sqlalchemy import create_engine, Column, Integer, String, Uuid 
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geoalchemy2 import Geometry, WKTElement
from shapely.geometry import LineString
from app.models.domain import Base, User, Collection, Trail, GPXTrack
import config

ALLOWED_EXTENSIONS = {'gpx', 'tcx', 'fit', 'csv'}

DATA = {
        'response_type':"code", # this tells the auth server that we are invoking authorization workflow
        'redirect_uri':"https://laughing-umbrella-p75jgv4prf75v9-5000.app.github.dev/alltrail", # redirect URI https://console.developers.google.com/apis/credentials
        'scope': 'https://www.googleapis.com/auth/userinfo.email', # resource we are trying to access through Google API
        'client_id':os.environ['GOOGLE_CLIENT_ID'], # client ID from https://console.developers.google.com/apis/credentials
        'prompt':'consent'} # adds a consent screen
 
URL_DICT = {
        'google_oauth' : 'https://accounts.google.com/o/oauth2/v2/auth', # Google OAuth URI
        'token_gen' : 'https://oauth2.googleapis.com/token', # URI to generate token to access Google API
        'get_user_info' : 'https://www.googleapis.com/oauth2/v3/userinfo' # URI to get the user info
        }
 
# Create a Sign in URI
CLIENT = oauth2.WebApplicationClient(os.environ['GOOGLE_CLIENT_ID'])
REQ_URI = CLIENT.prepare_request_uri(
    uri=URL_DICT['google_oauth'],
    redirect_uri=DATA['redirect_uri'],
    scope=DATA['scope'],
    prompt=DATA['prompt'])

def get_engine():
    engine = create_engine(f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require')
    return  engine

def get_geo_engine():    
    engine = create_engine(
        f'postgresql://{os.environ["AIVEN_USERNAME"]}:{os.environ["AIVEN_PASSWORD"]}@{os.environ["AIVEN_HOST"]}:{os.environ["AIVEN_PORT"]}/{os.environ["AIVEN_DBNAME"]}?sslmode=require',
        echo=True,
        plugins=["geoalchemy2"]
    )
    return engine

app = Flask(__name__, static_url_path='', 
            static_folder='static')
# Enable CORS for all routes and origins (development only)
CORS(app) 
# Or restrict to specific origins
# CORS(app, resources={r"/api/*": {"origins": "https://frontend.example.com"}})

leaflet = Leaflet()
leaflet.init_app(app)
# login_manager.init_app(app)

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)
app.secret_key="123"


@app.route('/login')
def login():
    "Home"
    return redirect(REQ_URI)

@app.route('/alltrail')
def alltrail_geoalchemy():
    # session.pop('user',None)
    # redirect to the newly created Sign-In URI
    import geopandas as gpd
    from sqlalchemy import func, bindparam
    from geoalchemy2.shape import to_shape
    import geojson
    from geoalchemy2.shape import to_shape

    engine= get_geo_engine()

    Session = sessionmaker(bind=engine)
    session = Session()

    locations = session.query(GPXTrack).all()
    
    query = "SELECT AVG(ST_Y(ST_Centroid(geom))) AS mean_latitude, AVG(ST_X(ST_Centroid(geom))) AS mean_longitude FROM gpx_tracks;"
    df_mean = pd.read_sql(query, session.connection())
    m = folium.Map(location=[df_mean['mean_latitude'].iloc[0], df_mean['mean_longitude'].iloc[0]], zoom_start=10, tiles='OpenStreetMap')
    track_list=[]
    for gpx_track in locations:
        geom = gpx_track.geom
        name = gpx_track.name
        shapely_geom = to_shape(geom)
        geojson_str = geojson.dumps(shapely_geom)

        print(gpx_track)
        track_list.append(gpx_track)
        tooltip = name + '<br>' + f"Length: {gpx_track.length:.2f} km" + ' <br>'  + f"Type: {gpx_track.type}"
         
        # Script de clic qui charge les données d'élévation
        on_click_script = folium.JsCode("""
        function(feature, layer) {
            layer.on('click', function(e) {
                console.log(window.parent.controlElevation);
                if (window.parent.controlElevation) {
                    window.parent.controlElevation.clear();
                    // Charger les données d'élévation pour ce track
                    var gjl = L.geoJson(layer.toGeoJSON(),{
		                onEachFeature: window.parent.controlElevation.addData.bind(window.parent.controlElevation)
		            });

		            // map.addLayer(service).fitBounds(bounds);
                    // window.parent.controlElevation.addData(layer.toGeoJSON());
                }  
                                                                                    
            });
        }
        """)
        if "hike" in str(gpx_track.type):
            color = 'green'
        elif str(gpx_track.type) == "running":
            color = 'blue'
        elif "offroad" in str(gpx_track.type):
            color = 'red'
        else:
            color = 'gray'
        gj=folium.GeoJson(geojson_str, tooltip=folium.Tooltip(text=tooltip), color=color, on_each_feature=on_click_script, )
        gj.add_to(m)
    
    # Passer les données GeoJSON au template
    engine.dispose()
    m.get_root().width = "100%"
    m.get_root().height = "600px"

    return render_template('trails.html', script_map=m.get_root()._repr_html_(), track_list=track_list)

@app.route('/user/<email>')
def login_success(email):
    "Landing page after successful login"
 
    return "Hello %s" % email

@app.route('/home')
def home():

    "Redirect after Google login & consent"
 
    # Get the code after authenticating from the URL
    code = request.args.get('code')
 
    # Generate URL to generate token
    token_url, headers, body = CLIENT.prepare_token_request(
            URL_DICT['token_gen'],
            authorisation_response=request.url,
            redirect_url=request.base_url,
            code=code)
 
    # Generate token to access Google API
    token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(os.environ['GOOGLE_CLIENT_ID'], os.environ['GOOGLE_CLIENT_SECRET']))
    print(token_response.content)

    # Parse the token response
    CLIENT.parse_request_body_response(json.dumps(token_response.json()))
 
    # Add token to the  Google endpoint to get the user info
    # oauthlib uses the token parsed in the previous step
    uri, headers, body = CLIENT.add_token(URL_DICT['get_user_info'])
 
    # Get the user info
    response_user_info = requests.get(uri, headers=headers, data=body)
    info = response_user_info.json()
    session['user']=info
    session.permanent = True
    print(session['user'])
    return redirect('/')

@app.route("/data")
def data():
    return {"message": "Success"}

@app.route("/")
def map():
    response=make_response(render_template("index.html"))
    return response


@app.route("/folium")
def folium_map():
    import geopandas as gpd
    import folium
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.ext.declarative import declarative_base
    from geojson_length import calculate_distance, Unit 
    engine = get_engine()
    gdf = gpd.read_postgis("SELECT name, geom FROM gpx_tracks", con=engine, geom_col='geom')

    # S'assurer que le CRS est EPSG:4326
    if gdf.crs.to_string() != 'EPSG:4326':
        gdf = gdf.to_crs('EPSG:4326')

    # 2. Créer la carte avec Folium
    # On centre la carte sur la moyenne des coordonnées
    m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=10)

    for idx, row in gdf.iterrows():
        geom = row['geom']
        name = row['name']
        print(f"Processing track: {name}, Geometry type: {geom.geom_type}")
        # Ajouter les données géographiques sous forme de GeoJSON
        if geom.geom_type == 'LineString':
            # folium.PolyLine(locations=[(point.y, point.x) for point in geom.coords], color='blue', weight=5, opacity=0.7, tooltip=name).add_to(m)
            # line = Feature(geometry=geom, properties={"name": name})
            tooltip = name + '<br>' + f"Length: {geom.length:.2f} km" + ' <br>   ' + str(calculate_distance(geom, Unit.kilometers)*100) + f"Type: {geom.geom_type}"
            folium.GeoJson(geom, tooltip=folium.Tooltip(text=tooltip), color='red').add_to(m)
        elif geom.geom_type == 'Point':
            folium.Marker(location=(geom.y, geom.x), tooltip=name).add_to(m)

    # 3. Rendre la carte HTML dans Flask
    return render_template('folium.html', map=m._repr_html_())

@app.route("/leaflet")
def leaflet():
    my_map = Map('my-map', center=[-41.139416, -73.025431], zoom=16)
    return render_template('leaflet.html', my_map=my_map)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/elevation', methods=['GET'])
def elevation():
    session.pop('user', None)
    return render_template('elevation.html')

@app.route('/logout')
def logout():
    session.pop('user',None)
    # redirect to the newly created Sign-In URI
    return redirect("/alltrail")

@app.route('/upload', methods = ['POST'])
def upload_file():
    owner = session['user']['sub']
    print(request.form)
    engine = get_engine()
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    type=request.form.get('activity_type')
    print("type : " + type)
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        Session = sessionmaker(bind=engine)
        sess = Session()

        gpx = gpxpy.parse(file)
        for track in gpx.tracks:
            print(track.name)
            # Calculate 3D distance in meters
            distance_3d = track.length_3d()
            print(f"Track: {track.name}, Distance: {distance_3d:.2f} meters")
            
            # Calculate 2D distance
            distance_2d = track.length_2d()
            print(f"Track: {track.name}, 2D Distance: {distance_2d:.2f} meters")
            # elevation gain
            
            for segment in track.segments:
                point= segment.points[0]
                print ('Start at ({0},{1}) -> {2}'.format(point.latitude, point.longitude, point.elevation))

            points = [(point.longitude, point.latitude) for segment in track.segments for point in segment.points]
            line_string = LineString(points)
            
            # Convert to WKT for insertion
            wkt = line_string.wkt
            
            new_track = GPXTrack(name=track.name, geom=WKTElement(wkt, srid=4326), owner=owner, type=type)
            sess.add(new_track)
            print(f"Inserted track: {track.name} with {len(points)} points.")
            sess.commit()    
            sess.close()
            
        for waypoint in gpx.waypoints:
            print ('waypoint {0} -> ({1},{2})'.format(waypoint.name, waypoint.latitude, waypoint.longitude))

        for route in gpx.routes:
            print ('Route:')

        return redirect("/alltrail")

if __name__ == "__main__":
    # app.run()
    app.run(host="0.0.0.0", port=5000, debug=True)