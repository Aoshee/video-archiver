from flask import Flask, request, session, redirect, url_for, abort, render_template
from flask_bootstrap import Bootstrap

from flask.ext.wtf import Form
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired, URL

from flask.json import jsonify

from archiver import *

class AddForm(Form):
    url = StringField('Video URL?', validators=[InputRequired(), URL()])
    submit = SubmitField('Submit')


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY']='changeme'

Bootstrap(app)

downloaders = {}

@app.route('/')
def index():
    return render_template('index.html', downloaders=downloaders.values())

@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddForm(request.form)
    if request.method == 'POST' and form.validate():
        new_id = (max(downloaders) if len(downloaders) > 0 else 0) + 1
        downloaders[new_id] = Downloader(new_id, form.url.data)
        return redirect(url_for('detail', dl_id=new_id))
    return render_template('add.html', form=form)

@app.route('/detail/<int:dl_id>')
def detail(dl_id):
    if dl_id in downloaders:
        return render_template('detail.html', download=downloaders[dl_id])
    else:
        abort(404)

@app.route('/start/<int:dl_id>')
def start(dl_id):
    if dl_id in downloaders:
        downloaders[dl_id].start()
        return ''
    else:
        abort(404)

@app.route('/stop/<int:dl_id>')
def stop(dl_id):
    if dl_id in downloaders:
        downloaders[dl_id].stop()
        return ''
    else:
        abort(404)

@app.route('/log/<int:dl_id>')
def log(dl_id):
    if dl_id in downloaders:
        return downloaders[dl_id].get_log()
    else:
        abort(404)

@app.route('/stats/<int:dl_id>')
def stats(dl_id):
    if dl_id in downloaders:
        return jsonify(downloaders[dl_id].get_stats())
    else:
        abort(404)

if __name__ == '__main__':
    app.run()
