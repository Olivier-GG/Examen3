from flask import Flask, jsonify, request, redirect, url_for, render_template, session, abort
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

eventos = db.eventos

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

app.secret_key = "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" # make sure this matches with that's in client_secret.json

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

GOOGLE_CLIENT_ID = "172801514922-vr1u0go6m1l8cuditgmlq42jesumc7lo.apps.googleusercontent.com"
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "client_secret.json")

flow = Flow.from_client_secrets_file(
    client_secrets_file=client_secrets_file,
    scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"],
    redirect_uri="https://examen3-12ppcy1kz-olivier-ggs-projects.vercel.app/callback" #Para verlo a nivel local
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
        abort(500)  # State does not match!

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
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if "google_id" not in session:
            return abort(401)  # Authorization required
        else:
            return function()

    return wrapper

def SesionIniciada():
    if "email" in session and session["email"] is not None:
        return True
    else:
        return False

@app.route("/protected_area")
def protected_area():
    if "email" in session and session["email"] is not None:
        return "Hello {session['email']}! <br/> <a href='/logout'><button>Logout</button></a>"
    else:
        return "Hello World! <br/> <a href='/login'><button>Login with Google</button></a>"







#Codigo CRUD

@app.route('/prueba', methods=['GET'])
def get_prueba():
    upload_result = cloudinary.uploader.upload("https://res.cloudinary.com/demo/image/upload/getting-started/shoes.jpg",public_id="shoes")
    print(upload_result["secure_url"])

    return render_template('/OAuth-master/googleOAuth/index.html')


#Mostrar todos los eventos
@app.route('/', methods=['GET'])
def showEventos():
    
    listaEventos = list(eventos.find().sort('timestamp',pymongo.DESCENDING))
    for e in listaEventos:
        e['_id'] = str(e['_id'])

    return render_template('eventos.html', eventos = listaEventos, logueado = SesionIniciada(), mapa = False)
    

#Añadir un nuevo evento
@app.route('/new', methods = ['GET', 'POST'])
def newAd():

    if SesionIniciada():

        if request.method == 'GET':
            return render_template('new.html', logueado = SesionIniciada())
        
        else:
            location = geolocator.geocode(request.form['inputDireccion']) 

            if location is None:

                evento = {'nombre': request.form['inputNombre'],
                        'timestamp': request.form['inputDate'], 
                        'lugar': request.form['inputDireccion'],
                        'organizador': session["email"]
                        }
            else:
                evento = {'nombre': request.form['inputNombre'],
                        'timestamp': request.form['inputDate'], 
                        'lugar': request.form['inputDireccion'],
                        'lat': location.latitude,
                        'lon': location.longitude,
                        'organizador': session["email"]
                        }
            
            file = request.files['inputImagen']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                evento['imagen'] = upload_result["secure_url"]
                
            eventos.insert_one(evento)
            return redirect(url_for('showEventos'))
        
    else:
        return redirect(url_for('login'))


#Editar un evento
@app.route('/edit/<_id>', methods = ['GET', 'POST'])
def editEvento(_id):
    
    if SesionIniciada():

        if request.method == 'GET':
            evento = eventos.find_one({'_id': ObjectId(_id)})
            return render_template('edit.html', evento = evento, logueado = SesionIniciada())
        
        else:   
            location = geolocator.geocode(request.form['inputDireccion']) 

            if location is None:

                evento = {'nombre': request.form['inputNombre'],
                        'timestamp': request.form['inputDate'], 
                        'lugar': request.form['inputDireccion'],
                        }
            else:
                evento = {'nombre': request.form['inputNombre'],
                        'timestamp': request.form['inputDate'], 
                        'lugar': request.form['inputDireccion'],
                        'lat': location.latitude,
                        'lon': location.longitude,
                        }
            file = request.files['inputImagen']
            if file:
                upload_result = cloudinary.uploader.upload(file)
                evento['imagen'] = upload_result["secure_url"]

            eventos.update_one({'_id': ObjectId(_id) }, { '$set': evento })    

            return redirect(url_for('showEventos'))
        
    else:
        return redirect(url_for('login'))


#Borrar un evento
@app.route('/delete/<_id>', methods = ['GET'])
def deleteEvento(_id):
    if SesionIniciada():
        eventos.delete_one({'_id': ObjectId(_id)})
        return redirect(url_for('showEventos'))
    else:
        return redirect(url_for('login'))


#Mostrar un evento
@app.route('/show/<_id>', methods = ['GET'])
def showEvento(_id):
    
    evento = eventos.find_one({'_id': ObjectId(_id)})
    return render_template('show.html', evento = evento, logueado = SesionIniciada())


#Filtrar por direccion
@app.route('/filtrar', methods = ['GET'])
def filtrar():
    direccion = request.args.get('direccion')

    lista = list(eventos.find().sort('timestamp',pymongo.DESCENDING))

    for e in lista:
        e['_id'] = str(e['_id'])

    location = geolocator.geocode(direccion) 

    listaEventos = []

    if location is None:
        listaEventos = lista
    else:
        for e in lista:
            if (e['lat'] - location.latitude < 0.2 and e['lat'] - location.latitude > -0.2) and (e['lon'] - location.longitude < 0.2 and e['lon'] - location.longitude > -0.2):
                e['_id'] = str(e['_id'])
                listaEventos.append(e)

    mapa = True
    if listaEventos == []:
        mapa = False

    return render_template('eventos.html', eventos = listaEventos, logueado = SesionIniciada(), mapa = mapa)


@app.route('/prueba2', methods = ['GET'])
def prueba():
    return render_template('/streetmap/showMap.html')



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)  #Este comando arranca flask
