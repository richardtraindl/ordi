
from datetime import datetime, date, timedelta

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, make_response
from werkzeug.exceptions import abort
from sqlalchemy import func, distinct, or_, and_
from flask_weasyprint import HTML, render_pdf
from flask_login import login_required
from app import app, db
from app.models import *
from .reqhelper import *
from .values import *
from .util.helper import *


bp = Blueprint('behandlungsverlauf', __name__, url_prefix='/behandlungsverlauf')


@bp.route('/index', methods=('GET', 'POST'))
@login_required
def index():
    if(request.method == 'POST'):
        try:
            jahr = int(request.form['jahr'])
        except:
            jahr = None
    else:
        jahr = datetime.today().year

    if(jahr):
        begin = str(jahr - 1) + "-12-31"
        end = str(jahr + 1) + "-01-01"
        behandlungsverlaeufe = db.session.query(Behandlungsverlauf, Person, Tier) \
            .join(Person, Behandlungsverlauf.person_id == Person.id) \
            .join(Tier, Behandlungsverlauf.tier_id == Tier.id).filter(Behandlungsverlauf.datum > begin, Behandlungsverlauf.datum < end).all()
    else:
        behandlungsverlaeufe = db.session.query(Behandlungsverlauf, Person, Tier) \
            .join(Person, Behandlungsverlauf.person_id == Person.id) \
            .join(Tier, Behandlungsverlauf.tier_id == Tier.id).all()

    if(jahr):
        str_jahr = str(jahr)
    else:
        str_jahr = ""

    return render_template("behandlungsverlauf/index.html", behandlungsverlaeufe=behandlungsverlaeufe, 
        jahr=str_jahr, page_title="Behandlungsverläufe")


@bp.route('/<int:id>/create', methods=('GET', 'POST'))
@login_required
def create(id):
    tierhaltung = db.session.query(Tierhaltung).get(id)

    datum = date.today().strftime("%d.%m.%Y")

    if(request.method == 'POST'):
        behandlungsverlauf, error = fill_and_validate_behandlungsverlauf(None, request)
        if(len(error) > 0):
            flash(error)
            return render_template('behandlungsverlauf/behandlungsverlauf.html', id=id, 
                person=tierhaltung.person, tier=tierhaltung.tier, 
                behandlungsverlauf=behandlungsverlauf, changed=True, 
                datum=datum, page_title="Behandlungsverlauf")

        behandlungsverlauf.person_id = tierhaltung.person.id
        behandlungsverlauf.tier_id = tierhaltung.tier.id
        db.session.add(behandlungsverlauf)
        db.session.commit()
        return redirect(url_for('behandlungsverlauf.edit', behandlungsverlauf_id=behandlungsverlauf.id))
    else:
        behandlungsverlauf = Behandlungsverlauf()
        return render_template('behandlungsverlauf/behandlungsverlauf.html', id=id, 
            person=tierhaltung.person, tier=tierhaltung.tier, 
            behandlungsverlauf=behandlungsverlauf, datum=datum, changed=False, 
            page_title="Behandlungsverlauf")


@bp.route('/<int:behandlungsverlauf_id>/edit', methods=('GET', 'POST'))
@login_required
def edit(behandlungsverlauf_id):
    behandlungsverlauf = db.session.query(Behandlungsverlauf).get(behandlungsverlauf_id)

    if(request.method == 'POST'):
        behandlungsverlauf, error = fill_and_validate_behandlungsverlauf(behandlungsverlauf, request)
        if(len(error) > 0):
            flash(error)
            return render_template('behandlungsverlauf/behandlungsverlauf.html', 
                behandlungsverlauf=behandlungsverlauf, changed=True, 
                page_title="Behandlungsverlauf")

        db.session.commit()

    return render_template('behandlungsverlauf/behandlungsverlauf.html', 
        behandlungsverlauf=behandlungsverlauf, changed=False, 
        page_title="Behandlungsverlauf")


@bp.route('/<int:behandlungsverlauf_id>/show', methods=('GET',))
@login_required
def show(behandlungsverlauf_id):
    behandlungsverlauf = db.session.query(Behandlungsverlauf).get(behandlungsverlauf_id)

    return render_template('behandlungsverlauf/mobile_behandlungsverlauf.html', 
        behandlungsverlauf=behandlungsverlauf, page_title="Behandlungsverlauf")


@bp.route('/<int:behandlungsverlauf_id>/download', methods=('GET',))
@login_required
def download(behandlungsverlauf_id):
    behandlungsverlauf = db.session.query(Behandlungsverlauf).get(behandlungsverlauf_id)

    html = render_template('behandlungsverlauf/print_behandlungsverlauf.html', bv=behandlungsverlauf)

    name = filter_bad_chars(behandlungsverlauf.person.familienname + \
                "_" + behandlungsverlauf.person.vorname)
    filename = str(behandlungsverlauf.id) + "_behandlungsverlauf_fuer_" + name + ".pdf"

    return render_pdf(HTML(string=html), stylesheets=None, download_filename=filename)


@bp.route('/<int:behandlungsverlauf_id>/delete', methods=('GET',))
@login_required
def delete(behandlungsverlauf_id):
    behandlungsverlauf = db.session.query(Behandlungsverlauf).get(behandlungsverlauf_id)

    db.session.delete(behandlungsverlauf)

    db.session.commit()

    return redirect(url_for('behandlungsverlauf.index'))

