import mysql.connector

db = mysql.connector.connect(
    host="localhost",
    user="scriptkid69",
    passwd="ubuntupasswd69",
    database="chatbot_database"
)

cs = db.cursor()

try:
    cs.execute(
        "CREATE TABLE clienti (clientID int PRIMARY KEY AUTO_INCREMENT,"
        "nume VARCHAR(50),"
        "oras VARCHAR(50))")
except:
    print("Table clienti is already created.")

try:
    cs.execute(
        "CREATE TABLE clinici (clinicaID int PRIMARY KEY AUTO_INCREMENT,"
        "nume VARCHAR(50),"
        "locatie VARCHAR(50))")
except:
    print("Table clinici is already created.")

try:
    cs.execute(
        "CREATE TABLE programari (programareID int PRIMARY KEY AUTO_INCREMENT,"
        "clientID INT(10),"
        "clinicaID INT(10),"
        "intervalRezervat VARCHAR(50),"
        "FOREIGN KEY (clientID) REFERENCES clienti(clientID) ON DELETE CASCADE,"
        "FOREIGN KEY (clinicaID) REFERENCES clinici(clinicaID) ON DELETE CASCADE)")
except:
    print("Table programari is already created.")

try:
    cs.execute(
        "CREATE TABLE specializari (specializareID int PRIMARY KEY AUTO_INCREMENT,"
        "nume_specializare VARCHAR(50),"
        "clinicaID INT(10))")
except:
    print("Table specializari is already created.")



