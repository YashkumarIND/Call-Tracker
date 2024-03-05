from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'


class CallBook(db.Model):
    __tablename__ = 'CallBook'
    id = db.Column(db.Integer, primary_key=True)
    TimeStamp = db.Column(db.TIMESTAMP, nullable=False)
    AnalystName = db.Column(db.String(50), nullable=False) 
    Date = db.Column(db.Date, nullable=False)
    ScripName = db.Column(db.String(50), nullable=False)
    Position = db.Column(db.String(10), nullable=False)
    EntryPrice = db.Column(db.Float, nullable=False)
    Target1 = db.Column(db.Float, nullable=False)
    Target2 = db.Column(db.Float, nullable=False)
    StopLoss = db.Column(db.Float, nullable=False)
    Status = db.Column(db.String(50), nullable=False)
    GainLoss = db.Column(db.Float, nullable=True)
    Remark = db.Column(db.String(255), nullable=True)
    scrip_Code = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='trades', lazy=True)

    def __repr__(self):
        return f'<Trade {self.ScripName} - {self.EntryPrice}>'
    

class AccessToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accesstoken = db.Column(db.String(1000), unique=True, nullable=False)
    TimeStamp = db.Column(db.TIMESTAMP, nullable=False)
    

    def __repr__(self):
        return f'<User {self.accesstoken}>'


class ScripCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scrip_code = db.Column(db.Integer, nullable=False)
    tick_size = db.Column(db.Float, nullable=False)
    inst_type = db.Column(db.String(50), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    indices = db.Column(db.TEXT, nullable=False)
    industry = db.Column(db.String(255), nullable=False)
    isin_code = db.Column(db.String(50), nullable=False)
    trading_symbol = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<ScripCode {self.scrip_code} - {self.trading_symbol}>'

