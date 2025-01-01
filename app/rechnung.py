
from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for, make_response
from werkzeug.exceptions import abort
from sqlalchemy import func, distinct, or_, and_
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required
from app import app, db
from app.models import *
from .reqhelper import *
from .createpdf import *
from .values import *
from .util.helper import *


bp = Blueprint('rechnung', __name__, url_prefix='/rechnung')


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
        rechnungen = db.session.query(Rechnung, Person, Tier) \
            .join(Person, Rechnung.person_id == Person.id) \
            .join(Tier, Rechnung.tier_id == Tier.id).filter(Rechnung.jahr==jahr).all()
    else:
        rechnungen = db.session.query(Rechnung, Person, Tier) \
            .join(Person, Rechnung.person_id == Person.id) \
            .join(Tier, Rechnung.tier_id == Tier.id).all()
        
    if(jahr):
        str_jahr = str(jahr)
    else:
        str_jahr = ""
    return render_template("rechnung/index.html", rechnungen=rechnungen, jahr=str_jahr, page_title="Rechnungen")


def calc_and_fill_rechnung(rechnung, rechnungszeilen):
    rechnung.brutto_summe = 0
    rechnung.steuerbetrag_zwanzig = 0
    rechnung.steuerbetrag_dreizehn = 0
    rechnung.steuerbetrag_zehn = 0

    for rechnungszeile in rechnungszeilen:
        try:
            steuersatz = ARTIKEL_STEUER[rechnungszeile.artikelcode]
        except:
            return "Falsche Artikelart."
        try:
            betrag = float(round(rechnungszeile.betrag, 2))
        except:
            return "Betrag ist keine Zahl."

        rechnung.brutto_summe += betrag
        nettobetrag = round(float(betrag * 100) / float(100 + steuersatz))
        if(steuersatz == 20):
            rechnung.steuerbetrag_zwanzig += (betrag - nettobetrag)
        elif(steuersatz == 13):
            rechnung.steuerbetrag_dreizehn += (betrag - nettobetrag)
        else: # steuersatz == 10
            rechnung.steuerbetrag_zehn += (betrag - nettobetrag)

    rechnung.netto_summe = rechnung.brutto_summe - (rechnung.steuerbetrag_zwanzig + rechnung.steuerbetrag_dreizehn + rechnung.steuerbetrag_zehn)
    return ""


@bp.route('/<int:rechnung_id>/create_from_rechnung', methods=('GET', 'POST'))
@login_required
def create_from_rechnung(rechnung_id):
    rechnung = db.session.query(Rechnung).filter(Rechnung.id==rechnung_id).first()
    tierhaltung = db.session.query(Tierhaltung).filter(Tierhaltung.person_id==rechnung.person_id, Tierhaltung.tier_id==rechnung.tier_id).first()

    return redirect(url_for('rechnung.create', tierhaltung_id=tierhaltung.id))


@bp.route('/<int:tierhaltung_id>/create', methods=('GET', 'POST'))
@login_required
def create(tierhaltung_id):
    artikelwerte = []
    for key, value in ARTIKEL.items():
        artikelwerte.append([key, value])

    tierhaltung = db.session.query(Tierhaltung).get(tierhaltung_id)

    if(request.method == 'POST'):
        rechnung, error = fill_and_validate_rechnung(None, request)
        reqrechnungszeilen = build_rechnungszeilen(request)

        rechnungszeilen = []
        for reqrechnungszeile in reqrechnungszeilen:
            rechnungszeile, error = fill_and_validate_rechnungszeile(rechnung, None, reqrechnungszeile)
            if(len(error) > 0):
                flash(error)
                return render_template('rechnung/rechnung.html', tierhaltung_id=tierhaltung_id, rechnung=rechnung, rechnungszeilen=reqrechnungszeilen, person=tierhaltung.person, tier=tierhaltung.tier, artikelwerte=artikelwerte,  page_title="Rechnung")
            else:
                rechnungszeilen.append(rechnungszeile)

        error = calc_and_fill_rechnung(rechnung, rechnungszeilen)
        if(len(error) > 0):
            flash(error)
            db.session.rollback()
            return render_template('rechnung/rechnung.html', tierhaltung_id=tierhaltung_id, rechnung=rechnung, rechnungszeilen=reqrechnungszeilen, person=tierhaltung.person, tier=tierhaltung.tier, artikelwerte=artikelwerte, page_title="Rechnung")

        rechnung.person_id = tierhaltung.person.id
        rechnung.tier_id = tierhaltung.tier.id
        db.session.add(rechnung)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            error = str(e.__dict__['orig'])
            flash(error)
            return render_template('rechnung/rechnung.html', tierhaltung_id=tierhaltung_id, rechnung=rechnung, rechnungszeilen=reqrechnungszeilen, person=tierhaltung.person, tier=tierhaltung.tier, artikelwerte=artikelwerte, page_title="Rechnung")

        for rechnungszeile in rechnungszeilen:
            rechnungszeile.rechnung_id = rechnung.id
            db.session.add(rechnungszeile)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            error = str(e.__dict__['orig'])
            flash(error)
            return render_template('rechnung/rechnung.html', tierhaltung_id=tierhaltung_id, rechnung=rechnung, rechnungszeilen=reqrechnungszeilen, person=tierhaltung.person, tier=tierhaltung.tier, artikelwerte=artikelwerte, page_title="Rechnung")

        return redirect(url_for('rechnung.show', rechnung_id=rechnung.id))
    else:
        rechnung = Rechnung()
        datum = datetime.now().strftime("%d.%m.%Y")
        ort = "Wien"
        rechnungszeilen=[] #[Rechnungszeile(datum=datum)]

        return render_template('rechnung/rechnung.html', tierhaltung_id=tierhaltung_id, rechnung=rechnung, rechnungszeilen=rechnungszeilen, person=tierhaltung.person, tier=tierhaltung.tier, datum=datum, ort=ort, artikelwerte=artikelwerte, page_title="Rechnung")


@bp.route('/<int:rechnung_id>/save_rechnung', methods=('GET', 'POST'))
@login_required
def save_rechnung(rechnung_id):
    artikelwerte = []
    for key, value in ARTIKEL.items():
        artikelwerte.append([key, value])

    rechnung = db.session.query(Rechnung).get(rechnung_id)
    rechnungszeilen = db.session.query(Rechnungszeile).filter(Rechnungszeile.rechnung_id==rechnung.id).all()

    if(request.method == 'POST'):
        try:
            new = request.form['new']
            print("new")
            return redirect(url_for('rechnung.create'))
        except:
            pass

        rechnung, error = fill_and_validate_rechnung(rechnung, request)
        reqrechnungszeilen = build_rechnungszeilen(request)

        #####################
        # Rechnungszeilen aus Datenbank mit jenen des Requests mergen
        mergedzeilen = []
        for rechnungszeile in rechnungszeilen:
            found = False
            for reqrechnungszeile in reqrechnungszeilen:
                if(len(reqrechnungszeile['rechnungszeile_id']) > 0):
                    try:
                        rechnungszeile_id = int(reqrechnungszeile['rechnungszeile_id'])
                    except:
                        continue
                    if(rechnungszeile.id == rechnungszeile_id):
                        mergedzeilen.append(reqrechnungszeile)
                        found = True
                        break
            if(found == False):
                mergedzeilen.append(rechnungszeile)

        for reqrechnungszeile in reqrechnungszeilen:
            if(len(reqrechnungszeile['rechnungszeile_id']) == 0):
                mergedzeilen.append(reqrechnungszeile)
        #####################

        if(len(error) > 0):
            flash(error)
            return render_template('rechnung/rechnung.html', rechnung=rechnung, rechnungszeilen=reqrechnungszeilen, artikelwerte=artikelwerte, page_title="Rechnung")

        calczeilen = []
        for mergedzeile in mergedzeilen:
            if(type(mergedzeile) is dict):
                rechnungszeile, error = fill_and_validate_rechnungszeile(rechnung, None, mergedzeile)
                if(len(error) > 0):
                    db.session.rollback()
                    flash(error)
                    return render_template('rechnung/rechnung.html', rechnung=rechnung, rechnungszeilen=mergedzeilen, artikelwerte=artikelwerte, page_title="Rechnung")
                else:
                    if(rechnungszeile.id):
                        newrechnungszeile = db.session.query(Rechnungszeile).get(rechnungszeile.id)
                        if(newrechnungszeile):
                            if(mergedzeile['touched'] == "1"):
                                newrechnungszeile.datum=rechnungszeile.datum
                                newrechnungszeile.artikelcode=rechnungszeile.artikelcode
                                newrechnungszeile.artikel=rechnungszeile.artikel
                                newrechnungszeile.betrag=rechnungszeile.betrag
                                calczeilen.append(newrechnungszeile)
                    else:
                        db.session.add(rechnungszeile)
                        calczeilen.append(rechnungszeile)
            else:
                calczeilen.append(mergedzeile)

        error = calc_and_fill_rechnung(rechnung, calczeilen)
        if(len(error) > 0):
            db.session.rollback()
            flash(error)
            return render_template('rechnung/rechnung.html', rechnung=rechnung, rechnungszeilen=mergedzeilen, artikelwerte=artikelwerte, page_title="Rechnung")

        try:
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            error = str(e.__dict__['orig'])
            flash(error)
            return render_template('rechnung/rechnung.html', rechnung=rechnung, rechnungszeilen=mergedzeilen, artikelwerte=artikelwerte, page_title="Rechnung")

        rechnungszeilen = db.session.query(Rechnungszeile).filter(Rechnungszeile.rechnung_id==rechnung.id).all()

    return redirect(url_for('rechnung.show', rechnung_id=rechnung.id))


@bp.route('/<int:rechnung_id>/show', methods=('GET',))
@login_required
def show(rechnung_id):
    artikelwerte = []
    for key, value in ARTIKEL.items():
        artikelwerte.append([key, value])

    rechnung = db.session.query(Rechnung).get(rechnung_id)
    rechnungszeilen = db.session.query(Rechnungszeile).filter(Rechnungszeile.rechnung_id==rechnung.id).all()

    return render_template('rechnung/rechnung.html', rechnung=rechnung, 
        rechnungszeilen=rechnungszeilen, artikelwerte=artikelwerte, page_title="Rechnung")


@bp.route('/<int:rechnung_id>/download', methods=('GET', 'POST'))
@login_required
def download(rechnung_id):
    rechnung = db.session.query(Rechnung).get(rechnung_id)

    rechnungszeilen = db.session.query(Rechnungszeile).filter(Rechnungszeile.rechnung_id==rechnung_id).all()

    byte_string = create_rechnung_pdf(rechnung, rechnungszeilen)

    name = filter_bad_chars(rechnung.person.familienname + "_" + rechnung.person.vorname)
    filename = str(rechnung.id) + "_rechnung_fuer_" + name + ".pdf"

    response = make_response(byte_string)

    response.headers.set('Content-Disposition', 'attachment', filename=filename)

    response.headers.set('Content-Type', 'application/pdf')

    return response


@bp.route('/<int:rechnung_id>/delete', methods=('GET',))
@login_required
def delete(rechnung_id):
    rechnung = db.session.query(Rechnung).get(rechnung_id)
    db.session.delete(rechnung)
    db.session.commit()
    return redirect(url_for('rechnung.index'))


@bp.route('/<int:rechnungszeile_id>/delete_rechnungszeile', methods=('GET',))
@login_required
def delete_rechnungszeile(rechnungszeile_id):
    rechnungszeile = db.session.query(Rechnungszeile).get(rechnungszeile_id)
    db.session.delete(rechnungszeile)
    db.session.commit()
    return redirect(url_for('rechnung.edit', rechnung_id=rechnungszeile.rechnung_id))


@bp.route('/<int:rechnungszeile_id>/async_delete_rechnungszeile', methods=('GET',))
@login_required
def async_delete_rechnungszeile(rechnungszeile_id):
    rechnungszeile = db.session.query(Rechnungszeile).get(rechnungszeile_id)
    if(rechnungszeile):
        db.session.delete(rechnungszeile)
        db.session.commit()
        return "OK"
    return ""


@bp.route('/<int:rechnungszeile_id>/async_read_rechnungszeile', methods=('GET',))
@login_required
def async_read_rechnungszeile(rechnungszeile_id):
    rechnungszeile = db.session.query(Rechnungszeile).get(rechnungszeile_id)
    if(rechnungszeile):
        return { 'datum' : rechnungszeile.datum.strftime("%d.%m.%Y"),
                 'artikelcode' : str(rechnungszeile.artikelcode),
                 'artikel' : str(rechnungszeile.artikel),
                 'betrag' : str(rechnungszeile.betrag) }
    return {}

