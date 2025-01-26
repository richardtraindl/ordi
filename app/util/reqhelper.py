
from datetime import datetime

from flask import request
from ..values import *
from ..models import *


def fill_and_validate_tier(tier, request):
    error = ""

    try:
        geschlechtscode = int(request.form['geschlechtscode'])
    except:
        geschlechtscode = GESCHLECHT['']

    if(len(request.form['geburtsdatum']) > 10):
        str_geburtsdatum = request.form['geburtsdatum'].split()[0]
    else:
        str_geburtsdatum = request.form['geburtsdatum']
    try:
        geburtsdatum = datetime.strptime(str_geburtsdatum, "%d.%m.%Y").date()
    except:
        geburtsdatum = None
        error = "Falsches Geburtsdatum. "

    if(request.form.get('patient')):
        patient = True
    else:
        patient = False

    if(tier == None):
        tier = Tier()
    tier.tiername=request.form['tiername']
    tier.tierart=request.form['tierart']
    tier.rasse=request.form['rasse']
    tier.farbe=request.form['farbe']
    tier.viren=request.form['viren']
    tier.merkmal=request.form['merkmal']
    tier.geburtsdatum=geburtsdatum
    tier.geschlechtscode=geschlechtscode
    tier.chip_nummer=request.form['chip_nummer']
    tier.eu_passnummer=request.form['eu_passnummer']
    tier.patient=patient

    if(len(tier.tiername) == 0):
        error += "Tiername fehlt. "
    if(len(tier.tierart) == 0):
        error += "Tierart fehlt. "
    return tier, error


def fill_and_validate_person(person, request):
    error = ""

    try:
        person_id = int(request.form['person_id'])
    except:
        person_id = None

    try:
        anredecode = int(request.form['anredecode'])
    except:
        anredecode = ANREDE['']

    if(request.form.get('kunde')):
        kunde = True
    else:
        kunde = False

    if(person == None):
        person = Person()
    person.anredecode=anredecode
    person.titel=request.form['titel']
    person.familienname=request.form['familienname']
    person.vorname=request.form['vorname']
    person.notiz=request.form['notiz']
    person.kunde=kunde
    person.adr_strasse=request.form['adr_strasse']
    person.adr_plz=request.form['adr_plz']
    person.adr_ort=request.form['adr_ort']
    person.kontakte=request.form['kontakte']

    if(len(person.familienname) == 0):
        error += "Familienname fehlt. "
    return person, error


def build_behandlungen(request):    
    data = (
        request.form.getlist('behandlung_id[]'),
        request.form.getlist('tier_id[]'),
        request.form.getlist('datum[]'),
        request.form.getlist('gewicht[]'),
        request.form.getlist('diagnose[]'),
        request.form.getlist('laborwerte1[]'),
        request.form.getlist('laborwerte2[]'),
        request.form.getlist('arzneien[]'),
        request.form.getlist('arzneimittel[]'),
        request.form.getlist('impfungen[]')
    )

    reqbehandlungen = []
    for idx in range(len(data[0])):
        reqbehandlung = {}
        reqbehandlung['behandlung_id'] = data[0][idx]
        reqbehandlung['tier_id'] = data[1][idx]
        reqbehandlung['datum'] = data[2][idx]
        reqbehandlung['gewicht'] = data[3][idx]
        reqbehandlung['diagnose'] = data[4][idx]
        reqbehandlung['laborwerte1'] = data[5][idx]
        reqbehandlung['laborwerte2'] = data[6][idx]
        reqbehandlung['arzneien'] = data[7][idx]
        reqbehandlung['arzneimittel'] = data[8][idx]
        reqbehandlung['impfungen'] = data[9][idx]

        if(len(reqbehandlung['gewicht']) == 0 and
           len(reqbehandlung['diagnose']) == 0 and
           len(reqbehandlung['laborwerte1']) == 0 and
           len(reqbehandlung['laborwerte2']) == 0 and
           len(reqbehandlung['arzneien']) == 0 and
           len(reqbehandlung['arzneimittel']) == 0 and
           len(reqbehandlung['impfungen']) == 0):
            continue

        reqbehandlungen.append(reqbehandlung)
    return reqbehandlungen


def fill_and_validate_behandlung(reqbehandlung):
    error = ""

    behandlung = Behandlung()

    if(len(reqbehandlung['behandlung_id']) > 0):
        try:
            behandlung.id = int(reqbehandlung['behandlung_id'])
        except:
            behandlung.id = None

    if(len(reqbehandlung['tier_id']) > 0):
        try:
            behandlung.tier_id = int(reqbehandlung['tier_id'])
        except:
            behandlung.tier_id = None

    if(len(reqbehandlung['datum']) >= 10):
        str_datum = reqbehandlung['datum'].split()[0]
        try:
            behandlung.datum = datetime.strptime(str_datum, "%d.%m.%Y")
        except:
            behandlung.datum = None
            error += "Falsches Behandlungsdatum. "
    else:
        behandlung.datum = None
        error += "Falsches Behandlungsdatum. "

    behandlung.gewicht=reqbehandlung['gewicht']
    behandlung.diagnose=reqbehandlung['diagnose']
    behandlung.laborwerte1=reqbehandlung['laborwerte1'] 
    behandlung.laborwerte2=reqbehandlung['laborwerte2']
    behandlung.arzneien=reqbehandlung['arzneien']
    behandlung.arzneimittel=reqbehandlung['arzneimittel']

    return behandlung, reqbehandlung['impfungen'], error


def fill_and_validate_rechnung(rechnung, request):
    error = ""

    try:
        jahr = int(request.form['jahr'])
    except:
        jahr = None
        error += "Jahr fehlt oder ungültig. "

    try:
        lfnr = int(request.form['lfnr'])
    except:
        lfnr = None
        error += "Laufnummer fehlt oder ungültig. "

    if(len(request.form['datum']) > 10):
        str_datum = request.form['datum'].split()[0]
    else:
        str_datum = request.form['datum']
    try:
        datum = datetime.strptime(str_datum, "%d.%m.%Y")
    except:
        datum = None
        error += "Falsches Ausstellungsdatum. "

    if(rechnung == None):
        rechnung = Rechnung()

    rechnung.jahr=jahr
    rechnung.lfnr=lfnr
    rechnung.datum=datum
    rechnung.ort=request.form['ort']
    rechnung.diagnose=request.form['diagnose']
    rechnung.bezahlung=request.form['bezahlung']
    rechnung.brutto_summe=0
    rechnung.netto_summe=0
    rechnung.steuerbetrag_zwanzig=0
    rechnung.steuerbetrag_dreizehn=0
    rechnung.steuerbetrag_zehn=0

    return rechnung, error


def build_rechnungszeilen(request):
    data = (
        request.form.getlist('rechnung_id[]'),
        request.form.getlist('rechnungszeile_id[]'),
        request.form.getlist('datum[]'),
        request.form.getlist('artikelcode[]'),
        request.form.getlist('artikel[]'),
        request.form.getlist('betrag[]')
    )
    reqrechnungszeilen = []
    for idx in range(len(data[0])):
        reqrechnungszeile = {}
        reqrechnungszeile['rechnung_id'] = data[0][idx]
        reqrechnungszeile['rechnungszeile_id'] = data[1][idx]
        reqrechnungszeile['datum'] = data[2][idx]
        reqrechnungszeile['artikelcode'] = data[3][idx]
        reqrechnungszeile['artikel'] = data[4][idx]
        reqrechnungszeile['betrag'] = data[5][idx]

        if(len(reqrechnungszeile['rechnungszeile_id']) == 0 and 
           reqrechnungszeile['artikelcode'] == "0" and
           len(reqrechnungszeile['artikel']) == 0 and 
           len(reqrechnungszeile['betrag']) == 0):
            continue

        reqrechnungszeilen.append(reqrechnungszeile)
    return reqrechnungszeilen


def fill_and_validate_rechnungszeile(rechnung, reqrechnungszeile):
    error = ""

    rechnungszeile = Rechnungszeile()

    try:
        rechnungszeile.rechnung_id = int(reqrechnungszeile['rechnung_id'])
    except:
        rechnungszeile.rechnung_id = None

    try:
        rechnungszeile.id = int(reqrechnungszeile['rechnungszeile_id'])
    except:
        rechnungszeile.id = None

    if(rechnung and rechnung.id):
        rechnungszeile.rechnung_id=rechnung.id

    if(len(reqrechnungszeile['datum']) >= 10):
        str_datum = reqrechnungszeile['datum'].split()[0]
        try:
            rechnungszeile.datum = datetime.strptime(str_datum, "%d.%m.%Y")
        except:
            rechnungszeile.datum = None
            error += "Falsches Rechnungszeilendatum. "
    else:
        rechnungszeile.datum = None
        error += "Falsches Rechnungszeilendatum. "

    try:
        rechnungszeile.artikelcode = int(reqrechnungszeile['artikelcode'])
        try:
            steuersatz = ARTIKEL_STEUER[rechnungszeile.artikelcode]
        except:
            rechnungszeile.artikelcode=None
            error += "Falsche Artikelart. "
    except:
        rechnungszeile.artikelcode = None
        error += "Falsche Artikelart. "

    if(len(reqrechnungszeile['artikel']) > 0):
        rechnungszeile.artikel=reqrechnungszeile['artikel']
    else:
        rechnungszeile.artikel = None
        error += "Artikeldetail fehlt. "

    if(len(reqrechnungszeile['betrag']) == 0):
        betrag = None
        error += "Betrag fehlt. "
    else:
        try:
            betrag = float(reqrechnungszeile['betrag'].replace(",", "."))
            rechnungszeile.betrag=round(betrag, 2)
        except:
            rechnungszeile.betrag = None
            error += "Betrag muss eine Zahl sein. "

    return rechnungszeile, error


def fill_and_validate_behandlungsverlauf(behandlungsverlauf, request):
    error = ""

    if(len(request.form['datum']) > 10):
        str_datum = request.form['datum'].split()[0]
    else:
        str_datum = request.form['datum']
    try:
        datum = datetime.strptime(str_datum, "%d.%m.%Y")
    except:
        datum = None
        error += "Falsches Datum. "

    if(behandlungsverlauf == None):
        behandlungsverlauf = Behandlungsverlauf()

    behandlungsverlauf.datum=datum
    behandlungsverlauf.diagnose=request.form['diagnose']
    behandlungsverlauf.behandlung=request.form['behandlung']

    return behandlungsverlauf, error

