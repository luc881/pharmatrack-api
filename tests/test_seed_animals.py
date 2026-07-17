"""El seed de ejemplo mantiene 15 animales por grupo raíz y códigos únicos."""
from collections import Counter

from pharmatrack.seeds.seed_animals import CATALOG
from pharmatrack.seeds.seed_animal_groups import GROUPS

ROOT_OF = {sub: root for root, subs in GROUPS.items() for sub in subs}


def test_seed_has_at_least_15_animals_per_root_group():
    per_root = Counter()
    for entry in CATALOG:
        per_root[ROOT_OF[entry["group"]]] += len(entry["animals"])

    assert set(per_root) == set(GROUPS), "faltan grupos raíz en el seed"
    assert all(count >= 15 for count in per_root.values()), dict(per_root)


def test_seed_package_species_declare_size():
    for entry in CATALOG:
        if entry.get("sale_format") == "package":
            assert entry.get("package_size"), entry["species"]


def test_seed_codes_are_unique():
    codes = [a["code"] for entry in CATALOG for a in entry["animals"]]
    duplicated = [code for code, n in Counter(codes).items() if n > 1]
    assert not duplicated, duplicated
