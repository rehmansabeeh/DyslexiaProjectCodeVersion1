# -*- coding: utf-8 -*-
import re

import os
# import numpy as np
from pymongo import MongoClient
from flask import Flask, jsonify, request, render_template
import json
import nltk
from utility import editDistance
from nltk.tokenize import sent_tokenize, word_tokenize
from flask import Flask, render_template, url_for, request, session, redirect
from flask_pymongo import PyMongo
import bcrypt


app = Flask(__name__)
client = MongoClient("localhost", 27017)
db = client['QawaidForDyslexiaDB']
collection_user = db['UserDB']
collection_urdu_dictionary = db['UrduDictionaryDB']
app.config['MONGO_URI'] = "mongodb://localhost:27017/QawaidForDyslexiaDB"

mongo = PyMongo(app)


@app.route("/",  methods=['GET', 'POST'])
def index():
    return render_template("chillaid/pages/basic-grid.html")


@app.route('/result', methods=['POST', 'GET'])
def result():
    if request.method == 'POST':
        text = request.form.get("text")
        text_dict = {'textstring': text}
        collection_user.insert_one(text_dict)
        urdu_documents = collection_urdu_dictionary.find()
        user_documents = collection_user.find()

    urdu_response = []
    for document in urdu_documents:
        document['_id'] = str(document['_id'])
        document['correctword'] = str(document['correctword'])
        document['form1'] = str(document['form1'])

        urdu_response.append(document)

    print("urdu response", urdu_response)
    response = []
    for document in user_documents:
        document['_id'] = str(document['_id'])
        document['textstring'] = str(document['textstring'])
        response.append(document)
    print("response", response)

    user_latest_text_dict = response[-1]
    user_text_string = user_latest_text_dict['textstring']
    user_text_tokens = word_tokenize(user_text_string)
    final_results = []
    print(user_text_tokens)

    for element in user_text_tokens:
        count = 0
        for document in urdu_response:
            if element == document['correctword']:
                count = count + 1
        if count > 0:
            final_results.append({"user_input": element, "found_count_in_db": count, "status": True, "user_input_length": len(
                element), "suggested_word": element, "comments": "", "edit_distance": 0, "found_count_in_worforms": 0})
        else:
            final_results.append({"user_input": element, "found_count_in_db": count, "status": False, "user_input_length": len(
                element), "suggested_word": "", "comments": "",  "edit_distance": -1, "found_count_in_worforms": 0})

    # initial_results = []

    for element in final_results:
        for key in element:
            if key == "user_input":
                if re.search('[a-zA-Z0-9]', element[key]):
                    element["comments"] = "input is not in Urdu language, please type in Urdu"
                    element["suggested_word"] = "no suggestion available"
                else:
                    for urdu_doc in urdu_response:
                        for urdu_key in urdu_doc:
                            if ((urdu_key != 'correctword') and (urdu_key != '_id')):
                                if urdu_doc[urdu_key] == element[key]:
                                    element["comments"] = "It is probably a word"
                                    element["suggested_word"] = urdu_doc["correctword"]

    for element in final_results:
        min_ed = element["edit_distance"]
        if element["status"] == False:
            for urdu_doc in urdu_response:
                for urdu_key in urdu_doc:
                    if not (urdu_key == "_id"):
                        #print("key", key, "urdu key",urdu_doc[urdu_key])
                        med = editDistance(element["user_input"], urdu_doc[urdu_key], len(
                            element["user_input"]), len(urdu_doc[urdu_key]))

                        if min_ed == -1:
                            min_ed = med
                        if med < min_ed:
                            min_ed = med

                    element["edit_distance"] = min_ed

    s = ""
    for element in final_results:
        if element["status"] == True:
            s = s + "<span style='display:inline; color:green'>" + \
                element["user_input"]+"</span>,"
        else:
            s = s + "<span style='display:inline; color:red'>" + \
                element["user_input"]+"</span>,"

    suggested_word_input = ""
    for element in final_results:
        suggested_word_input = suggested_word_input + \
            "<span style='display:inline; color:black'>" + \
            element["suggested_word"]+"</span>,"

    print(suggested_word_input)
    return render_template("index-u.html", f=s, correct=suggested_word_input, spellCount=3, grammerCount=1, sentenceStructure=1)
    # return render_template("chillaid/pages/basic-grid.html")


@app.route("/login", methods=['GET'])
def login():
    return render_template('login-user.html')
    # return render_template('login-u.html')


@app.route("/login-verification", methods=['POST', 'GET'])
def loginverification():
    if request.method == 'POST':
        users = mongo.db['users']
        print(users)
        login_user = users.find_one({'username': request.form['uname']})
        print(login_user)
        print("hello")
        if login_user:
            print("hello2")
            print(request.form['psw'])
            print(request.form['psw'].encode('UTF-8'))
            print(login_user['password'])
            print(bcrypt.hashpw(request.form['psw'].encode(
                'UTF-8'), login_user['password']))
            if bcrypt.hashpw(request.form['psw'].encode('UTF-8'), login_user['password']) == login_user['password']:
                print("yuaba daba doooo")
                session['username'] = request.form['uname']

                print("hello3")
                return redirect(url_for('taketest'))

        return 'Invalid username/password combination'


@app.route("/register", methods=['GET'])
def register():
    # return render_template('register-user.html')
    return render_template('register-u.html')


@app.route('/registration', methods=['POST', 'GET'])
def registerationprocess():
    if request.method == 'POST':
        users = mongo.db['users']
        existing_user = users.find_one({'username': request.form['uname']})
        print(existing_user)
        if existing_user is None:
            print("hello4")

            hashpass = bcrypt.hashpw(
                request.form['psw'].encode('utf-8'), bcrypt.gensalt())

            users.insert_one(
                {
                    'username': request.form['uname'],
                    'password': hashpass,
                    'isDyslexic': request.form['isDyslexic'],
                    'language': request.form['language'],
                    'reading': request.form['reading']

                }
            )
            session['username'] = request.form['uname']
            print("jellooooooooo")
            return redirect(url_for('taketest'))
        else:
            return 'That username already exists!'

    # redirect(url_for('taketest'))
    return render_template("chillaid/testList.html")


@app.route("/taketest", methods=['GET', 'POST'])
def taketest():
    # return render_template("taketest.html")
    return render_template("chillaid/testList.html")


@app.route("/test1", methods=['GET', 'POST'])
def test1():
    audios = os.listdir('static/audio/')
    collection_test = db['Test']
    test_doc = collection_test.find()
    for doc in (test_doc):
        print(doc)
    print(audios)
    audio0 = audios[0]
    audio1 = audios[1]
    audio2 = audios[2]
    audio3 = audios[3]

    # return render_template("test1.html", audio0 = audio0, audio1 = audio1, audio2 = audio2, audio3 = audio3, audio4= audio4)
    return render_template("chillaid/test1page.html", audio0=audio0, audio1=audio1, audio2=audio2, audio3=audio3)


@app.route('/test1page2', methods=['GET', 'POST'])
def test1page2():

    ans1 = request.form['question1']
    ans2 = request.form['question2']
    ans3 = request.form['question3']
    ans4 = request.form['question4']
    print("ans1",  ans1)
    print("ans2",  ans2)
    print("ans3",  ans3)
    print("ans4",  ans4)

    imgNames = os.listdir('static/imgs')
    img0 = imgNames[0]
    img1 = imgNames[1]
    img2 = imgNames[2]
    img3 = imgNames[3]
    img4 = imgNames[4]
    print(imgNames)
    # return render_template("test1page2.html", img0 = img0,img1 = img1, img2 = img2, img3 = img3, img4= img4)
    return render_template("chillaid/testImage.html", img0=img0, img1=img1, img2=img2, img3=img3, img4=img4)


@app.route("/test1finalpage", methods=['GET', 'POST'])
def test1finalpage():
    ans1 = request.form['question1']
    ans2 = request.form['question2']
    ans3 = request.form['question3']
    ans4 = request.form['question4']
    ans5 = request.form['question5']
    return render_template("test1finalpage.html")


@app.route("/test2", methods=['GET', 'POST'])
def test2():
    return render_template("test2.html")


@app.route("/test3", methods=['GET', 'POST'])
def test3():
    return render_template("test3.html")


@app.route("/test4", methods=['GET', 'POST'])
def test4():
    return render_template("test4.html")


@app.route("/test5", methods=['GET', 'POST'])
def test5():
    return render_template("test5.html")


@app.route("/test6", methods=['GET', 'POST'])
def test6():
    return render_template("test6.html")


@app.route("/test7", methods=['GET', 'POST'])
def test7():
    return render_template("test7.html")


@app.route("/test8", methods=['GET', 'POST'])
def test8():
    return render_template("test8.html")


@app.route("/test9", methods=['GET', 'POST'])
def test9():
    return render_template("test9.html")


@app.route("/test10", methods=['GET', 'POST'])
def test10():
    return render_template("test10.html")


if __name__ == "__main__":
    app.secret_key = 'mysecret'
    app.run()
