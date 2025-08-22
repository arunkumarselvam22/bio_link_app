from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Link
from forms import RegisterForm, LoginForm, LinkForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bio_link.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
@app.route('/')
def home():
    return render_template('home.html')
@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('profile', username=user.username))
        else:
            flash('Wrong email or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('home'))

@app.route('/user/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    links = Link.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', user=user, links=links)

@app.route('/manage_links', methods=['GET','POST'])
@login_required
def manage_links():
    form = LinkForm()
    if form.validate_on_submit():
        new_link = Link(name=form.name.data, url=form.url.data, user_id=current_user.id)
        db.session.add(new_link)
        db.session.commit()
        flash('Link added!', 'success')
        return redirect(url_for('manage_links'))

    links = Link.query.filter_by(user_id=current_user.id).all()
    return render_template('manage_links.html', form=form, links=links)

@app.route('/edit_link/<int:link_id>', methods=['GET','POST'])
@login_required
def edit_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id != current_user.id:
        flash("Unauthorized", "danger")
        return redirect(url_for('manage_links'))

    form = LinkForm(obj=link)
    if form.validate_on_submit():
        link.name = form.name.data
        link.url = form.url.data
        db.session.commit()
        flash('Link updated!', 'success')
        return redirect(url_for('manage_links'))

    return render_template('manage_links.html', form=form, links=[link], edit_mode=True)

@app.route('/delete_link/<int:link_id>')
@login_required
def delete_link(link_id):
    link = Link.query.get_or_404(link_id)
    if link.user_id != current_user.id:
        flash("Unauthorized", "danger")
    else:
        db.session.delete(link)
        db.session.commit()
        flash('Link deleted', 'info')
    return redirect(url_for('manage_links'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
