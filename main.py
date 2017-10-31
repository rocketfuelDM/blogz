
from flask import Flask, request, redirect, render_template, send_file, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from hashutils import make_pw_hash, check_pw_hash


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:YES@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
app.secret_key = 'secretkey'
db = SQLAlchemy(app)

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    btitle = db.Column(db.String(80), nullable=False)
    bpost = db.Column(db.Text, nullable=False)
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, btitle, bpost, owner):
        self.btitle = btitle
        self.bpost = bpost
        self.owner = owner

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    entries = db.relationship('Blog', backref='owner')

    def __init__(self, email, password):
        self.email = email
        self.pw_hash = make_pw_hash(password)

@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'index']
    if request.endpoint not in allowed_routes and 'email' not in session:
        return redirect('/login')

@app.route('/', methods=['POST', 'GET'])
def index():
    userlist =  User.query.all()
    return render_template('index.html',userlist=userlist)            

@app.route('/post', methods=['POST', 'GET'])
def post():

    if request.args.get('id'):

        blog = Blog.query.filter_by(id=request.args.get('id')).first()
        user = User.query.filter_by(id=blog.owner_id).first()
        title = blog.btitle
        body = blog.bpost
        return render_template('post.html',post_title=title,post_body=body, user=user)

    elif request.args.get('user'):

        user = User.query.filter_by(id=request.args.get('user')).first()
        blogs = Blog.query.filter_by(owner_id=request.args.get('user'))
        return render_template('singleuser.html', blogs=blogs, user=user)
    else:
        blog_posts = Blog.query.all()
        users = User.query.all()
        return render_template('blog.html', title='Blogz', blog_posts=blog_posts, users=users)

@app.route('/new_post', methods=['POST', 'GET'])
def new_post():
    print("test")
    owner = User.query.filter_by(email=session['email']).first()
    print("test2")
    if request.method == 'POST':
        print("test1")
        title_error = ''
        body_error = ''
        blog_title = request.form['title']
        blog_body = request.form['entry']

        if blog_title == '':
            title_error = flash('Please type a title.')
        if blog_body == '':
            body_error = flash('This field cannot be empty. Please tell us your story.')

        if title_error != '' or body_error != '':
            return render_template('new_post.html', title_error=title_error, body_error=body_error, title=blog_title, body=blog_body)
        else:
            new_blog = Blog(blog_title,blog_body,owner)
            db.session.add(new_blog)
            db.session.commit()
            return redirect('/post?id=' + str(new_blog.id))

    return render_template('new_post.html',title="Build-A-Blog!")    

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form["email"]
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_pw_hash(password, user.pw_hash):
            session['email'] = email
            flash("Logged In")
            return redirect('/')
        else:
            flash('Wrong Password. If you dont have an account please create one.', 'error')
    return render_template("login.html")

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        verify = request.form['verify']

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            new_user = User(email, password)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = email
            return redirect('/')
        else:
            return "<h1>User already exists! If you have an account please login.</h1>"

    return render_template('signup.html')

@app.route('/logout')
def logout():
    del session['email']
    return redirect('/')



if __name__ == '__main__':
    app.run()
