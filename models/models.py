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
    # Success = db.Column(db.Boolean, default=False, nullable=True)
    GainLoss = db.Column(db.Float, nullable=True)
    Remark = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='trades', lazy=True)


    def __repr__(self):
        return f'<Trade {self.ScripName} - {self.EntryPrice}>'

