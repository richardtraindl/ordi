
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import timedelta


app = Flask(__name__)

login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/richard/dev/flask/ordi/instance/ordi.sqlite3'
app.config['SECRET_KEY'] = 'esgibt nichtmehrvielzusagen'
app.config['PERMANENT_SESSION_LIFETIME'] =  timedelta(minutes=1440) # 24h

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from . import auth
app.register_blueprint(auth.bp)

from . import patient
app.register_blueprint(patient.bp)
app.add_url_rule('/', endpoint='index')

from . import rechnung
app.register_blueprint(rechnung.bp)

from . import behandlungsverlauf
app.register_blueprint(behandlungsverlauf.bp)

from . import abfragen
app.register_blueprint(abfragen.bp)

from . import kalender
app.register_blueprint(kalender.bp)
    
from . import admin
app.register_blueprint(admin.bp)

from .util.filters import mapanrede, mapgeschlecht, mapimpfung, mapartikel, fmtcurrency, fmtdate, supress_none, \
                          is_dict, calc_kw, add_days, add_hours, add_mins, gib_feiertag
app.jinja_env.filters['mapanrede'] = mapanrede
app.jinja_env.filters['mapgeschlecht'] = mapgeschlecht
app.jinja_env.filters['mapimpfung'] = mapimpfung
app.jinja_env.filters['mapartikel'] = mapartikel
app.jinja_env.filters['currency'] = fmtcurrency
app.jinja_env.filters['fmtdate'] = fmtdate
app.jinja_env.filters['sn'] = supress_none
app.jinja_env.filters['is_dict'] = is_dict
app.jinja_env.filters['calc_kw'] = calc_kw
app.jinja_env.filters['add_days'] = add_days
app.jinja_env.filters['add_hours'] = add_hours
app.jinja_env.filters['add_mins'] = add_mins
app.jinja_env.filters['feiertag'] = gib_feiertag
