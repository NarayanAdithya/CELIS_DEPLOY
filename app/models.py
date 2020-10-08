from app import db
from app import login
from werkzeug.security import generate_password_hash,check_password_hash
from flask_login import UserMixin
from datetime import datetime


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(64),index=True,unique=True)
    email=db.Column(db.String(120),index=True,unique=True)
    user_role=db.Column(db.String(20))
    Region=db.Column(db.String(20))
    password_hash=db.Column(db.String(128))
    threads=db.relationship('thread',backref='creator',lazy='dynamic')
    posts=db.relationship('post',backref='Author',lazy='dynamic')
    def __repr__(self):
        return '<Role:{} Name:{} Id:{}>'.format(self.user_role,self.username,self.id)
    def set_password(self,password):
        self.password_hash=generate_password_hash(password)
    def check_password(self,password):
        return check_password_hash(self.password_hash,password)


class thread(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    subject=db.Column(db.String(50))
    description=db.Column(db.String(100))
    created=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    posts=db.relationship('post',backref='BelongsTo',lazy='dynamic')
    def __repr__(self):
        return '<Thread by {}>'.format(self.user_id,self.created)

class post(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    message=db.Column(db.String(150))
    time=db.Column(db.DateTime,index=True,default=datetime.utcnow)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
    thread_id=db.Column(db.Integer,db.ForeignKey('thread.id'))
    def __repr__(self):
        return '<Post in thread {} by {}>'.format(self.thread_id,self.user_id)
