from espressoApi import EspressoConnect
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify,  json
import websockets
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from distutils.util import strtobool  # Import strtobool function
from serpapi import GoogleSearch
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from models.models import db, User, CallBook, AccessToken, ScripCode
from encrypt import encrypt_data, decrypt_data
import re
import asyncio



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '4bdc90ff4790171cf473075bcd717c27b3c25777d35ddefd07a3fd6187e8f6da'

# Initialize SQLAlchemy and migrate
db.init_app(app)
migrate = Migrate(app, db)

scheduler = BackgroundScheduler()
scheduler.start()

# Ensure the tables are created
# with app.app_context():
#     db.create_all()

#     # Check if the default user exists, create if not
#     existing_user = User.query.filter_by(username='yashkumarvispute').first()
#     if not existing_user:
#         test_user = User(username='yashkumarvispute', password='ookook')
#         db.session.add(test_user)
#         db.session.commit()





@app.route('/callbook', methods=['GET', 'POST'])
def callbook():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))
    
    symbols_sorted = ScripCode.query.with_entities(ScripCode.trading_symbol).all()
    symbols_sorted = [symbol[-1] for symbol in symbols_sorted]  
        
    user = User.query.filter_by(id=user_id).first()
    analyst_name=decrypt_data(user.username)

    if request.method == 'POST':

        scrip_code_entry = ScripCode.query.filter_by(trading_symbol=request.form['scripname']).first()

        # Create a new trade object with form data
        callbook = CallBook(
            TimeStamp=datetime.now(),
            AnalystName=analyst_name,
            Date=datetime.now().date(),
            ScripName=request.form['scripname'],
            Position=request.form['position'],
            EntryPrice=request.form['Entry-Price'],
            Target1=request.form['Target1'],
            Target2=request.form['Target2'],
            StopLoss=request.form['StopLoss'],
            Status='Hold',
            # Success=False,
            GainLoss=None,
            Remark=request.form['remark'],
            scrip_Code=scrip_code_entry.scrip_code,
            user_id=user_id
        )

        # Add the trade object to the database session and commit changes
        db.session.add(callbook)
        db.session.commit()

        flash('Trade placed successfully!', 'success')

        # Redirect to the route showing all trades
        return redirect(url_for('trades'))
    
    
    

    # If the request method is GET, render the callbook.html template
    return render_template('callbook.html', symbols=symbols_sorted)



@app.route('/api/add-token', methods=['POST'])
def add_token():
    try:
        # Extract access token from the request body
        access_token = request.json.get('access_token')

        # Ensure access token is provided
        if not access_token:
            return jsonify({'error': 'Access token is required'}), 400

        # Create a new AccessToken instance with provided token
        new_token = AccessToken(accesstoken=access_token, TimeStamp=datetime.utcnow())

        # Add the new token to the session and commit to save it in the database
        db.session.add(new_token)
        db.session.commit()

        return jsonify({'message': 'Access token added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get-scripcodes', methods=['GET'])
def get_scripcode():
    try:
        # Query all scripcodes from the database
        scripcodes = ScripCode.query.all()

        # Convert the list of ScripCode objects to a list of dictionaries
        scripcodes_list = []
        for scripcode in scripcodes:
            scripcodes_list.append({
                'Scrip Code': scripcode.scrip_code,
                'Tick Size': scripcode.tick_size,
                'Inst Type': scripcode.inst_type,
                'Company Name': scripcode.company_name,
                'Indices': scripcode.indices,
                'Industry': scripcode.industry,
                'ISIN Code': scripcode.isin_code,
                'Trading Symbol': scripcode.trading_symbol
            })

        # Return the list of scripcodes as JSON response
        return jsonify({'scripcodes': scripcodes_list}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def get_valid_access_token():
    with app.app_context():
        access_token_entry = AccessToken.query.order_by(AccessToken.TimeStamp.desc()).first()
        if access_token_entry:
            token_expiry = access_token_entry.TimeStamp + timedelta(hours=24)
            if datetime.now() < token_expiry:
                return access_token_entry.accesstoken
        return None



@app.route('/get-ltp', methods=['POST','GET'])
async def websocket_handler(share):
    
    access_token = get_valid_access_token()
    if access_token:
        api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6"
        uri = f"wss://streams.myespresso.com/espstream/api/stream?ACCESS_TOKEN={access_token}&API_KEY={api_key}"
        feed = {"action": "feed", "key": ["ltp"], "value": [share]}

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps(feed))

            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)
                    data=data["data"]
                    # Check if the received data is a list (JSON format)
                    if isinstance(data, list):
                        # Assuming the list contains a dictionary with key 'ltp', extract the 'ltp' value
                        ltp_value = data[0]['ltp']
                        print('LTP:', ltp_value)
                        return ltp_value

                    # Check if the received data is a dictionary (non-JSON format)
                    elif isinstance(data, dict) and 'status' in data and 'message' in data:
                        print("Received non-JSON data:", data['message'])

                except json.JSONDecodeError as e:
                    print("Received non-JSON data:", message)
                except Exception as ex:
                    print("An error occurred:", ex)
    else:
        print("No valid access token found.")






# Define the update_trades route
# @app.route('/api/update-trades', methods=['POST','GET'])
# def update_trades():
#     with app.app_context():
#         try:
#             # Retrieve active trades from the CallBook table where stop loss and target 2 are not hit
#             active_trades = CallBook.query.filter(CallBook.Status == 'Hold').all()

#             for trade in active_trades:
#                 # Retrieve trade details
#                 scrip_name = trade.ScripName
#                 position = trade.Position
#                 target1 = trade.Target1
#                 target2 = trade.Target2
#                 stop_loss = trade.StopLoss
#                 entry_price = trade.EntryPrice

#                 # Use Serpapi to get real-time data
#                 params = {
#                     "engine": "google_finance",
#                     "q": f"{scrip_name}:NSE",
#                     "api_key": "4bdc90ff4790171cf473075bcd717c27b3c25777d35ddefd07a3fd6187e8f6da"
#                 }
#                 search = GoogleSearch(params)
#                 results = search.get_dict()
#                 price_string = results["summary"]["price"]
#                 clean_price_string = re.sub(r'[^\d.]', '', price_string)
#                 current_price = float(clean_price_string)

                

#                 # Determine trade status based on position and target conditions
#                 if position == 'Long':
#                     if current_price >= target1 and current_price < target2:
#                         status = 'Target 1 Hit'
#                     elif current_price >= target2:
#                         status = 'Target 2 Hit'
#                     elif current_price <= stop_loss:
#                         status = 'Stop Loss Hit'
#                     else:
#                         status = 'Hold'
#                 elif position == 'Short':
#                     if current_price <= target1 and current_price > target2:
#                         status = 'Target 1 Hit'
#                     elif current_price <= target2:
#                         status = 'Target 2 Hit'
#                     elif current_price >= stop_loss:
#                         status = 'Stop Loss Hit'
#                     else:
#                         status = 'Hold'
#                 else:
#                     status = 'Invalid Position'


#                 #GainLoss Percentage Calculation
#                 gain_loss = round(((current_price - entry_price) / entry_price * 100),2)

#                 # Update the status of the trade in the database
#                 trade.Status = status
#                 trade.GainLoss=gain_loss
#                 db.session.commit()

#             return jsonify({'message': 'Trades updated successfully'}), 200

#         except Exception as e:
#             # Handle the exception (e.g., log error)
#             return jsonify({'error': str(e)}), 500






@app.route('/api/update-trades', methods=['POST','GET'])
async def update_trades():
        try:
                active_trades = CallBook.query.filter(CallBook.Status == 'Hold').all()
                
                current_price = await websocket_handler("NC34")

                return jsonify({"Share Price": current_price}), 200
    
                for trade in active_trades:
                    # Retrieve trade details
                    scrip_name = trade.ScripName
                    position = trade.Position
                    target1 = trade.Target1
                    target2 = trade.Target2
                    stop_loss = trade.StopLoss
                    entry_price = trade.EntryPrice


                    current_price=asyncio.run(websocket_handler("NC25"))

                    

                    # Determine trade status based on position and target conditions
                    if position == 'Long':
                        if current_price >= target1 and current_price < target2:
                            status = 'Target 1 Hit'
                        elif current_price >= target2:
                            status = 'Target 2 Hit'
                        elif current_price <= stop_loss:
                            status = 'Stop Loss Hit'
                        else:
                            status = 'Hold'
                    elif position == 'Short':
                        if current_price <= target1 and current_price > target2:
                            status = 'Target 1 Hit'
                        elif current_price <= target2:
                            status = 'Target 2 Hit'
                        elif current_price >= stop_loss:
                            status = 'Stop Loss Hit'
                        else:
                            status = 'Hold'
                    else:
                        status = 'Invalid Position'


                    #GainLoss Percentage Calculation
                    gain_loss = round(((current_price - entry_price) / entry_price * 100),2)

                    # Update the status of the trade in the database
                    trade.Status = status
                    trade.GainLoss=gain_loss
                    db.session.commit()

                return jsonify({'message': 'Trades updated successfully'}), 200

        except Exception as e:
            # Handle the exception (e.g., log error)
            return jsonify({'error': str(e)}), 500




# Schedule the update_trades function to run every 15 minutes from 9:15 AM to 3:30 PM, Monday to Friday
scheduler = BackgroundScheduler()
scheduler.add_job(
    update_trades,
    trigger=CronTrigger(day_of_week='mon-fri', hour='9-16', minute='*/15')
)
scheduler.start()

# Define the route to retrieve all trades
@app.route('/api/all-trades', methods=['GET'])
def all_trades():
    try:
        # Retrieve all trades from the CallBook table
        trades = CallBook.query.all()

        # Convert trades to a list of dictionaries
        trades_data = []
        for trade in trades:
            trade_data = {
                'id': trade.id,
                'TimeStamp': trade.TimeStamp,
                'AnalystName': decrypt_data(trade.AnalystName),  # Ensure decrypt_data function is implemented correctly
                'Date': trade.Date,
                'ScripName': trade.ScripName,
                'Position': trade.Position,
                'EntryPrice': trade.EntryPrice,
                'Target1': trade.Target1,
                'Target2': trade.Target2,
                'StopLoss': trade.StopLoss,
                'Status': trade.Status,
                'Remark': trade.Remark,
                'user_id': trade.user_id
            }
            trades_data.append(trade_data)

        return jsonify({'trades': trades_data}), 200
    except Exception as e:
        # Log the error for debugging purposes
        app.logger.error(f"Error retrieving all trades: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500


# Define the route to retrieve active trades
@app.route('/api/active-trades', methods=['GET'])
def active_trades():
    try:
        # Retrieve trades from the CallBook table where stop loss has not been hit
        trades = CallBook.query.filter(CallBook.Status == 'Hold' or CallBook.Status!='Target 2 Hit').all()

        # Convert trades to a list of dictionaries
        trades_data = []
        for trade in trades:
            trade_data = {
                'id': trade.id,
                'TimeStamp': trade.TimeStamp,
                'AnalystName': decrypt_data(trade.AnalystName),
                'Date': trade.Date,
                'ScripName': trade.ScripName,
                'Position': trade.Position,
                'EntryPrice': trade.EntryPrice,
                'Target1': trade.Target1,
                'Target2': trade.Target2,
                'StopLoss': trade.StopLoss,
                'Status': trade.Status,
                'Remark': trade.Remark,
                'user_id': trade.user_id
            }
            trades_data.append(trade_data)

        return jsonify({'trades': trades_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/espresso')
def espresso():
    # Render the espresso.html template
    return render_template('espresso.html')


#espresso api login link for the admin interface
# Your Flask route to render espresso.html
@app.route('/espresso-login')
def espressoLogin():
    # Logic to generate the login URL
    api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
    espressoApi = EspressoConnect(api_key)
    login_url = espressoApi.login_url()

    # Render the espresso.html template with the login URL
    return render_template('espresso.html', login_url=login_url)



# Define the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_users = User.query.all()

        for user in existing_users:
            decrypted_username = decrypt_data(user.username)
            decrypted_password = decrypt_data(user.password)
            if decrypted_username == username and decrypted_password == password:
                session['user_id'] = user.id

                if username == 'admin':
                    api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
                    espressoApi = EspressoConnect(api_key)
                    login_url = espressoApi.login_url()
                    return render_template('espresso.html', login_url=login_url)
                else:
                    return redirect(url_for('trades'))
        # If no matching user is found or incorrect credentials are provided
        flash('Invalid username/password', 'error')

    return render_template('login.html')


#request token code
@app.route('/request-token', methods=['GET'])
def request_token():
    # Extract the request token from the URL parameters
    request_token = request.args.get('request_token')
    return request_token



# Define the callbook route

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['uniqueusername']
        password = request.form['password']
        confirm_password = request.form['confirmpassword']

        # Check if the password and confirm password match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('signup'))

        # Decrypt existing usernames for comparison
        existing_users = User.query.all()
        for user in existing_users:
            decrypted_username = decrypt_data(user.username)
            if decrypted_username == username:
                flash('Username already exists. Please choose a different one.', 'error')
                return redirect(url_for('signup'))

        # Encrypt the username and password
        encrypt_username = encrypt_data(username)
        encrypt_password = encrypt_data(password)

        # Create a new user
        new_user = User(username=encrypt_username, password=encrypt_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Sign up successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')
# Define the trades route

@app.route('/trades')
def trades():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(id=user_id).first()
    decrypt_data_username = decrypt_data(user.username)
    
    if decrypt_data_username == 'admin':
        user_trades = CallBook.query.all()
        api_key = "7bysRZCyXtO7xy9uxk9EtZbNMa2sH6qr"
        secret_key = "BiR30xFE5S4XC9rT0aQcz1ZdAg3CyyBz"
        request_token = request.args.get('request_token')
        espressoApi = EspressoConnect(api_key)
        sessionEspresso = espressoApi.generate_session(request_token, secret_key)   
        access_token = espressoApi.get_access_token(api_key, sessionEspresso)
        access_token = json.loads(access_token)
        token = access_token["data"]["token"]

        # Create an AccessToken instance and add it to the database session
        access_token_entry = AccessToken(accesstoken=token, TimeStamp=datetime.now())
        db.session.add(access_token_entry)
        db.session.commit()

        return render_template('trades.html',user_trades=user_trades)
    else:
        user_trades = CallBook.query.filter_by(user_id=user_id).all()

    return render_template('trades.html', user_trades=user_trades)


@app.route('/accesstokens', methods=['GET'])
def all_tokens():
    try:
        # Retrieve all access tokens from the AccessToken table
        tokens = AccessToken.query.all()

        # Convert token data to a list of dictionaries
        tokens_data = []
        for token in tokens:
            token_data = {
                'id': token.id,
                'accesstoken': token.accesstoken,
                'TimeStamp': token.TimeStamp.strftime("%Y-%m-%d %H:%M:%S")  # Convert timestamp to string
            }
            tokens_data.append(token_data)

        # Return the token data as JSON response
        return jsonify({'tokens': tokens_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    

@app.route('/all-users', methods=['GET'])
def all_users():
    try:
        # Retrieve all users from the User table
        users = User.query.all()

        # Convert user data to a list of dictionaries
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': decrypt_data(user.username),  # Decrypt the username
                'password': decrypt_data(user.password)
            }
            users_data.append(user_data)

        # Return the user data as JSON response
        return jsonify({'users': users_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/delete-trades', methods=['DELETE'])
def delete_trades():
    with app.app_context():
        try:
            db.session.query(CallBook).delete()
            db.session.commit()
            print("All trades deleted successfully.")
            return "All trades deleted successfully."
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting trades: {str(e)}")
            return f"Error deleting trades: {str(e)}", 500


@app.route('/delete-all-data', methods=['DELETE'])
def delete_all_data():
    try:
        # Delete all data from each table
        with app.app_context():
            # Delete all data from the User table
            db.session.query(User).delete()
            db.session.commit()
            
            # Delete all data from the CallBook table
            db.session.query(CallBook).delete()
            db.session.commit()

        print("All data deleted successfully.")
        return "All data deleted successfully.", 200

    except Exception as e:
        # If an error occurs, rollback the changes and return an error message
        db.session.rollback()
        print(f"Error deleting data: {str(e)}")
        return f"Error deleting data: {str(e)}", 500
    

@app.route('/delete-all-scripcode', methods=['DELETE'])
def delete_all_scripcode():
    try:
        # Delete all data from each table
        with app.app_context():
            # Delete all data from the User table
            db.session.query(ScripCode).delete()
            db.session.commit()
            
            
        print("All scripcodes deleted successfully.")
        return "All scripcodes deleted successfully.", 200

    except Exception as e:
        # If an error occurs, rollback the changes and return an error message
        db.session.rollback()
        print(f"Error deleting data: {str(e)}")
        return f"Error deleting data: {str(e)}", 500
    


if __name__ == '__main__':
    app.run(debug=True)
    
    
