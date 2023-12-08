import datetime
from flask import Flask, render_template, flash, url_for, redirect
from flask_login import UserMixin, LoginManager, current_user, login_user, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy

# configuring flask app
app = Flask("__name__")
app.config['SECRET_KEY'] = 'asdfg78908765dfv3ge456h5esg4jk345678'
Bootstrap5(app)

# configuring sql database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///to_do_list.db'
db = SQLAlchemy()
db.init_app(app)

# config login
login_manager = LoginManager()
login_manager.init_app(app)


# database tables
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    to_do_list = db.relationship('ToDo', backref='user', lazy=True)


class ToDo(db.Model):
    __tablename__ = "To_do_list"
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


with app.app_context():
    db.create_all()


# login forms
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In!")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")


class ToDoForm(FlaskForm):
    to_do = StringField("To Do:", validators=[DataRequired()])
    submit = SubmitField("✙ Add")


@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/")
def home():
    form = ToDoForm()
    if current_user.is_authenticated:
        user_to_do_data = db.session.execute(db.select(ToDo).where(ToDo.user_id == current_user.id)).scalars().all()
    else:
        user_to_do_data = []
    return render_template("index.html", form=form, all_data=user_to_do_data, current_user=current_user)


@login_required
@app.route("/Add", methods=["POST"])
def add_task():
    form = ToDoForm()
    if form.validate_on_submit():
        task = form.to_do.data
        if task:
            date_obj = datetime.date.today()
            task_to_add = ToDo(task=task, date=date_obj, user_id=current_user.id)
            db.session.add(task_to_add)
            db.session.commit()
            return redirect(url_for("home"))
    return redirect(url_for('home'))


@login_required
@app.route("/strike/<int:task_id>")
def strike(task_id):
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    done_task = db.get_or_404(ToDo, task_id)
    done_task.task = f"<strike>{done_task.task}</strike>"
    db.session.commit()
    return redirect(url_for("home"))


@login_required
@app.route("/delete/<int:task_id>")
def delete_task(task_id):
    if not current_user.is_authenticated:
        return redirect(url_for("login"))
    task_to_delete = db.get_or_404(ToDo, task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()

        if not user:
            flash("This Email isn't registered. Please try again.")
            return redirect(url_for("login"))
        elif user.password != password:
            flash("Incorrect password. Please Try again")
            return redirect(url_for("login"))
        else:
            login_user(user)
            return redirect(url_for("home"))

    return render_template("login.html", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        user = db.session.execute(db.select(User).where(User.email == form.email.data)).scalar()
        if user:
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        user_to_add = User(name=form.name.data,
                           email=form.email.data,
                           password=form.password.data)

        db.session.add(user_to_add)
        db.session.commit()
        login_user(user_to_add)
        return redirect(url_for("home"))

    return render_template("register.html", form=form, current_user=current_user)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
