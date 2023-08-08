from flask import Flask, flash, jsonify, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,IntegerField
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///twitter.db'
db = SQLAlchemy(app)

#Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)


# User model
class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    tweets = db.relationship('Tweet', backref='user', lazy=True)

class UserForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")

#Tweet model
class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(80),nullable=False)
    content = db.Column(db.String(280), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class TweetForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired()])
	#content = StringField("Content", validators=[DataRequired()], widget=TextArea())
	content = StringField('Content', validators=[DataRequired()])
	submit = SubmitField("Submit")

class LoginForm(FlaskForm):
	username = StringField("Username", validators=[DataRequired()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Submit")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/')
def home():
    tweets = Tweet.query.all()
    return render_template('home.html',tweets=tweets)

@app.route('/tweet/<int:id>')
def tweet(id):
	tweet = Tweet.query.get_or_404(id)
	user=User.query.get_or_404(tweet.user_id)
	return render_template('tweet.html', tweet=tweet,user=user)

@app.route('/add-tweet', methods=['GET', 'POST'])
def add_tweet():
	form = TweetForm()

	if form.validate_on_submit():
		tweet = Tweet(title=form.title.data, content=form.content.data, user_id=current_user.id)
		# Clear The Form
		form.title.data = ''
		form.content.data = ''
		
		# Add post data to database
		db.session.add(tweet)
		db.session.commit()

		# Return a Message
		flash("Tweet posted Successfully!")

	# Redirect to the webpage
	return render_template("add_tweet.html", form=form)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tweet(id):
	tweet = Tweet.query.get_or_404(id)
	form = TweetForm()
	if form.validate_on_submit():
		tweet.title = form.title.data
		tweet.content = form.content.data
		# Update Database
		db.session.add(tweet)
		db.session.commit()
		flash("Tweet Has Been Updated!")
		return redirect(url_for('home'))
	
	if current_user.id == tweet.user_id :
		form.title.data = tweet.title
		#form.author.data = post.author
		form.content.data = tweet.content
		return render_template('edit_tweet.html', form=form)
	else:
		flash("You Aren't Authorized To Edit This tweet...")
		tweets = Tweet.query.all() 
		return render_template("home.html", tweets=tweets)


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user:
			# Check the hash
			if (user.password==form.password.data):
				login_user(user)
				return redirect(url_for('home'))
			else:
				flash("Wrong Password - Try Again!")
		else:
			flash("That User Doesn't Exist! Try Again...")


	return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
	logout_user()
	flash("You Have Been Logged Out!  Thanks For Stopping By...")
	return redirect(url_for('login'))


@app.route('/api/register', methods=['GET', 'POST'])
def register_user():
	form = UserForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None:
			# Hash the password!!!
			user = User(username=form.username.data,password=form.password.data)
			db.session.add(user)
			db.session.commit()
		form.username.data = ''
		form.password.data = ''

		flash("User Added Successfully!")
	return render_template("register.html", form=form)



if __name__ == '__main__':
    # db.create_all()
    app.run(debug=True)
