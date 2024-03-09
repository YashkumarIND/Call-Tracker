from espressoApi import EspressoConnect
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify,  json
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
import websockets
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from distutils.util import strtobool  
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from models.models import db, User, CallBook, AccessToken, ScripCode
from encrypt import encrypt_data, decrypt_data
import re
import asyncio
from dotenv import load_dotenv
import os
import jwt
import tracemalloc

tracemalloc.start()

load_dotenv()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("APP_SECRET_KEY_SQLALCHEMY")

# Configure JWT secret key
# app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')


# Initialize SQLAlchemy and migrate
db.init_app(app)
migrate = Migrate(app, db)

scheduler = BackgroundScheduler()
scheduler.start()


@app.route('/')
def index():
    return redirect(url_for('signup'))

#     # Function to generate JWT token
# def generate_token(user_id):
#     payload = {
#         'user_id': user_id,
#         'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)  # Token expiration time
#     }
#     token = jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')
#     return token


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['uniqueusername']
        password = request.form['password']
        confirm_password = request.form['confirmpassword']

        
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('signup'))

        
        existing_users = User.query.all()
        for user in existing_users:
            decrypted_username = decrypt_data(user.username)
            if decrypted_username == username:
                flash('Username already exists. Please choose a different one.', 'error')
                return redirect(url_for('signup'))

        
        encrypt_username = encrypt_data(username)
        encrypt_password = encrypt_data(password)

        
        new_user = User(username=encrypt_username, password=encrypt_password)
        db.session.add(new_user)
        db.session.commit()

        flash('Sign up successful. Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')


# Define the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_users = User.query.all()

        accesstoken_current=get_valid_access_token()

        for user in existing_users:
            decrypted_username = decrypt_data(user.username)
            decrypted_password = decrypt_data(user.password)
            if decrypted_username == username and decrypted_password == password:
                session['user_id'] = user.id

                if username == 'admin':
                    if accesstoken_current is not None:
                        return redirect(url_for('trades'))
                    else:
                        api_key = os.getenv("ESPRESSO_API_KEY")
                        espressoApi = EspressoConnect(api_key)
                        login_url = espressoApi.login_url()
                        return render_template('espresso.html', login_url=login_url)
                else:
                    return redirect(url_for('trades'))
       
        flash('Invalid username/password', 'error')

    return render_template('login.html')


def callbook_checker(position, entryprice, target1, target2, stoploss):
    try:
         # Check if any of the input values are null or empty
        if not all((position, entryprice, target1, target2, stoploss)):
            return False, "Please provide all required input values."
        
        if position == "Long":
            if target1 < entryprice or target2 < entryprice: 
                return False, "Check Targets, they seem to be less than Entry Price for a Long Trade!"
            if stoploss > entryprice:
                return False, "Keep stoploss less than Entry Price for a Long Trade!"
            if target2 < target1: 
                return False, "Target 2 should be larger than Target 1 for a Long Trade!"
            if stoploss > target1 or stoploss > target2:
                return False, "Keep Stop Loss less than Targets and Entry Price for a Long Trade!"

        elif position == "Short":
            if target1 > entryprice or target2 > entryprice:
                return False, "Check Targets, they seem to be greater than Entry Price for a Short Trade!"
            if stoploss < entryprice:
                return False, "Keep stoploss greater than Entry Price for a Short Trade!"
            if target2 > target1:
                return False, "Target 2 should be smaller than Target 1 for a Short Trade!"
            if stoploss < target1 or stoploss < target2:
                return False, "Keep Stop Loss greater than Targets and Entry Price for a Short Trade!"
        
        # All conditions passed if reached here
        return True, "All conditions met."

    except Exception as e:
        return False, str(e)



@app.route('/callbook', methods=['GET', 'POST'])
def callbook():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))
    
    symbols_sorted = ScripCode.query.with_entities(ScripCode.trading_symbol).all()
    symbols_sorted = [symbol[-1] for symbol in symbols_sorted]  
        
    user = User.query.filter_by(id=user_id).first()
    analyst_name = decrypt_data(user.username)

    if request.method == 'POST':
        scrip_code_entry = ScripCode.query.filter_by(trading_symbol=request.form['scripname']).first()
        
        # Call the checker function
        checker, message = callbook_checker(
            request.form['position'],
            request.form['Entry-Price'],
            request.form['Target1'],
            request.form['Target2'],
            request.form['StopLoss']
        )

        if not checker:
            flash(message, 'error')
            return redirect(url_for('callbook'))  # Redirect back to the callbook page if error

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
            GainLoss=None,
            Remark=request.form['remark'],
            scrip_Code=scrip_code_entry.scrip_code,
            user_id=user_id
        )
        
        db.session.add(callbook)
        db.session.commit()

        flash('Trade placed successfully!', 'success')
        
        return redirect(url_for('trades'))
    
    return render_template('callbook.html', symbols=symbols_sorted)




@app.route('/api/add-token', methods=['POST'])
def add_token():
    try:
        
        access_token = request.json.get('access_token')

        
        if not access_token:
            return jsonify({'error': 'Access token is required'}), 400

        
        new_token = AccessToken(accesstoken=access_token, TimeStamp=datetime.utcnow())

        
        db.session.add(new_token)
        db.session.commit()

        return jsonify({'message': 'Access token added successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/get-scripcodes', methods=['GET'])
def get_scripcode():
    try:
        
        scripcodes = ScripCode.query.all()

        
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
        api_key = os.getenv("ESPRESSO_API_KEY")
        uri = f"wss://streams.myespresso.com/espstream/api/stream?ACCESS_TOKEN={access_token}&API_KEY={api_key}"
        feed = {"action": "feed", "key": ["ltp"], "value": [share]}

        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps(feed))

            while True:
                try:
                    message = await ws.recv()
                    data = json.loads(message)
                    data=data["data"]
                    
                    if isinstance(data, list):
                        
                        ltp_value = data[0]['ltp']
                        print('LTP:', ltp_value)
                        return ltp_value

                    
                    elif isinstance(data, dict) and 'status' in data and 'message' in data:
                        print("Received non-JSON data:", data['message'])

                except json.JSONDecodeError as e:
                    print("Received non-JSON data:", message)
                except Exception as ex:
                    print("An error occurred:", ex)
    else:
        print("No valid access token found.")








@app.route('/api/update-trades', methods=['POST','GET'])
async def update_trades():
        try:
                active_trades = CallBook.query.filter(CallBook.Status == 'Hold' or CallBook.Status!='Target 2 Hit' or CallBook.Status!='Stop Loss Hit').all()
  
                if len(active_trades)<1:
                    return jsonify({'message': 'No active trades to update now!'}), 200
                
                else:
                    for trade in active_trades:
                        
                        
                        position = trade.Position
                        target1 = trade.Target1
                        target2 = trade.Target2
                        stop_loss = trade.StopLoss
                        entry_price = trade.EntryPrice
                        scrip_Code=trade.scrip_Code

                        scrip_Code_string = f"NC{str(scrip_Code)}"
                        current_price=await websocket_handler(scrip_Code_string)

                        
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


                        
                        gain_loss = round(((current_price - entry_price) / entry_price * 100),2)

                        
                        trade.Status = status
                        trade.GainLoss=gain_loss
                        db.session.commit()

                    return jsonify({'message': 'Trades updated successfully'}), 200

        except Exception as e:
            # Handle the exception (e.g., log error)
            return jsonify({'error': str(e)}), 500




# # Schedule the update_trades function to run every 15 minutes from 9:15 AM to 3:30 PM, Monday to Friday
# scheduler = AsyncIOScheduler()
# scheduler.add_job(
#     update_trades,
#     trigger='cron',
#     day_of_week='mon-fri',
#     hour='9-16',
#     minute='*/15'
# )
# scheduler.start()

# Define the route to retrieve all trades
@app.route('/api/all-trades', methods=['GET'])
def all_trades():
    try:
        
        trades = CallBook.query.all()

        
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
        
        app.logger.error(f"Error retrieving all trades: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500


# Define the route to retrieve active trades
@app.route('/api/active-trades', methods=['GET'])
def active_trades():
    try:
        
        trades = CallBook.query.filter(CallBook.Status == 'Hold' or CallBook.Status!='Target 2 Hit' or CallBook.Status!='Stop Loss Hit').all()

        
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
    
    return render_template('espresso.html')


#espresso api login link for the admin interface
# Your Flask route to render espresso.html
@app.route('/espresso-login')
def espressoLogin():
    
    api_key = os.getenv("ESPRESSO_API_KEY")
    espressoApi = EspressoConnect(api_key)
    login_url = espressoApi.login_url()

    
    return render_template('espresso.html', login_url=login_url)




#request token code
@app.route('/request-token', methods=['GET'])
def request_token():
    # Extract the request token from the URL parameters
    request_token = request.args.get('request_token')
    return request_token



# Define the callbook route



@app.route('/trades')
def trades():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(id=user_id).first()
    decrypt_data_username = decrypt_data(user.username)
    accesstoken_current = get_valid_access_token()

    is_admin = False
    
    if decrypt_data_username == 'admin':

        is_admin = True

        user_trades = CallBook.query.all()

        
        if accesstoken_current is None:
            api_key = os.getenv("ESPRESSO_API_KEY")
            secret_key = os.getenv("ESPRESSO_SECRET_API_KEY")
            request_token = request.args.get('request_token')
            espressoApi = EspressoConnect(api_key)
            sessionEspresso = espressoApi.generate_session(request_token, secret_key)   
            access_token = espressoApi.get_access_token(api_key, sessionEspresso)
            access_token = json.loads(access_token)
            token = access_token["data"]["token"]

            
            access_token_entry = AccessToken(accesstoken=token, TimeStamp=datetime.now())
            db.session.add(access_token_entry)
            db.session.commit()

            return render_template('trades.html',user_trades=user_trades, is_admin=is_admin)
        else:
            return render_template('trades.html',user_trades=user_trades, is_admin=is_admin)
        
    else:
        user_trades = CallBook.query.filter_by(user_id=user_id).all()
        return render_template('trades.html', user_trades=user_trades, is_admin=is_admin)


@app.route('/accesstokens', methods=['GET'])
def all_tokens():
    try:
        
        tokens = AccessToken.query.all()

        
        tokens_data = []
        for token in tokens:
            token_data = {
                'id': token.id,
                'accesstoken': token.accesstoken,
                'TimeStamp': token.TimeStamp.strftime("%Y-%m-%d %H:%M:%S")  
            }
            tokens_data.append(token_data)

        
        return jsonify({'tokens': tokens_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
@app.route('/api/scripcodes',methods=['GET'])
def scripcodes_inTrade():
    try:
        trade=CallBook.query.all()
        

        trade_data=[]
        scrip_codes_new=[]
        for t in trade:
            trade_data.append(t.scrip_Code)
            scrip_codes_new.append( f"NC{str(t.scrip_Code)}")
        return jsonify({"scripcodes":scrip_codes_new}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@app.route('/all-users', methods=['GET'])
def all_users():
    try:
        
        users = User.query.all()

        
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': decrypt_data(user.username),  
                'password': decrypt_data(user.password)
            }
            users_data.append(user_data)

        
        return jsonify({'users': users_data}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500



# @app.route('/delete-trades', methods=['DELETE'])
# def delete_trades():
#     with app.app_context():
#         try:
#             db.session.query(CallBook).delete()
#             db.session.commit()
#             print("All trades deleted successfully.")
#             return "All trades deleted successfully."
#         except Exception as e:
#             db.session.rollback()
#             print(f"Error deleting trades: {str(e)}")
#             return f"Error deleting trades: {str(e)}", 500


# @app.route('/delete-all-data', methods=['DELETE'])
# def delete_all_data():
#     try:
#         with app.app_context():
#             # Delete data from User table
#             db.session.query(User).delete()

#             # Delete data from CallBook table
#             db.session.query(CallBook).delete()

#             # Delete data from AccessToken table
#             db.session.query(AccessToken).delete()

#             # Commit the changes
#             db.session.commit()

#         print("All data deleted successfully.")
#         return "All data deleted successfully.", 200

#     except Exception as e:
#         # Rollback changes if an error occurs
#         db.session.rollback()
#         print(f"Error deleting data: {str(e)}")
#         return f"Error deleting data: {str(e)}", 500

    


@app.route('/logout',methods=['GET'])
def logout():
    try:
        session.pop('user_id', None)
        return redirect(url_for('login')), 200
    except Exception as e:
        
        return f"Error deleting data: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
    
