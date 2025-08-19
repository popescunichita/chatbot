# libraries
import asyncio
import speech_recognition as sr
import mysql.connector
import ctypes

from nltk_utils import *
from model import *
from train import *

db = mysql.connector.connect(
    host="localhost",
    user="scriptkid69",
    passwd="ubuntupasswd69",
    database="chatbot_database"
)

cs = db.cursor()
weekItervals = ["luni nouă zece",
                "marți nouă zece",
                "miercuri nouă zece",
                "joi nouă zece",
                "vineri nouă zece"]

with open('intents.json', 'r') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

# global variables
clinicaID = ""
responseMessage = ""
intervaleRezervate = []
intervaleDisponibile = []
clientID = ""
numeClient = ""
rescheduleCommand = ""
key = "popescunichitastefan"

# Alege o clinica random
cs.execute("SELECT nume FROM clinici ORDER BY RAND() LIMIT 1")
dbItem = cs.fetchall()
clinica = dbItem[0][0]

# ID clinica
cs.execute("SELECT clinicaID FROM clinici WHERE nume = '{}'".format(clinica))
dbItem = cs.fetchall()
clinicaID = dbItem[0][0]

# Intervale rezervate
cs.execute("SELECT intervalRezervat FROM programari WHERE clinicaID = '{}'".format(clinicaID))
dbItem = cs.fetchall()
try:
    for item in map(lambda x: x[0], dbItem):
        intervaleRezervate.append(item)

except:
    intervaleRezervate.append(dbItem[0][0])
    print("Nu există intervale rezervate.")


def question_respond(message):
    global clinicaID
    global responseMessage
    global intervaleRezervate
    global intervaleDisponibile
    global clientID
    global numeClient
    global rescheduleCommand

    sentence = tokenize(message)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    if message == "":
        responseMessage = "Nu am înțeles. Vă rugăm, repetați!"

    elif prob.item() > 0.85:
        # Comunicare cu chatbot
        for intent in intents["intents"]:
            if tag == intent["tag"]:
                if tag == "cAppointmentInit":
                    responseMessage = random.choice(intent["responses"])

                elif tag == "cAppointment":
                    numeClient = message[:message.rfind(' ')]
                    oras = message[len(numeClient) + 1:]

                    cs.execute("SELECT nume FROM clienti WHERE nume = '{}'".format(numeClient))
                    cs.fetchall()
                    if cs.rowcount < 1:
                        responseMessage = "Nu există programări pe numele dumneavoastră în oraşul nostru."
                        rescheduleCommand = "name"

                    cs.execute("DELETE FROM clienti WHERE nume = '{}' AND oras = '{}'".format(numeClient, oras))
                    db.commit()

                    if cs.rowcount > 0:
                        responseMessage = random.choice(intent["responses"])

                elif tag == "nAppointment":
                    responseMessage = random.choice(intent["responses"])

                elif tag == "name" or rescheduleCommand == "name":
                    rescheduleCommand = ""

                    cs.execute("INSERT INTO clienti(nume) VALUES('{}')".format(message))
                    db.commit()

                    numeClient = message

                    responseMessage = random.choice(intent["responses"])

                elif tag == "city":
                    cs.execute("UPDATE clienti SET oras = '{}' WHERE nume = '{}'".format(message, numeClient))
                    db.commit()

                    cs.execute("SELECT locatie FROM clinici WHERE nume = '{}'".format(clinica))
                    dbItem = cs.fetchall()
                    oras = dbItem[0][0]
                    if message == oras:
                        cs.execute(
                            "SELECT * FROM specializari WHERE clinicaID = {}".format(
                                clinicaID))
                        dbItem = cs.fetchall()
                        responseMessage = random.choice(intent["responses"]) + dbItem[0][1]
                        if len(dbItem) > 1:
                            for specializare in dbItem[1:]:
                                responseMessage += ', ' + specializare[1]

                    else:
                        responseMessage = "Programarea nu poate fi facută pentru oraşul ales de dumneavoastră."

                elif tag == "specialization":
                    intervaleDisponibile = set(weekItervals) - set(intervaleRezervate)
                    responseMessage = random.choice(intent["responses"])
                    for intervalDisponibil in intervaleDisponibile:
                        responseMessage += "\n" + intervalDisponibil

                elif tag == "interval":
                    if len(intervaleRezervate) == 0:
                        cs.execute("SELECT clientID FROM clienti WHERE nume = '{}'".format(numeClient))
                        dbItem = cs.fetchall()
                        clientID = dbItem[0][-1]

                        cs.execute(
                            "INSERT INTO programari (clientID, clinicaID, intervalRezervat) VALUES ({}, {}, '{}')".format(
                                clientID,
                                clinicaID,
                                message))
                        db.commit()

                        cs.execute("SELECT intervalRezervat FROM programari WHERE clientID = {}".format(
                            clientID))
                        dbItem = cs.fetchall()
                        intervalRezervat = dbItem[0][0]
                        intervaleRezervate.append(intervalRezervat)

                        responseChosen = random.choice(intent["responses"])
                        responseMessage = responseChosen[:responseChosen.find('în')] + \
                                          numeClient + " " + \
                                          responseChosen[responseChosen.find('în'):responseChosen.find('.')] + \
                                          intervalRezervat + ". " + \
                                          responseChosen[responseChosen.find('Dacă'):]
                    else:
                        intervalFlag = False
                        for interval in intervaleRezervate:
                            if message == interval:
                                intervalFlag = True

                        if intervalFlag:
                            responseMessage = "Acest interval a fost deja ales. Vă rog alegeți unul dintre intervalele disponibile:"
                            intervaleDisponibile = set(weekItervals) - set(intervaleRezervate)
                            for intervalDisponibil in intervaleDisponibile:
                                responseMessage += "\n" + intervalDisponibil + "\n"


                        else:
                            cs.execute("SELECT clientID FROM clienti WHERE nume = '{}'".format(numeClient))
                            dbItem = cs.fetchall()
                            clientID = dbItem[0][-1]

                            cs.execute(
                                "INSERT INTO programari (clientID, clinicaID, intervalRezervat) VALUES ({},{},'{}')".format(
                                    clientID,
                                    clinicaID,
                                    message
                                ))
                            db.commit()

                            cs.execute("SELECT intervalRezervat FROM programari WHERE clientID = {}".format(
                                clientID))
                            dbItem = cs.fetchall()
                            intervalRezervat = dbItem[0][0]
                            intervaleRezervate.append(intervalRezervat)
                            print(intervaleRezervate)

                            responseChosen = random.choice(intent["responses"])
                            responseMessage = responseChosen[:responseChosen.find('în')] + \
                                              numeClient + " " + \
                                              responseChosen[responseChosen.find('în'):responseChosen.find('.')] + \
                                              intervalRezervat + ". " + \
                                              responseChosen[responseChosen.find('Dacă'):]


                elif tag == "iCheck":
                    responseMessage = random.choice(intent["responses"])

                    cs.execute("DELETE FROM clienti WHERE nume = {}".format(numeClient))
                    db.commit()

                    rescheduleCommand = "name"

                elif tag == "cCheck":
                    responseMessage = random.choice(intent["responses"])

                elif tag == "goodbye":
                    responseMessage = random.choice(intent["responses"])
            else:
                responseMessage = "Nu am înțeles. Vă rugăm, repetați!"

    try:
        return responseMessage

    except KeyError:
        return "Error"
