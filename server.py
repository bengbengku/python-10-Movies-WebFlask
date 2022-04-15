from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from typing import Callable
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired
from dotenv import load_dotenv, find_dotenv
import os
import requests

load_dotenv(find_dotenv())

API_KEY = os.getenv("API")
APP_KEY = os.getenv("SEC_KEY_CONFIG")
DB = os.getenv("DB")

class MySQLAlchemy(SQLAlchemy):
    Column: Callable
    String: Callable
    Integer: Callable
    Float: Callable

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = APP_KEY
Bootstrap(app)

db = MySQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(280), nullable=False)


    def __repr__(self):
        return f'<Movie {self.title}>'

db.create_all()

class EditForm(FlaskForm):
    rating = FloatField("Your Rating Out of 10 e.g. 7.5", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")

class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")



@app.route("/")
def home():
    all_movies_data = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies_data)):
        all_movies_data[i].ranking = len(all_movies_data) - i
    db.session.commit()
    return render_template("index.html", items=all_movies_data)


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        params = {
            "api_key": API_KEY,
            "query": movie_title
        }

        res = requests.get("https://api.themoviedb.org/3/search/movie", params=params)
        data = res.json()["results"]
        return render_template('select.html', options=data)


    return render_template('add.html', form=form)


@app.route('/find')
def find_movie():
    movie_id = request.args.get("id")
    MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
    if movie_id:
        movie_url_find = f"https://api.themoviedb.org/3/movie/{movie_id}"
        res = requests.get(movie_url_find, params={"api_key": API_KEY, "language": "en-US"})
        data = res.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id=new_movie.id))



@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()

    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)

    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template('edit.html', movie=movie, form=form)

@app.route('/delete', methods=["GET", "POST"])
def delete():
    movie_id = request.args.get('id')
    movie_del = Movie.query.get(movie_id)
    db.session.delete(movie_del)
    db.session.commit()
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)