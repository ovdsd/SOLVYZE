import os
from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_cors import CORS, cross_origin
import asyncio
from neon_connect import get_db_connection, store_account, store_conversation
from rsa import generate_rsa_keys, encrypt_with_public_key, decrypt_with_private_key

app = Flask(__name__, static_url_path="", static_folder='static')
CORS(app)
app.config.update(SECRET_KEY=os.urandom(24))

load_dotenv()

"""ROUTING"""
@app.route('/')
def home():
    if 'username' in session:
        result = asyncio.run(fetch_user_details(session['username']))
        if result:
            return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/login', methods=["GET"])
@cross_origin()
def login():       
    return render_template('login.html')

@app.route('/register', methods=["GET"])
@cross_origin()
def register():
    return render_template('register.html')

@app.route('/chat')
@cross_origin()
def chat():
    if 'username' in session:
        result = asyncio.run(fetch_user_details(session['username']))
        if result:
            return render_template('chat.html')
    return redirect(url_for('home'))

@app.route('/process_message', methods=['POST'])
@cross_origin(origin='http://localhost:5000')
def process_message():
    if 'username' not in session:
        return jsonify({'error': 'User is not logged in.'}), 400
    data = request.json
    user_msg = data.get('message', '')
    username = session['username']
    ai_response = get_gemini_interaction(username, user_msg)
    return jsonify({'response': ai_response})

@app.route("/logout")
def logout():
    session.pop('username', None)
    session.pop('name', None)# Remove user_id from the session
    return redirect(url_for('home'))

@app.route('/li', methods=['POST'])
@cross_origin(origin='http://localhost:5000')
def li():
    data=request.json
    username = data['username']
    password = data['password']

    if not asyncio.run(fetch_user_details(username)):
        return jsonify({"error": "User does not exist"}), 400

    credentials = asyncio.run(fetch_user_details(username))
    priv_key = credentials['private_key']
    db_password = credentials['password']

    d, n = map(int, priv_key.split(','))

    cleaned_password = db_password.replace('[', '').replace(']', '').replace(' ', '')
    encrypted_password = list(map(int, cleaned_password.split(',')))
    # encrypted_password = list(map(int, db_password.split(',')))

    decrypted_password = decrypt_with_private_key(encrypted_password, d, n)

    if decrypted_password == password:
        session['username']  = credentials['username']
        session['name'] = credentials['display_name']
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 400  

@app.route('/su', methods=['POST'])
@cross_origin(origin='http://localhost:5000')
def su():
    data=request.json
    username = data['username']
    display_name = data['display_name']
    password = data['password']
    confirm_password = data['confirm_password']

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400
        
    res = asyncio.run(fetch_user_details(username))
    if res:
        return jsonify({"error": "User already exists"}), 400

    (e, n), (d, _) = generate_rsa_keys()
    public_key = f"{e},{n}"
    private_key = f"{d},{n}"
    encrypted_password = encrypt_with_public_key(password, e, n)
    asyncio.run(post_user(username, display_name, encrypted_password, public_key, private_key))
        
    session['username']  = username
    session['name'] = display_name
    return jsonify({"message": "Registration successful"}), 200


"""DB INTEGRATION"""

async def fetch_user_details(username):
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
    return result

async def fetch_user_credentials(username):
    pool = await pool.acquire()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("SELECT id, password, private_key FROM users WHERE username = $1", username)
    return result

async def post_user(username, display_name, password, public_key, private_key):
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        result = await conn.fetchrow("INSERT INTO users (username, display_name, password, public_key, private_key) VALUES ($1, $2, $3, $4, $5) RETURNING id", username, display_name, password, public_key, private_key)
    print(result)
    return result

"""SYSTEM"""
def get_gemini_interaction(username, user_msg):
    key = os.getenv('GEMINI_API_KEY')
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(user_msg)
    asyncio.run(store_conversation(username, user_msg, response.text))
    return str(response.text)

# async def handle_gemini(user_id, user_msg):
#     ai_response = get_gemini_interaction(user_msg)
#     await store_conversation(user_id, user_msg, ai_response)
#     return ai_response

if __name__ == '__main__':
    app.run(debug=True)