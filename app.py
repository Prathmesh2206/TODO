from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Setting up database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todolist.sqlite3"
db = SQLAlchemy(app)


# Task Model
class Task(db.Model):
    task_no = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    due_date = db.Column(db.DateTime)
    status = db.Column(db.String, default="In-Progress", nullable=False)

    def __repr__(self):
        return self.task


@app.route("/")
def list_tasks():
    tasks = Task.query.all()
    if request.args.get("view"):
        if request.args.get("view") == "in_progress":
            tasks = list(Task.query.filter_by(status="In-Progress"))
        elif request.args.get("view") == "completed":
            tasks = list(Task.query.filter_by(status="Complete"))
        else:
            tasks = Task.query.all()
    return render_template("home.html", tasks=tasks)


@app.route("/add", methods=["GET", "POST"])
def create_task():
    if request.method == "POST":
        task = Task(
            task=request.form["task"],
            due_date=datetime.fromisoformat(request.form["due_date"]),
        )
        db.session.add(task)
        db.session.commit()
        return redirect("/")
    return render_template("add.html")


@app.route("/toggle_status/<int:no>")
def toggle_status(no):
    task = list(Task.query.filter_by(task_no=no))[0]
    task.status = "Complete" if task.status == "In-Progress" else "In-Progress"
    db.session.commit()
    return redirect("/")


@app.route("/edit/<int:no>", methods=["GET", "POST"])
def edit_task(no):
    task = list(Task.query.filter_by(task_no=no))[0]
    if request.method == "POST":
        task.task = request.form["task"]
        task.due_date = datetime.fromisoformat(request.form["due_date"])
        db.session.commit()
        return redirect("/")
    return render_template("edit.html", task=task)


@app.route("/delete/<int:no>")
def delete_task(no):
    task = list(Task.query.filter_by(task_no=no))[0]
    db.session.delete(task)
    db.session.commit()
    return redirect("/")


app.run(debug=True)
