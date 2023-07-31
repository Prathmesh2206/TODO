from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user
from datetime import datetime


# Create a flask application
app = Flask(__name__)

# Tells flask-sqlalchemy what database to connect to
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
# Enter a secret key
app.config["SECRET_KEY"] = "todoapp"
# Initialize flask-sqlalchemy extension
db = SQLAlchemy()

# LoginManager is needed for our application
# to be able to log in and out users
login_manager = LoginManager()
login_manager.init_app(app)


departments = {
      0: "Administration",
      1: "Quality Assurance",
      2: "Network Security",
      3: "Remote Browser Isolation"
}

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    designation = db.Column(db.String(250), nullable=False)
    department = db.Column(db.Integer)
    tasks = db.relationship('Task', backref='users', lazy=True)

    def __repr__(self):
        return self.username

class Task(db.Model):
    task_no = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(120), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String, default="In-Progress", nullable=False)
    created_by = db.Column(db.Integer,nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'),nullable=False)

    def __repr__(self):
        return self.task

# Initialize app with extension
db.init_app(app)
# Create database within app context
 
with app.app_context():
    db.create_all()


# Creates a user loader callback that returns the user object given an id
@login_manager.user_loader
def loader_user(user_id):
    return Users.query.get(user_id)

@app.route('/register', methods=["GET", "POST"])
def register():
# If the user made a POST request, create a new user
	if request.method == "POST":
		user = Users(username=request.form.get("username"),password=request.form.get("password"), designation=request.form.get("designation"), department=request.form.get("department"))
		# Add the user to the database
		db.session.add(user)
		# Commit the changes made
		db.session.commit()
		# Once user account created, redirect them
		# to login route (created later on)
		return redirect(url_for("home"))
	# Renders sign_up template if user made a GET request
	return render_template("sign_up.html")

@app.route("/login", methods=["GET", "POST"])
def login():
	# If a post request was made, find the user by
	# filtering for the username
	if request.method == "POST":
		user = Users.query.filter_by(
			username=request.form.get("username")).first()
		# Check if the password entered is the
		# same as the user's password
		if user.password == request.form.get("password"):
			# Use the login_user method to log in the user
			login_user(user)
			return redirect(url_for("home"))
		# Redirect the user back to the home
		# (we'll create the home route in a moment)
	return render_template("login.html")

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/")
def home():
    if current_user.is_authenticated:
        if current_user.designation == 'Admin':
            users = Users.query.all()    
            return render_template("home.html", users=users, departments=departments)
        if current_user.designation == 'Manager':
            tasks = Task.query.filter_by(created_by=current_user.id)
            users=Users.query.all();
            assigned_users=[]
            for i in tasks:
                 for j in users:
                      if i.assigned_to==j.id:
                        assigned_users.append(j.username)
                        break;
            if request.args.get("view"):
                if request.args.get("view") == "in_progress":
                    tasks = list(Task.query.filter_by(status="In-Progress"))
                elif request.args.get("view") == "completed":
                    tasks = list(Task.query.filter_by(status="Complete"))
                else:
                    tasks = Task.query.all()
            return render_template("home.html", tasks=tasks,users=assigned_users)
        if current_user.designation == 'Employee':
            tasks = Task.query.filter_by(assigned_to=current_user.id)
            if request.args.get("view"):
                if request.args.get("view") == "in_progress":
                    tasks = list(Task.query.filter_by(status="In-Progress"))
                elif request.args.get("view") == "completed":
                    tasks = list(Task.query.filter_by(status="Complete"))
                else:
                    tasks = Task.query.all()
            return render_template("home.html",tasks=tasks)
    return render_template("home.html")
 
@app.route("/add", methods=["GET", "POST"])
def create_task():
    if current_user.designation=='Manager':
        users = Users.query.filter_by(department = 1) # GET ONLY USERS OF CURRENT USER KA DEPARTMENT, and not a manager
        # print(current_user)
        subordinates=list(Users.query.filter_by(department=current_user.department ))
        subordinates.remove(current_user)
        # print(subordinates)
        if request.method == "POST":
            task = Task(
                task=request.form["task"],
                due_date=datetime.fromisoformat(request.form["due_date"]),
                assigned_to=request.form["assign_to"],
                created_by=request.form["created_by"]
            )
            db.session.add(task)
            db.session.commit()
            return redirect("/")
        return render_template("add.html", users=users)


@app.route("/toggle_status/<int:no>")
def toggle_status(no):
    task = list(Task.query.filter_by(task_no=no))[0]
    task.status = "Complete" if task.status == "In-Progress" else "In-Progress"
    db.session.commit()
    return redirect("/")


@app.route("/edit/<int:no>", methods=["GET", "POST"])
def edit_task(no):
    if current_user.designation=='Manager':
        task = list(Task.query.filter_by(task_no=no))[0]
        if request.method == "POST":
            task.task = request.form["task"]
            task.due_date = datetime.fromisoformat(request.form["due_date"])
            db.session.commit()
            return redirect("/")
        return render_template("edit.html", task=task)
    else:
         return render_template("error.html")
    return render_template("home.html")


@app.route("/delete/<int:no>")
def delete_task(no):
    if current_user.designation=='Manager':
        task = list(Task.query.filter_by(task_no=no))[0]
        db.session.delete(task)
        db.session.commit()
    return redirect("/")

 
if __name__ == "__main__":
    app.run(debug=True)