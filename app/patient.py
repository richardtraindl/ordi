
from datetime import datetime, timedelta

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, send_file
from werkzeug.exceptions import abort
from sqlalchemy import func, distinct, or_, and_
from flask_weasyprint import HTML, render_pdf
from flask_login import login_required
from app import app, db
from app.models import *
from .values import *
from .util.reqhelper import *
from .util.helper import *


bp = Blueprint('patient', __name__, url_prefix='/patient')


#tierhaltung
@app.route('/', methods=('GET', 'POST'))
@bp.route('/', methods=('GET', 'POST'))
@bp.route('/index', methods=('GET', 'POST'))
@login_required
def index():
    if(request.method == 'POST'):
        familienname = request.form['familienname']
        session['familienname'] = familienname

        tiername = request.form['tiername']
        session['tiername'] = tiername

        if(request.form.get('kunde')):
            kunde = True
            session['kunde'] = 1
        else:
            kunde = False
            session['kunde'] = 0

        if(request.form.get('patient')):
            patient = True
            session['patient'] = 1
        else:
            patient = False
            session['patient'] = 0
    else:
        familienname = session.get('familienname')
        if(familienname is None):
            familienname = ""

        tiername = session.get('tiername')
        if(tiername is None):
            tiername = ""

        kunde = session.get('kunde')
        if(kunde is None or kunde == 1):
            kunde = True
        else:
            kunde = False

        patient = session.get('patient')
        if(patient is None or patient == 1):
            patient = True
        else:
            patient = False

    tierhaltungen = db.session.query(Tierhaltung, Person, Tier) \
        .join(Tierhaltung.person) \
        .join(Tierhaltung.tier) \
        .filter(func.lower(Person.familienname).like(func.lower(familienname) + "%"), func.lower(Tier.tiername).like(func.lower(tiername) + "%"), Person.kunde==kunde, Tier.patient==patient).order_by(Person.familienname.asc(), Tier.tiername.asc()).all() # .limit(500)

    return render_template("patient/index.html", tierhaltungen=tierhaltungen, 
        familienname=familienname, tiername=tiername, kunde=kunde, patient=patient, page_title="Karteikarten")


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    anredewerte = []
    for key, value in ANREDE.items():
        anredewerte.append([key, value])

    geschlechtswerte = []
    for key, value in GESCHLECHT.items():
        geschlechtswerte.append([key, value])

    if(request.method == 'POST'):
        person, error = fill_and_validate_person(None, request)
        if(error):
            flash(error[1])
            tier = Tier()
            return render_template('patient/create.html', person=person, tier=tier, anredewerte=anredewerte, geschlechtswerte=geschlechtswerte, error=error, page_title="Neue Karteikarte")

        tier, error = fill_and_validate_tier(None, request)
        if(error):
            flash(error[1])
            return render_template('patient/create.html', person=person, tier=tier, anredewerte=anredewerte, 
                geschlechtswerte=geschlechtswerte, error=error, page_title="Neue Karteikarte")

        db.session.add(person)
        db.session.add(tier)
        db.session.commit()

        tierhaltung = Tierhaltung(person_id = person.id, tier_id = tier.id)
        db.session.add(tierhaltung)
        db.session.commit()
        return redirect(url_for('patient.show', tierhaltung_id=tierhaltung.id))
    else:
        person = Person()
        tier = Tier()
        return render_template('patient/create.html', person=person, 
            tier=tier, anredewerte=anredewerte, geschlechtswerte=geschlechtswerte, ref=request.referrer, page_title="Neue Karteikarte")


@bp.route('/<int:tierhaltung_id>/show', methods=('GET',))
@login_required
def show(tierhaltung_id):
    anredewerte = []
    for key, value in ANREDE.items():
        anredewerte.append([key, value])

    geschlechtswerte = []
    for key, value in GESCHLECHT.items():
        geschlechtswerte.append([key, value])

    laborreferenzen = []
    for referenz in LABOR_REFERENZ:
        laborreferenzen.append(referenz)

    impfungswerte = []
    for key, value in IMPFUNG.items():
        impfungswerte.append([key, value])

    tierhaltung = Tierhaltung.query.get(tierhaltung_id)
    behandlungen = db.session.query(Behandlung) \
        .filter(Behandlung.tier_id == tierhaltung.tier.id) \
        .order_by(Behandlung.datum.asc()).all()

    datum = datetime.today()
    datum_ende = datum + timedelta(days=7)

    return render_template("patient/tierhaltung.html", tierhaltung=tierhaltung, behandlungen=behandlungen, datum=datum.strftime("%d.%m.%Y"), anredewerte=anredewerte, geschlechtswerte=geschlechtswerte, laborreferenzen=laborreferenzen, impfungswerte=impfungswerte, page_title="Karteikarte")


@bp.route('/<int:tierhaltung_id>/delete', methods=('GET',))
@login_required
def delete(tierhaltung_id):
    tierhaltung = Tierhaltung.query.get(tierhaltung_id)
    if(tierhaltung):
        if(db.session.query(Tierhaltung).filter(Tierhaltung.person_id == tierhaltung.person_id).count() == 1):
            person = db.session.query(Person).get(tierhaltung.person_id)
        else:
            person = None

        if(db.session.query(Tierhaltung).filter(Tierhaltung.tier_id == tierhaltung.tier_id).count() == 1):
            tier = db.session.query(Tier).get(tierhaltung.tier_id)
        else:
            tier = None

        db.session.delete(tierhaltung)
        db.session.commit()

        if(person):
            db.session.delete(person)
            db.session.commit()

        if(tier):
            db.session.delete(tier)
            db.session.commit()

    return redirect(url_for('patient.index'))
# tierhaltung


# tier
@bp.route('/<int:tierhaltung_id>/create_tier', methods=('GET', 'POST'))
@login_required
def create_tier(tierhaltung_id):
    geschlechtswerte = []
    for key, value in GESCHLECHT.items():
        geschlechtswerte.append([key, value])

    if(request.method == 'POST'):
        tier, error = fill_and_validate_tier(None, request)
        if(error):
            flash(error[1])
            return render_template('patient/create_tier.html', tier=None, 
                geschlechtswerte=geschlechtswerte, error=error, page_title="Neues Tier")

        db.session.add(tier)
        db.session.commit()

        tierhaltung = Tierhaltung.query.get(tierhaltung_id)
        new_tierhaltung = Tierhaltung(person_id=tierhaltung.person_id, tier_id = tier.id)
        db.session.add(new_tierhaltung)
        db.session.commit()
        return redirect(url_for('patient.show', tierhaltung_id=new_tierhaltung.id))
    else:
        tierhaltung = Tierhaltung.query.get(tierhaltung_id)
        person = tierhaltung.person
        tier = Tier()
        return render_template('patient/create_tier.html', person=person, tier=tier, geschlechtswerte=geschlechtswerte, page_title="Neues Tier")


@bp.route('/<int:tierhaltung_id>/<int:tier_id>/edit_tier', methods=('GET', 'POST'))
@login_required
def edit_tier(tierhaltung_id, tier_id):
    geschlechtswerte = []
    for key, value in GESCHLECHT.items():
        geschlechtswerte.append([key, value])

    if(request.method == 'POST'):
        tier = Tier.query.get(tier_id)
        tier, error = fill_and_validate_tier(tier, request)
        if(error):
            flash(error[1])
            return render_template('patient/edit_tier.html', id=id, tier=tier, 
                geschlechtswerte=geschlechtswerte, error=error, page_title="Tier ändern")
        else:
            db.session.commit()

    tier = Tier.query.get(tier_id)

    return render_template('patient/edit_tier.html', tierhaltung_id=tierhaltung_id, tier=tier, geschlechtswerte=geschlechtswerte, page_title="Tier ändern")
# tier


# person
@bp.route('/<int:tierhaltung_id>/<int:person_id>/edit_person', methods=('GET', 'POST'))
@login_required
def edit_person(tierhaltung_id, person_id):
    anredewerte = []
    for key, value in ANREDE.items():
        anredewerte.append([key, value])

    if(request.method == 'POST'):
        person = Person.query.get(person_id)
        person, error = fill_and_validate_person(person, request)
        if(error):
            flash(error[1])
            return render_template('patient/edit_person.html', tierhaltung_id=tierhaltung_id, person=person, 
                anredewerte=anredewerte, error=error, page_title="Person ändern")
        else:
            db.session.commit()

    person = db.session.query(Person).get(person_id)

    return render_template('patient/edit_person.html', tierhaltung_id=tierhaltung_id, person=person, anredewerte=anredewerte, page_title="Person ändern")
# person


# behandlung
def save_or_delete_impfungen(behandlung, impfungstexte):
    for impfungstext in impfungstexte:
        try:
            impfungscode = IMPFUNG[impfungstext]
        except:
            print("severe error")
            cursor.close()
            return False

        found = False
        for impfung in behandlung.impfungen:
            if(impfungscode == impfung.impfungscode):
                found = True
                break

        if(found == False):
            new_impfung = Impfung(behandlung_id=behandlung.id, impfungscode=impfungscode)
            db.session.add(new_impfung)
    db.session.commit()

    for impfung in behandlung.impfungen:
        found = False
        for impfungstext in impfungstexte:
            impfungscode = IMPFUNG[impfungstext]
            if(impfungscode == impfung.impfungscode):
                found = True
                break
        if(found == False):
            db.session.delete(impfung)
    db.session.commit()

    return True


@bp.route('/<int:tierhaltung_id>/save_behandlungen', methods=('GET', 'POST'))
@login_required
def save_behandlungen(tierhaltung_id):
    anredewerte = []
    for key, value in ANREDE.items():
        anredewerte.append([key, value])

    geschlechtswerte = []
    for key, value in GESCHLECHT.items():
        geschlechtswerte.append([key, value])

    laborreferenzen = []
    for referenz in LABOR_REFERENZ:
        laborreferenzen.append(referenz)

    impfungswerte = []
    for key, value in IMPFUNG.items():
        impfungswerte.append([key, value])

    if(request.method == 'POST'):
        tierhaltung = Tierhaltung.query.get(tierhaltung_id)
        if(not tierhaltung):
            flash("Tierhaltung nicht (mehr) vorhanden!")
            return redirect(url_for('patient.index'))

        datum=datetime.today()

        errorbehandlungen = []
        error = None

        reqbehandlungen = build_behandlungen(request)
        for idx, reqbehandlung in enumerate(reqbehandlungen):
            behandlung, str_impfungen, newerror = fill_and_validate_behandlung(reqbehandlung)
            if(newerror):
                errorbehandlungen.append(reqbehandlung)
                if(not error):
                    error = [None, newerror[0], newerror[1]]
            else:
                if(behandlung.id == None):
                    behandlung.tier_id = tierhaltung.tier_id
                    db.session.add(behandlung)
                    db.session.commit()

                    if(len(str_impfungen.strip()) > 0):
                        impfungstexte = str_impfungen.strip().split(',')
                    else:
                        impfungstexte = []
                    save_or_delete_impfungen(behandlung, impfungstexte)
                else:
                    dbbehandlung = db.session.query(Behandlung).get(behandlung.id)
                    dbbehandlung.datum=behandlung.datum
                    dbbehandlung.gewicht=behandlung.gewicht
                    dbbehandlung.diagnose=behandlung.diagnose
                    dbbehandlung.laborwerte1=behandlung.laborwerte1 
                    dbbehandlung.laborwerte2=behandlung.laborwerte2
                    dbbehandlung.arzneien=behandlung.arzneien
                    dbbehandlung.arzneimittel=behandlung.arzneimittel
                    db.session.commit()

                    if(len(str_impfungen.strip()) > 0):
                        impfungstexte = str_impfungen.strip().split(',')
                    else:
                        impfungstexte = []
                    save_or_delete_impfungen(dbbehandlung, impfungstexte)

        # Neu lesen nach Speichern
        behandlungen = db.session.query(Behandlung) \
                        .filter(Behandlung.tier_id == tierhaltung.tier.id) \
                        .order_by(Behandlung.datum.asc()).all()

        # Bestehende Datensätze mit fehlerhaften Request Datensätzen ergänzen (austauschen oder aufnehmen)
        for errorbehandlung in errorbehandlungen:
            if(len(errorbehandlung['behandlung_id']) > 0):
                try:
                    behandlung_id = int(errorbehandlung['behandlung_id'])
                except:
                    continue
                
                for idx in range(len(behandlungen)):
                    if(not isinstance(behandlungen[idx], dict)):
                        if(behandlungen[idx].id == behandlung_id):
                            behandlungen[idx] = errorbehandlung
                            if(error and error[0] is None):
                                error = [idx, error[1], error[2]]
            else:
                behandlungen.append(errorbehandlung)
                if(error and error[0] is None):
                    error = [(len(behandlungen) - 1), error[1], error[2]]

        if(error):
            flash(error[2])

            return render_template('patient/tierhaltung.html', tierhaltung=tierhaltung, behandlungen=behandlungen, 
                      datum=datum.strftime("%d.%m.%Y"), anredewerte=anredewerte, geschlechtswerte=geschlechtswerte,
                      laborreferenzen=laborreferenzen, impfungswerte=impfungswerte, error=error, page_title="Karteikarte")

    return redirect(url_for('patient.show', tierhaltung_id=tierhaltung_id))


@bp.route('/<int:behandlung_id>/delete_behandlung', methods=('GET',))
@login_required
def delete_behandlung(behandlung_id):
    behandlung = Behandlung.query.get(behandlung_id)
    if(behandlung):
        tierhaltung = db.session.query(Tierhaltung) \
            .filter(Tierhaltung.tier_id==behandlung.tier_id).first()
        db.session.delete(behandlung)
        db.session.commit()
        return redirect(url_for('patient.show', tierhaltung_id=tierhaltung.id))
    else:
        flash("Fehler beim Löschen der Behandlung: " + str(behandlung_id))
        return redirect(url_for('patient.index'))


@bp.route('/<int:behandlung_id>/async_delete_behandlung', methods=('GET',))
@login_required
def async_delete_behandlung(behandlung_id):
    behandlung = Behandlung.query.get(behandlung_id)
    if(behandlung):
        db.session.delete(behandlung)
        db.session.commit()
        return "OK"
    return ""


@bp.route('/<int:behandlung_id>/async_read_behandlung', methods=('GET',))
@login_required
def async_read_behandlung(behandlung_id):
    behandlung = Behandlung.query.get(behandlung_id)
    if(behandlung):
        str_impfungen = ""
        for impfung in behandlung.impfungen:
            if(len(str_impfungen) > 0):
                str_impfungen += ","
            str_impfungen += reverse_lookup(IMPFUNG, impfung.impfungscode)

        return { 'datum' : behandlung.datum.strftime("%d.%m.%Y"),
                 'gewicht' : behandlung.gewicht,
                 'diagnose' : behandlung.diagnose,
                 'laborwerte1' : behandlung.laborwerte1,
                 'laborwerte2' : behandlung.laborwerte2,
                 'arzneien' : behandlung.arzneien,
                 'arzneimittel' : behandlung.arzneimittel,
                 'impfungen' : str_impfungen }
    return {}
# behandlung


@bp.route('/<int:tierhaltung_id>/download', methods=('GET', 'POST'))
@login_required
def download(tierhaltung_id):
    tierhaltung = Tierhaltung.query.get(tierhaltung_id)

    behandlungen = db.session.query(Behandlung) \
        .filter(Behandlung.tier_id == tierhaltung.tier.id) \
        .order_by(Behandlung.datum.asc()).all()
    
    html = render_template('patient/print_tierhaltung.html', tierhaltung=tierhaltung, behandlungen=behandlungen)

    name = filter_bad_chars(tierhaltung.person.familienname + "_" + tierhaltung.person.vorname)
    filename = str(tierhaltung.id) + "_karteikarte_fuer_" + name + ".pdf"

    return render_pdf(HTML(string=html), stylesheets=None, download_filename=filename)

