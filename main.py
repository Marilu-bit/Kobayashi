#Padrão para fazer funionar
from flask import Flask
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

#Chamr o views
from views import *

#Colocar o site no ar
if __name__=="__main__":
    app.run(debug=False)


