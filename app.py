# -*- coding: utf-8 -*-
import re
import numpy as np
from pymongo import MongoClient
from flask import Flask, jsonify, request, render_template
import json
import nltk
from utility import editDistance
from nltk.tokenize import sent_tokenize, word_tokenize

app = Flask(__name__)
client = MongoClient("localhost", 27017)
db = client['QawaidForDyslexiaDB']
collection_user = db['UserDB']
collection_urdu_dictionary = db['UrduDictionaryDB']

@app.route("/")
def index():
    return render_template("chillaid/pages/basic-grid.html")

@app.route('/', methods=['POST'])
def submit_textarea():
    text = request.form.get("text")
    text_dict= {'textstring': text}
    collection_user.insert_one(text_dict) 
    urdu_documents = collection_urdu_dictionary.find()
    user_documents = collection_user.find()
    
    urdu_response = []
    for document in urdu_documents:
        document['_id'] = str(document['_id'])
        document['correctword'] = str(document['correctword'])
        document['form1'] = str(document['form1'])
        urdu_response.append(document)

    response = []
    for document in user_documents:
        document['_id'] = str(document['_id'])
        document['textstring'] = str(document['textstring'])
        response.append(document)

    user_latest_text_dict = response[-1]
    user_text_string = user_latest_text_dict['textstring']    
    user_text_tokens = word_tokenize(user_text_string)
    user_latest_text_token_dict = []


    for element in user_text_tokens:
        count = 0
        for document in urdu_response:
            if element == document['correctword']:
                count = count + 1 
        user_latest_text_token_dict.append({element:count})
    initial_results = []  
    
    for element in user_latest_text_token_dict:
        for key in element:
            #print(element[key])
            if element[key] > 0:
                initial_results.append({key: True})
            else:
                initial_results.append({key: False})



    for element in initial_results:
        for key in element:
            if re.search('[a-zA-Z0-9]', key):
                print("input is not in Urdu language, please type in Urdu")
            else:
                for urdu_doc in urdu_response:
                    for urdu_key in urdu_doc:
                        if ((urdu_key != 'correctword') and (urdu_key != '_id')):
                            if urdu_doc[urdu_key] == key:
                                print("intented word is", urdu_doc['correctword'])

    med_list =[]
    for element in initial_results:
        for key in element:
                for urdu_doc in urdu_response:
                    for urdu_key in urdu_doc:
                        if not (urdu_key == "_id"):
                            #print("key", key, "urdu key",urdu_doc[urdu_key])
                            med = editDistance(key, urdu_doc[urdu_key], len(key), len(urdu_doc[urdu_key]) )
                            med_list.append({urdu_doc[urdu_key]:med, "id": urdu_doc["_id"]})
    
    #final_prediction = []
    min_med = {"edit_distance": 0, "id": ""}
    for element in med_list:
        for key in element:
            if not (key == "id"):
                if min_med["edit_distance"]== 0:
                    min_med["edit_distance"] = element[key]
                    min_med["id"] = element["id"]
                    #print(min_med)             
                else:
                    if min_med["edit_distance"] > element[key]:
                        min_med["edit_distance"] = element[key]
                        min_med["id"] = element["id"]
                    #print(min_med)
    print(min_med)
    
    predicted_id = min_med["id"]
    print(predicted_id)
    final_word = ""

    for docs in urdu_response:
        if docs["_id"] == predicted_id:
           final_word= docs["correctword"]

    print(final_word)
    return render_template("index.html", f=final_word)



if __name__ == "__main__":
    app.run()


