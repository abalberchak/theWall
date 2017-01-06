from flask import Flask, render_template, redirect, request, session, flash, Markup
from flask.ext.bcrypt import Bcrypt
# the "re" module will let us perform some regular expression operations
import re
from mysqlconnection import MySQLConnector

# password = 'pasword';
# encrypted_password = md5.new(password).hexdigest();
# print encrypted_password;


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
NAME_REGEX = re.compile(r'^[a-zA-Z]+$')
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = "SECRET"
mysql = MySQLConnector(app, 'wall_db')

@app.route('/')
def index():
	return render_template("index.html")



@app.route('/wall')
def wall():
	# query = "SELECT users.first_name, messages.users_id, messages.created_at, messages.message, messages.id FROM messages JOIN users ON messages.users_id = users.id ORDER BY messages.created_at DESC"
	query = "SELECT users.first_name, messages.users_id, messages.created_at, messages.message, messages.id FROM messages JOIN users ON messages.users_id = users.id ORDER BY messages.created_at DESC"
	
	messages = mysql.query_db(query)
	# print messages

	query = "SELECT users.first_name, comments.users_id, comments.messages_id, comments.comment, comments.id as comment_id, comments.created_at, comments.updated_at FROM comments JOIN users ON comments.users_id = users.id ORDER BY comments.created_at DESC"
	

	comments = mysql.query_db(query)
	# print comments

	return render_template('wall.html', wall_messages=messages, wall_comments=comments)



@app.route('/users/create', methods=['POST'])
def create():
	# errors = ""
	if len(request.form['first_name']) < 2:
		message = Markup("<h5 class='red'>First name must be letters only and have at least 2 characters!</h5>")
		# errors += message
		flash(message)
		print "First name must be letters only and have at least 2 characters!"
		return redirect('/')

	if not NAME_REGEX.match(request.form['first_name']):
		message = Markup("<h5 class='red'>First name must be letters only!</h5>")
		# errors += message
		flash(message)
		print "First name must be letters only!"
		return redirect('/')

	elif len(request.form['last_name']) < 2:
		message = Markup("<h5 class= 'red'>Last name must have at least 2 characters!</h5>")
		flash(message)
		print "Last name must have at least 2 characters!"
		return redirect('/')

	elif not NAME_REGEX.match(request.form['last_name']):
		message = Markup("<h5 class='red'>Last name must be letters only!</h5>")
		flash(message)
		print "Last name must be letters only!"
		return redirect('/')

	elif len(request.form['email']) < 1:
		message = Markup("<h5 class='red'>Please enter a valid email!<h5>")
		flash(message)
		print "Please enter a valid email!"
		return redirect('/')

	elif not EMAIL_REGEX.match(request.form['email']):
		message = Markup("<h5 class='red'>Please enter a valid email!</h5>")
		flash(message)
		print "Please enter a valid email!"
		return redirect('/')	

	elif len(request.form['password']) < 8:
		message = Markup("<h5 class = 'red'>Password must be at least 8 characters long!</h5>")
		flash(message)
		return redirect('/')

	elif (request.form['password'] != request.form['password_confirmation']):
		message = Markup("<h5 class = 'red'>Password and Password Confirmation must match!</h5>")
		flash(message)
		return redirect('/')

	else:

		first_name = request.form['first_name']
		last_name = request.form['last_name']
		email = request.form['email']
		password = request.form['password']
		pw_hash = bcrypt.generate_password_hash(password)

		query = "INSERT INTO users (first_name, last_name, email, pw_hash, created_at, updated_at) VALUES (:first_name, :last_name, :email, :pw_hash, NOW(), NOW())"

		data = {
			'first_name': first_name,
			'last_name': last_name,
			'email': email,
			'pw_hash': pw_hash
			}
		user = mysql.query_db(query, data)
		message = Markup("<h5 class='green'>User " + first_name + " " + last_name + " has been registered!</h5>")
		flash(message)
		return redirect('/')


@app.route('/users/login', methods=['POST'])
def login():
	email = request.form['email']
	password = request.form['password']
	query = "SELECT * FROM users WHERE email = :email LIMIT 1"
	data = {'email': email

			}
	user = mysql.query_db(query, data)
	# print user

	if bcrypt.check_password_hash(user[0]['pw_hash'], password):
		session['id'] = int(user[0]['id'])
		session['name'] = user[0]['first_name']
		# print session['id']
		return redirect('/wall')

	else: 
		# print bcrypt.check_password_hash(user[0]['pw_hash'], password)
		message = Markup("<h5 class='red'>Email and password do not match. Please try again.</h5>")
		flash(message)
		return redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
	session.pop('id', None)
	session.pop('name', None)
	return redirect('/')


@app.route('/post_message', methods=['POST'])
def post_message():

	post_message = request.form['post_message']

	query = "INSERT INTO messages (message, created_at, updated_at, users_id) VALUES (:message, NOW(), NOW(), :users_id)"

	data = {
		'message': request.form['post_message'],
		'users_id': session['id'],
		}

	messages = mysql.query_db(query, data)
	return redirect('/wall')


@app.route('/delete_message/<id>', methods=['POST'])
def delete_message(id):


	query = 'SELECT * FROM messages WHERE id = :id'
	data = {'id': id}
	messages = mysql.query_db(query, data)


	if messages:
		if messages[0]['users_id'] == session['id']:

			query = 'DELETE FROM comments WHERE messages_id = :id'
			data = {'id': id}
			mysql.query_db(query, data)

			query = 'DELETE FROM messages WHERE id = :id'
			data = {'id': id}
			mysql.query_db(query, data)


	return redirect('/wall')



@app.route('/post_comment', methods=['POST'])
def post_comment():

	
	query = "INSERT INTO comments (comment, created_at, updated_at, messages_id, users_id) VALUES (:comment, NOW(), NOW(), :messages_id, :users_id)"
	data = {
		'comment': request.form['post_comment'],
		'messages_id': request.form['message_id'],
		'users_id': session['id'],
		}
	print request.form['message_id']
	comments2 = mysql.query_db(query, data)
	

	return redirect('/wall')



@app.route('/delete_comment/<id>')
def delete_comment(id):

	
	query = 'SELECT * FROM comments WHERE id = :id'
	data = {'id': id}
	comments = mysql.query_db(query, data)
	print id


	if comments:
		if comments[0]['users_id'] == session['id']:

			query = 'DELETE FROM comments WHERE id = :id'
			data = {'id': id}
			comments = mysql.query_db(query, data)



	return redirect('/wall')










app.run(debug=True)