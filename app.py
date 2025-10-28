# Paste your Python code here
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "supersecretkey123"

# --- Configuration ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    score = db.Column(db.Integer, default=0)
    kills = db.Column(db.Integer, default=0)
    matches = db.Column(db.Integer, default=0)
    rank = db.Column(db.String(50), default="Recruit")
    profile_pic = db.Column(db.String(200), default="/static/default-avatar.png")
    is_admin = db.Column(db.Boolean, default=False)
    clan_id = db.Column(db.Integer, db.ForeignKey('clan.id'), nullable=True)

    def update_rank(self):
        if self.kills >= 1000: self.rank = "Second Lieutenant"
        elif self.kills >= 800: self.rank = "Chief Warrant Officer III"
        elif self.kills >= 600: self.rank = "Chief Warrant Officer II"
        elif self.kills >= 500: self.rank = "Warrant Officer"
        elif self.kills >= 300: self.rank = "Staff Sergeant"
        elif self.kills >= 100: self.rank = "Sergeant"
        elif self.kills >= 50: self.rank = "Corporal"
        elif self.kills >= 20: self.rank = "Lance Corporal"
        elif self.kills >= 10: self.rank = "Private"
        else: self.rank = "Recruit"

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(50), nullable=False)

class Clan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slogan = db.Column(db.String(200), nullable=True)
    logo = db.Column(db.String(200), default="/static/default-clan.png")
    leader_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    members = db.relationship('User', backref='clan', lazy=True, foreign_keys='User.clan_id')

# --- Initialize DB & Default Admin ---
with app.app_context():
    db.create_all()

    # Create default admin if missing
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@mmc.com",
            password=generate_password_hash("FKgoat@2025#"),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Default admin created: username=admin, password=FKgoat@2025#")
    elif not admin.is_admin:
        admin.is_admin = True
        db.session.commit()
        print("✅ Default admin fixed: is_admin=True")
# ⚠️ No session assignment here → no auto-login

# --- Routes ---
@app.route("/", methods=["GET","POST"])
def home():
    page = request.args.get("page", "home")
    user = None
    users = []
    events = Event.query.order_by(Event.id.desc()).all()
    clans = Clan.query.all()

    if 'user_id' in session:
        user = User.query.get(session['user_id'])

    # LOGIN
    if page=="login" and request.method=="POST":
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and check_password_hash(existing_user.password, password):
            session['user_id'] = existing_user.id
            flash("Logged in successfully!", "success")
            return redirect(url_for('home', page="dashboard"))
        else:
            flash("Invalid credentials!", "danger")

    # REGISTER
    if page=="register" and request.method=="POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter((User.username==username)|(User.email==email)).first():
            flash("Username or email exists!", "danger")
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('home', page="login"))

    # CONTACT
    if page=="contact" and request.method=="POST":
        flash("Message sent successfully!", "success")

    # LEADERBOARD
    if page=="leaderboard":
        users = User.query.order_by(User.score.desc()).all()

    return render_template("index.html", page=page, user=user, users=users, events=events, clans=clans)

# --- Profile update ---
@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        flash("Login first!", "danger")
        return redirect(url_for('home'))

    user = User.query.get(session['user_id'])

    # Update profile pic
    file = request.files.get('profile_pic')
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        user.profile_pic = f"/{path.replace('\\', '/')}"

    # Update rank manually
    rank = request.form.get('rank')
    if rank:
        user.rank = rank

    db.session.commit()
    flash("Profile updated!", "success")
    return redirect(url_for('home', page='profile'))

# --- Upload Profile Pic ---
@app.route('/upload', methods=['POST'])
def upload_profile_pic():
    if 'user_id' not in session:
        flash("Login first!", "danger")
        return redirect(url_for('home'))
    file = request.files['profile_pic']
    if file:
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        user = User.query.get(session['user_id'])
        user.profile_pic = f"/{path.replace('\\','/')}"
        db.session.commit()
        flash("Profile picture updated!", "success")
    return redirect(url_for('home', page='profile'))

# --- Add Event (Admin Only) ---
@app.route("/add_event", methods=["GET","POST"])
def add_event():
    if 'user_id' not in session:
        flash("Login required!", "danger")
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash("Admin only!", "danger")
        return redirect(url_for('home'))
    if request.method=="POST":
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        new_event = Event(title=title, description=description, date=date)
        db.session.add(new_event)
        db.session.commit()
        flash("Event added!", "success")
        return redirect(url_for('home'))
    return render_template("add_event.html", user=user)

# --- Create Clan ---
@app.route("/create_clan", methods=["GET","POST"])
def create_clan():
    if 'user_id' not in session:
        flash("Login required!", "danger")
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    if request.method=="POST":
        name = request.form['name']
        slogan = request.form['slogan']
        logo_file = request.files.get('logo')
        logo_path = "/static/default-clan.png"
        if logo_file:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logo_file.save(logo_path)
            logo_path = f"/{logo_path.replace('\\','/')}"
        new_clan = Clan(name=name, slogan=slogan, logo=logo_path, leader_id=user.id)
        db.session.add(new_clan)
        db.session.commit()
        user.clan_id = new_clan.id
        db.session.commit()
        flash("Clan created successfully!", "success")
        return redirect(url_for('home', page="dashboard"))
    return render_template("create_clan.html", user=user)

# --- Join Clan ---
@app.route("/join_clan/<int:clan_id>")
def join_clan(clan_id):
    if 'user_id' not in session:
        flash("Login first!", "danger")
        return redirect(url_for('home'))
    user = User.query.get(session['user_id'])
    user.clan_id = clan_id
    db.session.commit()
    flash("Joined clan successfully!", "success")
    return redirect(url_for('home', page="dashboard"))

# --- Logout ---
@app.route("/logout")
def logout():
    session.pop('user_id', None)
    flash("Logged out!", "success")
    return redirect(url_for('home'))

# --- Run ---
if __name__=="__main__":
    app.run(debug=True)
