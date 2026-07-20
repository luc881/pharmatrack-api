"""
pharmatrack/seeds/seed_articles.py

Artículos de divulgación de ejemplo, publicados, para visualizar la
sección del sitio. Idempotentes por título: corren siempre y no duplican.
Edítalos o bórralos desde el dashboard cuando existan artículos reales.
"""
from datetime import datetime

from sqlalchemy.orm import Session

from pharmatrack.models.articles.orm import Article

ARTICLES = [
    {
        "title": "Guía básica para tu primera tarántula",
        "category": "Cuidados",
        "excerpt": "Terrario, sustrato, humedad y alimentación: todo lo que necesitas resolver antes de traer a casa tu primer ejemplar.",
        "cover_image": "https://picsum.photos/seed/art-tarantula/1200/675",
        "author_name": "Opuntia Den",
        "author_role": "Criadora",
        "tags": ["tarántulas", "principiantes", "terrario"],
        "body": """Las tarántulas son de las mascotas exóticas más nobles para empezar: ocupan poco espacio, comen una vez por semana y sus cuidados son sencillos si entiendes tres variables — espacio, sustrato y humedad.

## El terrario ideal

Para una especie terrestre juvenil basta un contenedor de 20x20 cm con ventilación lateral. La regla más importante es la altura: una caída desde arriba puede romper el abdomen de una terrestre.

> Más sustrato y menos altura: la regla de oro para especies terrestres.

Las arborícolas son lo contrario — necesitan altura, un tronco o corcho vertical y mejor ventilación.

## Sustrato y humedad

Fibra de coco o turba de 5 a 8 cm de profundidad. La mayoría de las especies de principiante (Brachypelma, Grammostola, Tliltocatl) vienen de zonas semiáridas: un rincón ligeramente húmedo y el resto seco es suficiente.

## La alimentación

Un grillo o cucaracha del tamaño de su abdomen una vez por semana. Si no lo toma en 24 horas, retíralo — sobre todo antes de una muda, cuando dejan de comer por semanas y es completamente normal.""",
    },
    {
        "title": "Isópodos y colémbolos: el equipo de limpieza del terrario",
        "category": "Bioactivo",
        "excerpt": "Cómo funcionan los detritívoros en un montaje bioactivo y por qué son la mejor inversión para cualquier terrario húmedo.",
        "cover_image": "https://picsum.photos/seed/art-bioactivo/1200/675",
        "author_name": "Opuntia Den",
        "author_role": "Criadora",
        "tags": ["isópodos", "colémbolos", "bioactivo"],
        "body": """Un terrario bioactivo es un pequeño ecosistema que se limpia solo. El secreto son los detritívoros: isópodos y colémbolos que procesan restos de comida, heces y materia vegetal antes de que aparezcan hongos o ácaros.

## Qué hace cada quien

Los colémbolos son los primeros en llegar a cualquier resto y los mejores contra el moho. Los isópodos procesan materia más gruesa: hojarasca, madera en descomposición y mudas.

> Un cultivo establecido de colémbolos previene el 90% de los brotes de moho de un montaje nuevo.

## Cómo sembrarlos

Siembra los colémbolos directo en el sustrato al montar el terrario, una semana antes de meter al habitante principal. Los isópodos van después, con un puñado de hojarasca como refugio y primera comida.

## Mantenimiento

Prácticamente ninguno: mantén una zona húmeda y agrega hojarasca cada mes. Si la población explota, es señal de exceso de comida — reduce las raciones del habitante principal.""",
    },
    {
        "title": "Cómo elegir tu primer gecko",
        "category": "Especies",
        "excerpt": "Crestado, leopardo o gargoyle: las diferencias reales de cuidado entre los tres geckos más recomendados para empezar.",
        "cover_image": "https://picsum.photos/seed/art-gecko/1200/675",
        "author_name": "Opuntia Den",
        "author_role": "Criadora",
        "tags": ["geckos", "reptiles", "principiantes"],
        "body": """Los tres geckos que más recomendamos para empezar comparten algo: no necesitan luz UVB obligatoria si su dieta está bien suplementada, y toleran los errores típicos del primer año. Pero sus cuidados no son intercambiables.

## Gecko crestado

El más fácil de los tres. Temperatura ambiente (22-26 °C, sin foco), dieta de papilla comercial y un terrario vertical con plantas. Su único enemigo es el calor: arriba de 29 °C se estresa.

## Gecko leopardo

Terrestre y de zonas áridas: necesita una zona cálida de 30-32 °C con manta térmica y escondites secos y húmedos. Come insectos vivos, así que necesitarás mantener grillos o cucarachas.

> Si no quieres mantener insectos vivos en casa, el crestado es tu gecko.

## Gecko gargoyle

Primo del crestado con los mismos cuidados básicos, pero más territorial y de crecimiento más lento. Su ventaja: es aún más resistente y tolera mejor la manipulación.

## El veredicto

Para un primer reptil sin complicaciones: crestado. Si te atrae la interacción y no te molestan los insectos: leopardo. Si quieres algo menos común con el mismo nivel de dificultad: gargoyle.""",
    },
]


def seed_articles(db: Session):
    created = 0
    for data in ARTICLES:
        if db.query(Article.id).filter(Article.title == data["title"]).first():
            continue
        db.add(Article(**data, published_at=datetime.utcnow()))
        created += 1
    db.commit()
    print(f"   Artículos de ejemplo: {created} creados, {len(ARTICLES) - created} ya existían")
