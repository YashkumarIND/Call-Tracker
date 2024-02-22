from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from trading_symbols import symbols_sorted
from distutils.util import strtobool  # Import strtobool function
from serpapi import GoogleSearch
from apscheduler.schedulers.background import BackgroundScheduler
from models.models import db, User, CallBook

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
with app.app_context():
    db.create_all()

    # Check if the default user exists, create if not
    existing_user = User.query.filter_by(username='yashkumarvispute').first()
    if not existing_user:
        test_user = User(username='yashkumarvispute', password='ookook')
        db.session.add(test_user)
        db.session.commit()

# Define the update_trades route
@app.route('/api/update-trades', methods=['POST'])
def update_trades():
    try:
        # Receive the data containing the trade details from the request
        data = request.get_json()

        # Retrieve trade details from the data
        scrip_name = data.get('scrip_name')
        position = data.get('position')
        target1 = data.get('target1')
        target2 = data.get('target2')
        stop_loss = data.get('stop_loss')

        # Use Serpapi to get real-time data
        params = {
            "engine": "google_finance",
            "q": f"{scrip_name}:NSE",
            "api_key": "4bdc90ff4790171cf473075bcd717c27b3c25777d35ddefd07a3fd6187e8f6da" 
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        current_price = float(results["summary"]["price"])

        # Determine trade status based on position and target conditions
        if position == 'Long':
            if current_price >= target1 and current_price < target2:
                status = 'Target 1 Hit'
            elif current_price >= target2:
                status = 'Target 2 Hit'
            elif current_price <= stop_loss:
                status = 'Stop Loss Hit'
            else:
                status = 'Hold' if current_price > stop_loss else 'Exit'
        elif position == 'Short':
            if current_price <= target1 and current_price > target2:
                status = 'Target 1 Hit'
            elif current_price <= target2:
                status = 'Target 2 Hit'
            elif current_price >= stop_loss:
                status = 'Stop Loss Hit'
            else:
                status = 'Hold' if current_price < stop_loss else 'Exit'
        else:
            status = 'Invalid Position'

        return jsonify({'status': status}), 200

    except Exception as e:
        # Handle the exception (e.g., return an error response)
        return jsonify({'error': str(e)}), 500

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
                'AnalystName': trade.AnalystName,
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

# Define the route to retrieve active trades
@app.route('/api/active-trades', methods=['GET'])
def active_trades():
    try:
        # Retrieve trades from the CallBook table where stop loss has not been hit
        trades = CallBook.query.filter(CallBook.Status == 'Active').all()

        # Convert trades to a list of dictionaries
        trades_data = []
        for trade in trades:
            trade_data = {
                'id': trade.id,
                'TimeStamp': trade.TimeStamp,
                'AnalystName': trade.AnalystName,
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

# Define the login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and password == user.password:
            session['user_id'] = user.id
            return redirect(url_for('callbook'))
        else:
            flash('Invalid username/password', 'error')

    return render_template('login.html')

# Define the callbook route
@app.route('/callbook', methods=['GET', 'POST'])
def callbook():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))
        
    user = User.query.filter_by(id=user_id).first()
    analyst_name=user.username

    if request.method == 'POST':
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

# Define the trades route
@app.route('/trades')
def trades():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))

    user_trades = CallBook.query.filter_by(user_id=user_id).all()

    return render_template('trades.html', user_trades=user_trades)

if __name__ == '__main__':
    app.run(debug=True)
