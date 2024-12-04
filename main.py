from flask import Flask, jsonify, request, redirect, url_for, render_template
from environs import Env
import pymongo
from bson import ObjectId
from bson.json_util import dumps
from datetime import datetime, timedelta


#Para crear archivos docker ---> docker compose up --build

app = Flask(__name__) #Inicializamos flask

env = Env()
env.read_env()
uri = env('MONGO_URI') #Leemos del archivo .env la variable MONGO_URI

print("Conectandome a la base de datos: ", uri)

clienteBD = pymongo.MongoClient(uri) #Conectamos el cliente a la base de datos

db = clienteBD.ExamenFrontend

ads = db.ads

@app.route('/prueba', methods=['GET'])
def get_prueba():
   
    return "prueba"




@app.route('/', methods=['GET'])
def showAds():
    
    return render_template('ads.html', ads = list(ads.find().sort('date',pymongo.DESCENDING)))
    
@app.route('/new', methods = ['GET', 'POST'])
def newAd():

    if request.method == 'GET' :
        return render_template('new.html')
    else:
        ad = {'author': request.form['inputAuthor'],
              'text': request.form['inputText'], 
              'priority': int(request.form['inputPriority']),
              'date': datetime.now()
             }
        ads.insert_one(ad)
        return redirect(url_for('showAds'))

@app.route('/edit/<_id>', methods = ['GET', 'POST'])
def editAd(_id):
    
    if request.method == 'GET' :
        ad = ads.find_one({'_id': ObjectId(_id)})
        return render_template('edit.html', ad = ad)
    else:
        ad = { 'author': request.form['inputAuthor'],
               'text': request.form['inputText'],
               'priority' : int(request.form['inputPriority'])
             }
        ads.update_one({'_id': ObjectId(_id) }, { '$set': ad })    
        return redirect(url_for('showAds'))

@app.route('/delete/<_id>', methods = ['GET'])
def deleteAd(_id):
    
    ads.delete_one({'_id': ObjectId(_id)})
    return redirect(url_for('showAds'))






if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000, debug=True)  #Este comando arranca flask
