from pywebio.session import *
from pywebio.pin import *

import pywebio.output as po
from pywebio.input import *
import re  # For email validation
import pymysql  # For MySQL connection


from pywebio import start_server
from pywebio.output import put_html, put_buttons
from pywebio.session import set_env, info as session_info

from flask import Flask
from pywebio.platform.flask import webio_view 
app= Flask(__name__)


# Replace with your actual database credentials (store securely using environment variables)
DATABASE_HOST = "192.168.100.8"
DATABASE_PORT = "3306"
DATABASE_USER = "index"
DATABASE_PASSWORD = "remote"
DATABASE_NAME = "remote"

def connect_to_database():
    """Establishes a connection to the MySQL database."""
    try:
        connection = pymysql.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
            cursorclass=pymysql.cursors.DictCursor  # Use dictionary cursor
        )
        return connection
    except (pymysql.Error, Exception) as err:
        po.put_markdown(f"Error connecting to database: {err}")
        return None


def register_user():
    po.clear()
    put_html("<img src='https://www.abipa-intl.com/hs-fs/hubfs/logo_abipa_international_final_CHARCOAL.png?width=300&height=332&name=logo_abipa_international_final_CHARCOAL.png' alt='Welcome Image' style='width:25%;height:auto;'>")

    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    def validate_email(email):
        if not re.match(email_regex, email):
            return "Invalid email format."
        return None

    def validate_password(password):
        if len(password) < 8:
            return "Password must be at least 8 characters long."
        return None

    role_options = ["operateur", "maintenance", "administrator"]

    form_data = input_group("Registration", [
        input("Email", type=TEXT, name="email", validate=validate_email),
        input("Username", type=TEXT, name="username", required=True),
        input("Password", type=PASSWORD, name="password", validate=validate_password),
        input("Confirm Password", type=PASSWORD, name="confirm_password", required=True),
        select("Role", options=role_options, name="role", required=True)
    ])

    if form_data["password"] != form_data["confirm_password"]:
        po.put_markdown("Passwords do not match.")
        return

    validation_errors = []
    for field, value in form_data.items():
        if field in ("email", "username", "password") and value is None:
            validation_errors.append(f"{field.capitalize()} is required.")

    if validation_errors:
        po.put_markdown("\n".join(validation_errors))
        return

    register(form_data)
    login_form()

def register(data):
    connection = connect_to_database()
    if not connection:
        return

    try:
        sql = "INSERT INTO users (email, username, password, role) VALUES (%s, %s, %s, %s)"
        with connection.cursor() as cursor:
            cursor.execute(sql, (data["email"], data["username"], data["password"], data["role"]))
        connection.commit()
        po.put_text(f"Registration successful! Email: {data['email']}, Username: {data['username']}")
    except (pymysql.Error, Exception) as err:
        po.put_markdown(f"Error registering user: {err}")
    finally:
        if connection:
            connection.close()


def landing_page():
    # Display an image (replace 'image_url' with the actual URL of your image)
    img = open('C:/Picsart_24-06-03_19-45-18-590.png','rb').read()
    po.put_image(img,width='450px',height='200px')
    #put_html("<img src='https://drive.google.com/file/d/1PylMbHq6GSsTEonFBTWIsmfBvbXXJsy_/view?usp=drivesdk' alt='Welcome Image' style='width:25%;height:auto;'>")
    
    put_html("<br><br>")
    # Display Register and Login buttons
    put_buttons(['Login'], onclick=[login_form] )
    

def login_form():
    po.clear()
    #put_html("<img src='https://www.abipa-intl.com/hs-fs/hubfs/logo_abipa_international_final_CHARCOAL.png?width=300&height=332&name=logo_abipa_international_final_CHARCOAL.png' alt='Welcome Image' style='width:25%;height:auto;'>")
    img = open('C:/Picsart_24-06-03_19-45-18-590.png','rb').read()
    po.put_image(img,width='450px',height='200px')
    while True:
        form_data = input_group("Login", [
            input("Username", type=TEXT, name="username", required=True),
            input("Password", type=PASSWORD, name="password", required=True),
        ])

        connection = connect_to_database()
        if not connection:
            return

        try:
            sql = "SELECT * FROM users WHERE username = %s AND password = %s"
            with connection.cursor() as cursor:
                cursor.execute(sql, (form_data["username"], form_data["password"]))
                result = cursor.fetchone()

            if result:
                # Extract user role from the database result
                user_role = result['role']
                po.toast('Login successful!', color='#0AD42E', duration=0)
                po.clear()
                main_page(user_role)
                break
            else:
                po.toast('Invalid username or password. Please try again.', color='#F80909', duration=0)
        except (pymysql.Error, Exception) as err:
            po.put_markdown(f"Error logging in: {err}")
        finally:
            if connection:
                connection.close()



def show_interventions():
    po.clear()
    img = open('C:/interventions.png','rb').read()
    po.put_image(img,width='450px',height='200px')
    put_buttons(['interventions', 'Rapport'], onclick=[ show_interventions, Rapport])

    """Fetches and displays the interventions table."""

    connection = connect_to_database()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM interrr")
            result = cursor.fetchall()
        connection.commit()

        # Convert the result to a list of lists for put_table
        table_data = [list(row.values()) for row in result]

        # Get the column names (assuming all rows have the same keys)
        if result:
            headers = list(result[0].keys())

        po.put_table(table_data, header=headers)

        # Add a select input to choose the intervention ID
        intervention_id = select("Select Intervention ID", options=[row[0] for row in table_data])  # Assuming the id is the first column

        # Add a select input to choose the state
        state_options = ["a traiter", "en traitement", "terminer"]
        new_state = select("New State", options=state_options)

        # Update the state
        update_state(intervention_id, new_state)
    except (pymysql.Error, Exception) as err:
        po.put_markdown(f"Error fetching interventions: {err}")
    finally:
        if connection:
            connection.close()
        #po.put_button('close', onclick=main_page)


def update_state(intervention_id, new_state):
    """Updates the state of an intervention in the database."""

    connection = connect_to_database()
    if not connection:
        return

    try:
        sql = """UPDATE interrr SET state = %s WHERE id = %s"""
        with connection.cursor() as cursor:
            cursor.execute(sql, (new_state, intervention_id))
        connection.commit()
        po.toast('State updated successfully',color='#0AD42E', duration=0)
    except (pymysql.Error, Exception) as err:
        po.toast('Error updating state',color='#F80909', duration=0)
    finally:
        if connection:
            connection.close()



            
    def update_state_form(intervention_id):
     """Fetches and displays the interventions table."""

    state_options = ["a traiter", "en traitement", "terminer", "cloture"]

    new_state = select("New State", options=state_options)

    connection = connect_to_database()
    if not connection:
        return

    try:
        sql = """UPDATE interrr SET state = %s WHERE id = %s"""
        with connection.cursor() as cursor:
            cursor.execute(sql, (new_state, intervention_id))
        connection.commit()
        po.toast('State updated successfully',color='#0AD42E', duration=0)
    except (pymysql.Error, Exception) as err:
        po.toast('Error updating state',color='#F80909', duration=0)
    finally:
        if connection:
            connection.close()


def store_intervention_data(data):
    """Stores the intervention form data in the database."""
    connection = connect_to_database()
    if not connection:
        return

    try:
        # Prepare a parameterized query to prevent SQL injection
        sql = """INSERT INTO interrr (machine, nom_prenom, constat_operateur, date_heure, arret_production, priorite, state)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        with connection.cursor() as cursor:
            cursor.execute(sql, (data["machine"], data["nom_prenom"], data["constat_operateur"], data["date_heure"], data["arret_production"], data["priorite"], "a traiter"))
        connection.commit()
        po.toast('Intervention data stored successfully',color='#0AD42E', duration=0)
    except (pymysql.Error, Exception) as err:
        po.toast('Error storing intervention data',color='#F80909', duration=0)
    finally:
        if connection:
            connection.close()



def intervention_form():
    po.clear()
    img = open("C:/demande d'intervention.png",'rb').read()
    po.put_image(img,width='450px',height='200px')
    put_buttons(['Demande d\'intervention'], onclick=[intervention_form])
  
    """Form for 'Demande d'intervention'."""

    machine_options = ["B1", "B2", "B3", "B4", "M1", "M2", "M3", "M4", "R1", "R2", "R3", "R4", "R5", "SE1", "SE2", "SE3"]
    arret_production_options = ["OUI", "NON"]
    priorite_options = ["Faible", "Normal", "Haute"]
    state_options = ["a traiter"]

    form_data = input_group("Demande d'intervention", [
        select("Machine", options=machine_options, name="machine"),
        input("Nom/Prénom", type=TEXT, name="nom_prenom", required=True),
        textarea("Constat operateur", rows=3, name="constat_operateur"),
        input("Date et Heure", type=DATETIME, name="date_heure"),
        radio("Arrêt Production", options=arret_production_options, name="arret_production"),
        radio("Priorité", options=priorite_options, name="priorite"),
        select("State", options=state_options, name="state"),
    ])

    store_intervention_data(form_data)


def main_page(user_role):
    # Clear the output before displaying the main page
    po.clear()
    img = open("C:/accueil.png",'rb').read()
    po.put_image(img,width='450px',height='200px')

    # Display buttons based on the user's role
    if user_role == 'operateur':
        put_buttons(['Demande d\'intervention'], onclick=[intervention_form])
    elif user_role == 'maintenance':
        put_buttons(['interventions', 'Rapport'], onclick=[show_interventions, Rapport])
    elif user_role == 'RR':
        put_buttons(['register',], onclick=[register_user])    
    elif user_role == 'administrator':
        put_buttons(['Demande d\'intervention', 'interventions', 'Rapport'], onclick=[intervention_form1, show_interventions1, Rapport1])
    else:
        po.put_text("Error: User role not recognized.")

def show_interventions1():
    po.clear()
    img = open('C:/interventions.png','rb').read()
    po.put_image(img,width='450px',height='200px')
    put_buttons(['Demande d\'intervention', 'interventions', 'Rapport'], onclick=[intervention_form1, show_interventions1, Rapport1])

    """Fetches and displays the interventions table."""

    connection = connect_to_database()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM interrr")
            result = cursor.fetchall()
        connection.commit()

        # Convert the result to a list of lists for put_table
        table_data = [list(row.values()) for row in result]

        # Get the column names (assuming all rows have the same keys)
        if result:
            headers = list(result[0].keys())

        po.put_table(table_data, header=headers)

        # Add a select input to choose the intervention ID
        intervention_id = select("Select Intervention ID", options=[row[0] for row in table_data])  # Assuming the id is the first column

        # Add a select input to choose the state
        state_options = ["a traiter", "en traitement", "terminer", "cloture"]
        new_state = select("New State", options=state_options)

        # Update the state
        update_state(intervention_id, new_state)
    except (pymysql.Error, Exception) as err:
        po.put_markdown(f"Error fetching interventions: {err}")
    finally:
        if connection:
            connection.close()
        #po.put_button('close', onclick=main_page)



def store_rapport_data(data):
    """Stores the rapport form data in the database and updates the state in the interrr table."""
    connection = connect_to_database()
    if not connection:
        return

    try:
        # Prepare a parameterized query to prevent SQL injection
        sql_rapport = """INSERT INTO rapport (intervention_id, machine, nom_prenom, constat, date_heure_debut, date_heure_fin, nature_de_defaillance)
                         VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        sql_interrr = """UPDATE interrr SET state = %s WHERE id = %s"""

        with connection.cursor() as cursor:
            cursor.execute(sql_rapport, (data["intervention_id"], data["machine"], data["nom_prenom"], data["constat"], data["date_heure_debut"], data["date_heure_fin"], data["nature_de_defaillance"]))
            cursor.execute(sql_interrr, (data["state"], data["intervention_id"]))
        connection.commit()
        po.toast('Rapport data stored successfully',color='#0AD42E', duration=0)
    except (pymysql.Error, Exception) as err:
        po.toast('Error storing rapport data',color='#F80909', duration=0)
    finally:
        if connection:
            connection.close()


def get_all_intervention_ids():
    """Fetches all intervention ids from the interrr table in the database."""

    connection = connect_to_database()
    if not connection:
        return

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM interrr")
            result = cursor.fetchall()
        connection.commit()

        # Extract the ids from the result
        intervention_ids = [row['id'] for row in result]
        return intervention_ids
    except (pymysql.Error, Exception) as err:
        po.put_markdown(f"Error fetching intervention ids: {err}")
    finally:
        if connection:
            connection.close()




def Rapport():
    po.clear()
    img = open('C:/rapport.png','rb').read()
    po.put_image(img,width='450px',height='200px')
    put_buttons(['interventions', 'Rapport'], onclick=[ show_interventions, Rapport])
   
    """Form for 'Rapport'."""

    machine_options = ["B1", "B2", "B3", "B4", "M1", "M2", "M3", "M4", "R1", "R2", "R3", "R4", "R5", "SE1", "SE2", "SE3"]
    nature_de_defaillance_options = ["Electrique", "Mecanique", "Pneumatique","Hydraulique","Automate","Autre",]
    intervention_id_options = get_all_intervention_ids()  # Function to get all intervention ids from the database
    state_options = [ "terminer"]

    form_data = input_group("Rapport", [
        select("Intervention ID", options=intervention_id_options, name="intervention_id"),
        select("Machine", options=machine_options, name="machine"),
        input("Nom", type=TEXT, name="nom_prenom", required=True),
        textarea("Constat", rows=3, name="constat"),
        input("Date et Heure de debut:", type=DATETIME, name="date_heure_debut"),
        input("Date et Heure de fin:", type=DATETIME, name="date_heure_fin"),
        radio("Nature de defaillance", options=nature_de_defaillance_options, name="nature_de_defaillance"),
        select("State", options=state_options, name="state"),
    ])

    store_rapport_data(form_data)


def Rapport1():
    po.clear()
    img = open('C:/rapport.png','rb').read()
    po.put_image(img,width='450px',height='200px')
    put_buttons(['Demande d\'intervention', 'interventions', 'Rapport'], onclick=[intervention_form1, show_interventions1, Rapport1])
   
    """Form for 'Rapport'."""

    machine_options = ["B1", "B2", "B3", "B4", "M1", "M2", "M3", "M4", "R1", "R2", "R3", "R4", "R5", "SE1", "SE2", "SE3"]
    nature_de_defaillance_options = ["Electrique", "Mecanique", "Pneumatique","Hydraulique","Automate","Autre",]
    intervention_id_options = get_all_intervention_ids()  # Function to get all intervention ids from the database
    state_options = [ "terminer"]

    form_data = input_group("Rapport", [
        select("Intervention ID", options=intervention_id_options, name="intervention_id"),
        select("Machine", options=machine_options, name="machine"),
        input("Nom", type=TEXT, name="nom_prenom", required=True),
        textarea("Constat", rows=3, name="constat"),
        input("Date et Heure de debut:", type=DATETIME, name="date_heure_debut"),
        input("Date et Heure de fin:", type=DATETIME, name="date_heure_fin"),
        radio("Nature de defaillance", options=nature_de_defaillance_options, name="nature_de_defaillance"),
        select("State", options=state_options, name="state"),
    ])

    store_rapport_data(form_data)


def intervention_form1():
    po.clear()
    img = open("C:/demande d'intervention.png",'rb').read()
    po.put_image(img,width='450px',height='200px')
    put_buttons(['Demande d\'intervention', 'interventions', 'Rapport'], onclick=[intervention_form1, show_interventions1, Rapport1])
  
    """Form for 'Demande d'intervention'."""

    machine_options = ["B1", "B2", "B3", "B4", "M1", "M2", "M3", "M4", "R1", "R2", "R3", "R4", "R5", "SE1", "SE2", "SE3"]
    arret_production_options = ["OUI", "NON"]
    priorite_options = ["Faible", "Normal", "Haute"]
    state_options = ["a traiter"]

    form_data = input_group("Demande d'intervention", [
        select("Machine", options=machine_options, name="machine"),
        input("Nom/Prénom", type=TEXT, name="nom_prenom", required=True),
        textarea("Constat operateur", rows=3, name="constat_operateur"),
        input("Date et Heure", type=DATETIME, name="date_heure"),
        radio("Arrêt Production", options=arret_production_options, name="arret_production"),
        radio("Priorité", options=priorite_options, name="priorite"),
        select("State", options=state_options, name="state"),
    ])

    store_intervention_data(form_data)

app.add_url_rule('/', 'webio_view', webio_view(landing_page),methods=['GET','POST'])

if __name__ == "__main__":
    #start_server(landing_page, port=1234, debug=True)
    app.run(debug=False)