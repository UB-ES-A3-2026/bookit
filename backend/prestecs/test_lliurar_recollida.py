"""Tests del lliurament d'una comanda de recollida a la biblioteca (US7-T8).

`POST /api/prestecs/biblioteca/comandes/<id>/recollida/`: la biblioteca marca com a
lliurada una comanda de recollida preparada quan l'usuari la ve a buscar.
"""

import threading

import pytest
from django.db import connection
from rest_framework.test import APIClient

from cataleg.models import ExemplarBiblioteca, Llibre
from prestecs.models import Comanda, LiniaComanda, Prestec
from prestecs.serveis import TransicioNoPermesa, canvia_estat, text_notificacio
from usuaris.models import Biblioteca, PerfilRepartidor, Usuari

Estat = Comanda.Estat
Tipus = Comanda.TipusLliurament
ES_A_DOMICILI = "Aquesta comanda és a domicili: la lliura el repartidor."


def url(comanda_id):
    return f"/api/prestecs/biblioteca/comandes/{comanda_id}/recollida/"


def crea_usuari(correu, rol=Usuari.Role.USUARI):
    return Usuari.objects.create_user(
        correu,
        "Llibres-de-tardor-24",
        {"name": correu.split("@")[0], "address": "C/ Major 1", "library_card_number": correu, "role": rol},
    )


def crea_biblioteca(correu, nom):
    usuari = crea_usuari(correu, Usuari.Role.BIBLIOTECA)
    Biblioteca.objects.create(usuari=usuari, nom=nom)
    usuari.is_active = True
    usuari.save(update_fields=["is_active"])
    return usuari


def client_de(usuari):
    client = APIClient()
    client.force_authenticate(usuari)
    return client


@pytest.fixture
def biblioteca():
    return crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")


@pytest.fixture
def lector():
    return crea_usuari("lector@example.com")


@pytest.fixture
def llibres(biblioteca):
    llibres = [
        Llibre.objects.create(titol="Solitud", autor="Víctor Català", isbn="9788475882574"),
        Llibre.objects.create(titol="La plaça del Diamant", autor="Mercè Rodoreda", isbn="9788429740011"),
    ]
    for llibre in llibres:
        ExemplarBiblioteca.objects.create(llibre=llibre, biblioteca=biblioteca, quantitat=3)
    return llibres


@pytest.fixture
def nova_comanda(lector, biblioteca, llibres):
    def crea(estat=Estat.PREPARADA, tipus=Tipus.RECOLLIDA, de=None):
        comanda = Comanda.objects.create(
            usuari=lector, biblioteca=de or biblioteca, estat=estat, tipus_lliurament=tipus
        )
        for llibre in llibres:
            LiniaComanda.objects.create(comanda=comanda, llibre=llibre)
        return comanda

    return crea


@pytest.mark.django_db
def test_la_biblioteca_lliura_una_comanda_de_recollida_preparada(biblioteca, nova_comanda):
    comanda = nova_comanda()

    resposta = client_de(biblioteca).post(url(comanda.pk))

    assert resposta.status_code == 200
    assert resposta.json()["estat"] == "lliurada"
    assert resposta.json()["tipus_lliurament"] == "recollida"
    comanda.refresh_from_db()
    assert comanda.estat == Estat.LLIURADA
    assert list(comanda.canvis_estat.values_list("estat", flat=True)) == [Estat.LLIURADA]


@pytest.mark.django_db
def test_l_usuari_rep_l_avis_de_lliurament(biblioteca, nova_comanda, lector):
    comanda = nova_comanda()

    client_de(biblioteca).post(url(comanda.pk))

    notificacio = comanda.notificacions.get()
    assert notificacio.usuari == lector
    assert notificacio.text == text_notificacio(Estat.LLIURADA)


@pytest.mark.django_db
def test_es_creen_els_prestecs_dels_llibres(biblioteca, nova_comanda, lector, llibres):
    comanda = nova_comanda()

    client_de(biblioteca).post(url(comanda.pk))

    prestecs = Prestec.objects.filter(linia__comanda=comanda).order_by("pk")
    assert [prestec.llibre for prestec in prestecs] == llibres
    assert all(prestec.usuari == lector and prestec.biblioteca == biblioteca for prestec in prestecs)


@pytest.mark.django_db
def test_una_comanda_a_domicili_no_la_lliura_la_biblioteca(biblioteca, nova_comanda):
    comanda = nova_comanda(tipus=Tipus.DOMICILI)

    resposta = client_de(biblioteca).post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": ES_A_DOMICILI}
    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA
    assert not Prestec.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("estat", "missatge"),
    [
        (Estat.REBUDA, "Aquesta comanda encara no està llesta per a recollida."),
        (Estat.LLIURADA, "Aquesta comanda ja està lliurada."),
        (Estat.CANCELLADA, "Aquesta comanda no es pot lliurar perquè està cancel·lada."),
        (Estat.EN_CAMI, "Aquesta comanda no es pot lliurar perquè està en camí."),
    ],
)
def test_nomes_es_pot_lliurar_una_comanda_preparada(biblioteca, nova_comanda, estat, missatge):
    comanda = nova_comanda(estat=estat)

    resposta = client_de(biblioteca).post(url(comanda.pk))

    assert resposta.status_code == 409
    assert resposta.json() == {"detail": missatge}
    comanda.refresh_from_db()
    assert comanda.estat == estat
    assert not comanda.notificacions.exists()
    assert not Prestec.objects.exists()


@pytest.mark.django_db
def test_lliurar_dues_vegades_no_repeteix_l_avis_ni_els_prestecs(biblioteca, nova_comanda, llibres):
    comanda = nova_comanda()
    client = client_de(biblioteca)
    client.post(url(comanda.pk))

    resposta = client.post(url(comanda.pk))

    assert resposta.status_code == 409
    assert comanda.notificacions.count() == 1
    assert Prestec.objects.filter(linia__comanda=comanda).count() == len(llibres)


@pytest.mark.django_db
def test_una_comanda_d_una_altra_biblioteca_rep_404(biblioteca, nova_comanda):
    altra = crea_biblioteca("altra@example.com", "Biblioteca Sagrada Família")
    comanda = nova_comanda(de=altra)

    resposta = client_de(biblioteca).post(url(comanda.pk))

    assert resposta.status_code == 404
    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA


@pytest.mark.django_db
def test_una_comanda_que_no_existeix_rep_404(biblioteca):
    assert client_de(biblioteca).post(url(9999)).status_code == 404


@pytest.mark.django_db
def test_sense_sessio_rep_401(nova_comanda):
    assert APIClient().post(url(nova_comanda().pk)).status_code == 401


@pytest.mark.django_db
@pytest.mark.parametrize("rol", [Usuari.Role.USUARI, Usuari.Role.REPARTIDOR])
def test_qui_no_es_una_biblioteca_rep_403(nova_comanda, rol):
    comanda = nova_comanda()
    usuari = crea_usuari("altre@example.com", rol)
    if rol == Usuari.Role.REPARTIDOR:
        PerfilRepartidor.objects.create(
            usuari=usuari,
            cognoms="Puig",
            dni="12345678Z",
            telefon="612345678",
            vehicle=PerfilRepartidor.Vehicle.BICI,
            num_seguretat_social="281234567840",
            estat=PerfilRepartidor.Estat.VALIDAT,
        )

    resposta = client_de(usuari).post(url(comanda.pk))

    assert resposta.status_code == 403
    comanda.refresh_from_db()
    assert comanda.estat == Estat.PREPARADA


@pytest.mark.django_db
def test_una_comanda_de_recollida_preparada_no_pot_sortir_en_cami(nova_comanda):
    comanda = nova_comanda()

    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, Estat.EN_CAMI)


@pytest.mark.django_db
def test_una_comanda_de_recollida_preparada_es_pot_cancellar(nova_comanda):
    comanda = nova_comanda()

    canvia_estat(comanda, Estat.CANCELLADA)

    assert comanda.estat == Estat.CANCELLADA


@pytest.mark.django_db
def test_una_comanda_a_domicili_preparada_continua_sense_poder_passar_a_lliurada(nova_comanda):
    comanda = nova_comanda(tipus=Tipus.DOMICILI)

    with pytest.raises(TransicioNoPermesa):
        canvia_estat(comanda, Estat.LLIURADA)


@pytest.mark.django_db
def test_la_llista_de_la_biblioteca_diu_el_tipus_de_lliurament(biblioteca, nova_comanda):
    recollida = nova_comanda()
    domicili = nova_comanda(tipus=Tipus.DOMICILI)

    comandes = client_de(biblioteca).get("/api/prestecs/biblioteca/comandes/").json()

    tipus = {comanda["id"]: comanda["tipus_lliurament"] for comanda in comandes}
    assert tipus == {recollida.pk: "recollida", domicili.pk: "domicili"}


@pytest.mark.django_db
def test_el_recorregut_complet_d_una_comanda_de_recollida(biblioteca, lector, llibres):
    client_lector = client_de(lector)
    client_biblioteca = client_de(biblioteca)

    confirmada = client_lector.post(
        "/api/prestecs/comandes/",
        {"biblioteca": biblioteca.pk, "llibres": [llibres[0].pk], "tipus_lliurament": "recollida"},
        format="json",
    )
    id_comanda = confirmada.json()["id"]
    assert client_biblioteca.post(f"/api/prestecs/biblioteca/comandes/{id_comanda}/preparada/").status_code == 200
    assert client_lector.get("/api/prestecs/prestecs/").json() == []

    assert client_biblioteca.post(url(id_comanda)).status_code == 200

    assert client_lector.get("/api/prestecs/comandes/").json()[0]["estat"] == "lliurada"
    prestecs = client_lector.get("/api/prestecs/prestecs/").json()
    assert [prestec["llibre"]["titol"] for prestec in prestecs] == ["Solitud"]
    assert client_lector.get("/api/prestecs/notificacions/").json()[0]["text"] == text_notificacio(Estat.LLIURADA)


@pytest.mark.django_db(transaction=True)
def test_lliurar_i_cancellar_alhora_nomes_en_deixa_passar_un():
    """La biblioteca lliura la comanda alhora que l'usuari la cancel·la.

    Totes dues accions surten de "preparada", però quan una s'ha fet l'altra ja no
    està permesa: una comanda lliurada no es pot cancel·lar i una de cancel·lada no
    es pot lliurar.
    """
    biblioteca = crea_biblioteca("biblioteca@example.com", "Biblioteca Montbau")
    lector = crea_usuari("lector@example.com")
    comanda = Comanda.objects.create(
        usuari=lector, biblioteca=biblioteca, estat=Estat.PREPARADA, tipus_lliurament=Tipus.RECOLLIDA
    )
    sortida = threading.Barrier(2)
    resultats = []

    def canvia(nou_estat):
        try:
            sortida.wait()
            canvia_estat(Comanda.objects.get(pk=comanda.pk), nou_estat, des_de=[Estat.PREPARADA])
            resultats.append(nou_estat)
        except TransicioNoPermesa:
            resultats.append("rebutjat")
        finally:
            connection.close()

    fils = [threading.Thread(target=canvia, args=(estat,)) for estat in (Estat.LLIURADA, Estat.CANCELLADA)]
    for fil in fils:
        fil.start()
    for fil in fils:
        fil.join()

    comanda.refresh_from_db()
    guanyador = next(resultat for resultat in resultats if resultat != "rebutjat")
    assert "rebutjat" in resultats
    assert comanda.estat == guanyador
    assert comanda.canvis_estat.count() == 1
