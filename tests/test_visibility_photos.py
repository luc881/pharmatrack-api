"""Qué se ve en el sitio y de dónde salen las fotos.

- La nominal (la especie) y cada variedad se muestran u ocultan por separado:
  ocultar la nominal no esconde Glacier.
- Un ejemplar puede quedarse fuera del sitio (solo venta rápida o mostrador).
- Las fotos de especie y variedad son la fuente de verdad: un ejemplar sin
  foto propia usa la de su variedad y, si no, la de su especie.
"""
from fastapi import status

from .utils import client
from .test_animals import (_make_taxonomy, _create_animal, animals_put, morphs_post,
                           species_put)

PUBLIC = "/api/v1/public/animals"
PUBLIC_SPECIES = "/api/v1/public/species"
QUICK = "/api/v1/products/quick-sale"


def _ids(url=PUBLIC):
    return {a["id"] for a in client.get(url).json()["data"]}


# =========================================================
# Nominal y variedades, independientes
# =========================================================
def test_hiding_the_nominal_keeps_its_varieties(auth_headers):
    *_, sp, glacier = _make_taxonomy(auth_headers, morph_name="Glacier")
    nominal = _create_animal(auth_headers, sp["id"])
    variety = _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"]])

    species_put(f"/{sp['id']}", json={"show_public": False}, headers=auth_headers)

    assert _ids() == {variety["id"]}
    assert client.get(f"{PUBLIC}/{variety['id']}").status_code == status.HTTP_200_OK
    assert client.get(f"{PUBLIC}/{nominal['id']}").status_code == status.HTTP_404_NOT_FOUND

    # la especie sigue en el catálogo (su variedad la necesita), marcada sin nominal
    species = client.get(PUBLIC_SPECIES).json()
    assert [(s["id"], s["nominal_public"]) for s in species] == [(sp["id"], False)]
    assert [m["name"] for m in species[0]["morphs"]] == ["Glacier"]


def test_species_with_nothing_visible_leaves_the_catalog(auth_headers):
    *_, sp, glacier = _make_taxonomy(auth_headers, morph_name="Glacier")
    species_put(f"/{sp['id']}", json={"show_public": False}, headers=auth_headers)
    client.put(f"/api/v1/morphs/{glacier['id']}", json={"show_public": False}, headers=auth_headers)
    assert client.get(PUBLIC_SPECIES).json() == []


def test_hiding_a_variety_keeps_the_nominal(auth_headers):
    *_, sp, glacier = _make_taxonomy(auth_headers, morph_name="Glacier")
    nominal = _create_animal(auth_headers, sp["id"])
    _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"]])
    client.put(f"/api/v1/morphs/{glacier['id']}", json={"show_public": False}, headers=auth_headers)
    assert _ids() == {nominal["id"]}


# =========================================================
# Un ejemplar fuera del sitio (solo venta rápida)
# =========================================================
def test_animal_can_stay_off_the_site_but_in_quick_sale(auth_headers):
    *_, sp, _m = _make_taxonomy(auth_headers)
    hidden = _create_animal(auth_headers, sp["id"], show_public=False, quick_sale=True)
    shown = _create_animal(auth_headers, sp["id"])
    assert hidden["show_public"] is False and hidden["quick_sale"] is True
    assert shown["show_public"] is True and shown["quick_sale"] is False

    assert _ids() == {shown["id"]}
    assert client.get(f"{PUBLIC}/{hidden['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert [i["id"] for i in client.get(QUICK, headers=auth_headers).json()] == [hidden["product_id"]]


def test_edit_changes_site_and_quick_sale(auth_headers):
    *_, sp, _m = _make_taxonomy(auth_headers)
    animal = _create_animal(auth_headers, sp["id"])

    res = animals_put(str(animal["id"]), json={"show_public": False, "quick_sale": True},
                      headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["show_public"] is False and res.json()["quick_sale"] is True
    assert _ids() == set()
    assert len(client.get(QUICK, headers=auth_headers).json()) == 1


# =========================================================
# Fotos de especie y variedad
# =========================================================
def test_species_and_morph_take_several_photos(auth_headers):
    *_, sp, glacier = _make_taxonomy(auth_headers, morph_name="Glacier")
    res = species_put(f"/{sp['id']}", json={"photos": ["https://x/a.jpg", "https://x/b.jpg"]},
                      headers=auth_headers)
    assert res.status_code == status.HTTP_200_OK, res.text
    assert res.json()["photos"] == ["https://x/a.jpg", "https://x/b.jpg"]
    # la primera es la principal
    assert res.json()["image"] == "https://x/a.jpg"

    res = client.put(f"/api/v1/morphs/{glacier['id']}", json={"photos": ["https://x/g.jpg"]},
                     headers=auth_headers)
    assert res.json()["photos"] == ["https://x/g.jpg"] and res.json()["image"] == "https://x/g.jpg"

    # vaciar quita también la principal
    res = species_put(f"/{sp['id']}", json={"photos": []}, headers=auth_headers)
    assert res.json()["photos"] == [] and res.json()["image"] is None

    morph = morphs_post(json={"species_id": sp["id"], "name": "Papaya",
                              "photos": ["https://x/p.jpg"]}, headers=auth_headers).json()
    assert morph["image"] == "https://x/p.jpg"


def test_animal_without_photo_shows_its_variety_or_species_photo(auth_headers):
    *_, sp, glacier = _make_taxonomy(auth_headers, morph_name="Glacier")
    species_put(f"/{sp['id']}", json={"photos": ["https://x/sp.jpg"]}, headers=auth_headers)
    client.put(f"/api/v1/morphs/{glacier['id']}", json={"photos": ["https://x/gl.jpg"]},
               headers=auth_headers)
    nominal = _create_animal(auth_headers, sp["id"], quick_sale=True)
    variety = _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"]], quick_sale=True)
    own = _create_animal(auth_headers, sp["id"], quick_sale=True, photos=["https://x/own.jpg"])

    images = {i["id"]: i["image"] for i in client.get(QUICK, headers=auth_headers).json()}
    assert images == {
        nominal["product_id"]: "https://x/sp.jpg",
        variety["product_id"]: "https://x/gl.jpg",
        own["product_id"]: "https://x/own.jpg",
    }


def test_new_taxon_photo_reaches_existing_products(auth_headers):
    """Los animales que ya existían, sin foto propia, toman la foto nueva."""
    *_, sp, glacier = _make_taxonomy(auth_headers, morph_name="Glacier")
    nominal = _create_animal(auth_headers, sp["id"])
    variety = _create_animal(auth_headers, sp["id"], morph_ids=[glacier["id"]])
    own = _create_animal(auth_headers, sp["id"], photos=["https://x/own.jpg"])

    species_put(f"/{sp['id']}", json={"photos": ["https://x/sp.jpg"]}, headers=auth_headers)
    client.put(f"/api/v1/morphs/{glacier['id']}", json={"photos": ["https://x/gl.jpg"]},
               headers=auth_headers)

    def image(animal):
        return client.get(f"/api/v1/products/{animal['product_id']}", headers=auth_headers).json()["image"]

    assert image(nominal) == "https://x/sp.jpg"
    assert image(variety) == "https://x/gl.jpg"
    assert image(own) == "https://x/own.jpg"


def test_photo_urls_longer_than_the_column_are_rejected(auth_headers):
    *_, sp, _m = _make_taxonomy(auth_headers)
    res = species_put(f"/{sp['id']}", json={"photos": ["https://x/" + "a" * 300]}, headers=auth_headers)
    assert res.status_code == 422


def test_moving_part_of_a_hidden_lot_keeps_it_hidden(auth_headers):
    from .test_animal_move import _bulk_species, _move

    sp = _bulk_species(auth_headers)
    src = _create_animal(auth_headers, sp["id"], purpose="breeder", stock=10, show_public=False)
    res = _move(auth_headers, src["id"], purpose="sale", quantity=4, price=200)
    assert res.status_code == status.HTTP_200_OK, res.text
    moved = [a for a in res.json() if a["id"] != src["id"]][0]
    assert moved["show_public"] is False


def test_species_and_morph_can_be_created_already_hidden(auth_headers):
    """El formulario de alta manda «Visible en el sitio»: no es un 422."""
    from .test_animals import species_post
    *_, sp, _m = _make_taxonomy(auth_headers)
    res = species_post(json={"genus_id": sp["genus_id"], "name": "Caffrorum", "show_public": False},
                       headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    assert res.json()["show_public"] is False

    res = morphs_post(json={"species_id": sp["id"], "name": "Oculta", "show_public": False},
                      headers=auth_headers)
    assert res.status_code == status.HTTP_201_CREATED, res.text
    assert res.json()["show_public"] is False


def test_validation_errors_are_logged(auth_headers, caplog):
    """Un 422 deja rastro en el registro (Railway): ruta y campos, sin los valores."""
    import logging
    with caplog.at_level(logging.WARNING):
        res = client.post("/api/v1/species", json={"genus_id": 1, "name": "x", "inventado": "secreto"},
                          headers=auth_headers)
    assert res.status_code == 422
    logged = " ".join(r.getMessage() for r in caplog.records)
    assert "/api/v1/species" in logged and "inventado" in logged
    assert "secreto" not in logged
