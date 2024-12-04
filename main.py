from flask import Flask, jsonify, request, redirect, url_for, render_template
from environs import Env
import pymongo
from bson import ObjectId
from bson.json_util import dumps
from datetime import datetime, timedelta
import os
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url


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


@app.route('/prueba', methods=['GET'])
def get_prueba():
    upload_result = cloudinary.uploader.upload("https://res.cloudinary.com/demo/image/upload/getting-started/shoes.jpg",public_id="shoes")
    print(upload_result["secure_url"])

    return render_template('/OAuth-master/googleOAuth/index.html')





#Mostrar todos los eventos
@app.route('/', methods=['GET'])
def showEventos():
    
    return render_template('eventos.html', eventos = list(eventos.find().sort('timestamp',pymongo.DESCENDING)))
    

#Añadir un nuevo evento
@app.route('/new', methods = ['GET', 'POST'])
def newAd():

    if request.method == 'GET':
        return render_template('new.html')
    
    else:
        file = request.files['inputImagen']
        RutaArchivo = os.path.dirname(__file__)
        print(RutaArchivo)
        upload_result = cloudinary.uploader.upload(RutaArchivo,public_id="shoes")
        print(upload_result["secure_url"])

        evento = {'nombre': request.form['inputNombre'],
                'timestamp': request.form['inputDate'], 
                'lugar': request.form['inputDireccion'],
                'imagen': upload_result["secure_url"]
                }
        eventos.insert_one(evento)
        return redirect(url_for('showEventos'))


#Editar un evento
@app.route('/edit/<_id>', methods = ['GET', 'POST'])
def editEvento(_id):
    
    if request.method == 'GET':

        evento = eventos.find_one({'_id': ObjectId(_id)})
        return render_template('edit.html', evento = evento)
    
    else:

        evento = {'nombre': request.form['inputNombre'],
                'timestamp': request.form['inputTimestamp'], 
                'lugar': request.form['inputLugar'],
                }
        eventos.update_one({'_id': ObjectId(_id) }, { '$set': evento })    

        return redirect(url_for('showEventos'))


#Borrar un evento
@app.route('/delete/<_id>', methods = ['GET'])
def deleteEvento(_id):
    
    eventos.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('showEventos'))


#Mostrar un evento
@app.route('/show/<_id>', methods = ['GET'])
def showEvento(_id):
    
    evento = eventos.find_one({'_id': ObjectId(_id)})
    return render_template('show.html', evento = evento)






if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)  #Este comando arranca flask
