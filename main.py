from flask import Flask, jsonify, request, redirect, url_for, render_template, session, abort, flash
from environs import Env
import pymongo
from bson import ObjectId
from bson.json_util import dumps
from datetime import datetime, timedelta
import os
import pathlib
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pip._vendor import cachecontrol
import google.auth.transport.requests
import requests
from geopy.geocoders import Nominatim 



app = Flask(__name__) #Inicializamos flask

env = Env()
env.read_env()
uri = env('MONGO_URI') #Leemos del archivo .env la variable MONGO_URI

print("Conectandome a la base de datos: ", uri)

clienteBD = pymongo.MongoClient(uri) #Conectamos el cliente a la base de datos

db = clienteBD.ExamenFrontend

marcadores = db.marcadores
visitas = db.visitas

#configuracion de cloudinary
cloudinary.config( 
    cloud_name = "dldq8py5w", 
    api_key = "639814948327696", 
    api_secret = "gCHw-Mz0hg7R3I5BMTyKKYIab8s", 
    secure=True
)

#Para mapas
geolocator = Nominatim(user_agent="mi_app_examen_frontend")

#Configuracion Login Google

app.secret_key = "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" # asegurar que es la misma que en client_secret.json

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "172801514922-vr1u0go6m1l8cuditgmlq42jesumc7lo.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://examen3-two.vercel.app/callback" #Para verlo en vercel
    #redirect_uri="http://localhost:8000/callback" #Para verlo a nivel local
)


@app.route("/login")
def login():
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)


@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500) 

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=GOOGLE_CLIENT_ID,
        clock_skew_in_seconds=10
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = id_info.get("email")
    session["token"] = credentials._id_token

    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


def SesionIniciada():
    if "email" in session and session["email"] is not None:
        return True
    else:
        return False





#Codigo CRUD

#Mostrar todos los marcadores de una persona
@app.route('/', methods=['GET'])
def showMapa():
    if SesionIniciada():
        listaMarcadores = list(marcadores.find({'email': session["email"]}))
        for m in listaMarcadores:
            m['_id'] = str(m['_id'])

        return render_template('mapa.html', email = session["email"], marcadores = listaMarcadores, logueado = SesionIniciada())
    else:
        return render_template('mapa.html', marcadores = [], logueado = SesionIniciada())

#Añadir un nuevo marcador
@app.route('/new', methods = ['GET', 'POST'])
def newMarcador():

    if SesionIniciada():

        if request.method == 'GET':
            return render_template('new.html', logueado = SesionIniciada())
        
        else:
            location = geolocator.geocode(request.form['inputDireccion']) 

            if location is None:

                marcador = {'email': session["email"],
                        }
            else:
                marcador = {'email': session["email"],
                        'lat': location.latitude,
                        'lon': location.longitude,         
                        }
            
            file = request.files['inputImagen']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                marcador['imagen'] = upload_result["secure_url"]
                
            marcadores.insert_one(marcador)
            return redirect(url_for('showMapa'))
        
    else:
        return redirect(url_for('login'))


@app.route('/buscar', methods = ['GET'])
def buscar():
    if SesionIniciada():
        direccion = request.args.get('direccion')
        listaMarcadores = list(marcadores.find({'email': direccion}))
        visitas.insert_one({'email': session["email"], 'token': session["token"], 'fechaVisita': datetime.now().timestamp()})
        for m in listaMarcadores:
                m['_id'] = str(m['_id'])

        listaVisitas = list(visitas.find({'email': direccion}))
        for v in listaVisitas:
            v['_id'] = str(v['_id'])
            v['fechaVisita'] = datetime.fromtimestamp(v['fechaVisita'])

        return render_template('show.html', marcadores = listaMarcadores, correo = direccion, visitas = listaVisitas)
    else:
        return redirect(url_for('login'))



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)  #Este comando arranca flask
