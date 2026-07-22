"""Direcciones mexicanas: estados y códigos postales.

ponytail: rangos de CP por estado en una tabla de 32 filas, en vez de la
base completa de SEPOMEX (~145k filas) o una API de paga. Sirve para
SUGERIR el estado al escribir el CP; el usuario siempre puede corregirlo,
así que un rango impreciso es una molestia menor, nunca un bloqueo.
"""

MX_STATES = (
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche",
    "Chiapas", "Chihuahua", "Ciudad de México", "Coahuila", "Colima",
    "Durango", "Estado de México", "Guanajuato", "Guerrero", "Hidalgo",
    "Jalisco", "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca",
    "Puebla", "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa",
    "Sonora", "Tabasco", "Tamaulipas", "Tlaxcala", "Veracruz", "Yucatán",
    "Zacatecas",
)

# (inicio, fin, estado) — inclusive
_ZIP_RANGES = (
    (1000, 16999, "Ciudad de México"),
    (20000, 20999, "Aguascalientes"),
    (21000, 22999, "Baja California"),
    (23000, 23999, "Baja California Sur"),
    (24000, 24999, "Campeche"),
    (25000, 27999, "Coahuila"),
    (28000, 28999, "Colima"),
    (29000, 30999, "Chiapas"),
    (31000, 33999, "Chihuahua"),
    (34000, 35999, "Durango"),
    (36000, 38999, "Guanajuato"),
    (39000, 41999, "Guerrero"),
    (42000, 43999, "Hidalgo"),
    (44000, 49999, "Jalisco"),
    (50000, 57999, "Estado de México"),
    (58000, 61999, "Michoacán"),
    (62000, 62999, "Morelos"),
    (63000, 63999, "Nayarit"),
    (64000, 67999, "Nuevo León"),
    (68000, 71999, "Oaxaca"),
    (72000, 75999, "Puebla"),
    (76000, 76999, "Querétaro"),
    (77000, 77999, "Quintana Roo"),
    (78000, 79999, "San Luis Potosí"),
    (80000, 82999, "Sinaloa"),
    (83000, 85999, "Sonora"),
    (86000, 86999, "Tabasco"),
    (87000, 89999, "Tamaulipas"),
    (90000, 90999, "Tlaxcala"),
    (91000, 96999, "Veracruz"),
    (97000, 97999, "Yucatán"),
    (98000, 99999, "Zacatecas"),
)


def state_for_zip(zip_code: str) -> str | None:
    """Estado probable de un CP, o None si no cae en ningún rango."""
    if not zip_code or not zip_code.isdigit() or len(zip_code) != 5:
        return None
    number = int(zip_code)
    return next((state for start, end, state in _ZIP_RANGES if start <= number <= end), None)


def format_address(data: dict) -> str:
    """Arma el texto de una línea por renglón, saltando lo que falte."""
    street = " ".join(filter(None, [data.get("street"), data.get("ext_number")]))
    if data.get("int_number"):
        street = f"{street} Int. {data['int_number']}".strip()

    locality = ", ".join(filter(None, [
        f"CP {data['zip_code']}" if data.get("zip_code") else None,
        data.get("city"),
        data.get("state"),
    ]))

    lines = [street, data.get("neighborhood"), locality]
    if data.get("address_notes"):
        lines.append(f"Referencias: {data['address_notes']}")
    return "\n".join(line for line in lines if line and line.strip())
