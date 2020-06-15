from hashlib import md5
from datetime import datetime
from app import db,login,app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt

followers = db.Table('followers',
			db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
			db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
			)

class User(UserMixin, db.Model):
	#__tablename__ = user
	id = db.Column(db.Integer, primary_key = True)
	username = db.Column(db.String(32), index = True, unique = True)
	email = db.Column(db.String(64), unique=True)
	password_hash = db.Column(db.String(128))
	about_me = db.Column(db.String(256))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	
	blogs = db.relationship('Blog', backref='author', lazy='dynamic')
	
	followed = db.relationship(
				'User', secondary=followers,
				 primaryjoin=(followers.c.follower_id == id),
				 secondaryjoin=(followers.c.followed_id == id),
				 backref=db.backref('followers', lazy='dynamic'),
				 lazy='dynamic')
				 
	def __repr__(self):
		return '<User{}>'.format(self.username)
		
	def set_password(self, password):
		self.password_hash = generate_password_hash(password)
		
	def check_password(self,password):
		return check_password_hash(self.password_hash, password)
		
	def avatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)
		
	def follow(self,user):
		if not self.is_following(user):
			self.followed.append(user)
			
	def unfollow(self,user):
		if self.is_following(user):
			self.followed.remove(user)
			
	def is_following(self,user):
		return self.followed.filter(followers.c.followed_id == user.id).count()>0
			
			
	def followed_posts(self):
		followed = Blog.query.join(followers, (followers.c.followed_id == Blog.user_id)).filter(followers.c.follower_id == self.id)
		
		own = Blog.query.filter_by(user_id =self.id)
		return followed.union(own).order_by(Blog.time_stamp.desc())
			
	def get_reset_password_token(self, expires_in=600):
		return jwt.encode(\
				{'reset_password': self.id, 'expires_in':time()+ expires_in},\
				app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

	@staticmethod
	def verify_reset_password_token(token):
		try:
			id = jwt.decode(token, app.config['SECRET_KEY'],\
			algorithm='HS256')['reset_password']
		except:
			return
		return User.query.get(id)	
			
		
class Blog(db.Model):
	#__tablename__ = blog
	id = db.Column(db.Integer, primary_key = True)
	title = db.Column(db.String(128), unique=True)
	time_stamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
	body = db.Column(db.String(512))
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	language = db.Column(db.String(5))
	
	def __repr__(self):
		return '<Blog {}>'.format(self.title)
		
@login.user_loader
def load_user(id):
	return User.query.get(int(id))
	
		