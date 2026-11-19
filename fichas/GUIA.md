# Cómo se escriben las fichas

Hay dos fichas distintas. Las dos deben decir lo mismo en los datos que comparten
(temperatura, humedad, tamaño, dificultad, origen): **la de Animales manda**; si al
investigar sale algo distinto, se avisa y se corrige primero allá.

| | Ficha de la especie (Animales) | Guía de cuidados (Sitio → Fichas) |
|---|---|---|
| Dónde se edita | Animales → Especies y morphs → Editar especie | Sitio → Fichas, o en lote con el script |
| Dónde sale | Página de cada producto de la especie | `/fichas/<slug>` del sitio |
| Para qué | Vender: cómo es y lo básico para cuidarlo | Referencia completa para el cliente |
| Formato | Texto en campos fijos | JSON (`fichas/lote-N.json`) |

Reglas para las dos:

- Español de México, frases cortas, tú al lector. Sin relleno de marketing.
- **Nunca inventar datos.** Lo que no se sabe se dice («no sabemos de dónde viene»).
  Un dato que solo el criador sabe (tamaño de su línea, de dónde salió una variedad)
  se deja como `[dato]` y se le pregunta.
- Solo fuentes reales que se hayan leído (artículos, Plazi, GBIF, Wikipedia, guías de
  criadores serios). Las de tiendas se citan como tales.
- Usar solo especies y variedades que ya existen; nunca crear nuevas.
- Dificultad: `Fácil`, `Intermedia` o `Difícil`. Rareza: `Común`, `Poco común`,
  `Rara` o `Muy rara`.
- Especies sin identificar («sp.», «Entomobryidae sp.»): sin autoridad, y una sección
  que lo explique con honestidad.

---

## 1. Ficha de la especie (Animales → Editar especie)

| Campo | Límite | Qué lleva |
|---|---|---|
| Especie | 100 | Solo la segunda palabra: `Gestroi`, `Sp. "Panda King"`, `Klugii "Montenegro"` |
| Nombre común | 150 | `Isópodo Payaso`, `Cochinilla Enana Blanca` |
| Descripción | 2000 | 2–4 párrafos: qué es, qué lo hace especial, tamaño, morphs |
| Origen | 150 | `Montenegro y costa adriática` |
| Temperatura | 50 | `21-27 °C` |
| Humedad | 50 | `70-80 %` |
| Tamaño adulto | 50 | `18 mm`, `10-15 mm`, `Hasta 20 mm` |
| Dificultad / Rareza | opciones fijas | ver arriba |
| Hábitat y comportamiento | 2000 | Montaje: terrario, ventilación, sustrato, temperatura y humedad |
| Alimentación | 2000 | Base, verdura, proteína, calcio, qué retirar |
| Notas de esta especie | 2000 | Reproducción, para quién es y para quién no, avisos |

Una línea en blanco separa párrafos. Sin Markdown (ni `**`, ni tablas).

**Variedad (morph)**: nombre entre comillas simples (`'Papaya'`) y una «Descripción del
morph» de 1–3 párrafos (máx. 2000) solo con apariencia y lo que la distingue; los
cuidados se heredan de la especie.

---

## 2. Guía de cuidados (Sitio → Fichas)

Un archivo JSON con una lista de fichas (ver `lote-1.json` y `lote-2.json`). Campos:

| Campo | Límite | Qué lleva |
|---|---|---|
| `especie` | — | Nombre científico completo, para ubicarla |
| `species_id` | — | Número de la especie si se conoce (gana sobre `especie`) |
| `summary` | **600**, obligatorio | Un párrafo: qué es, por qué interesa, lo clave del cuidado |
| `authority` | 200 | `Brandt, 1833`; entre paréntesis si cambió de género: `(Stål, 1856)`; vacío en «sp.» |
| `origin` | 150 | Igual que en Animales |
| `difficulty` | opciones | Igual que en Animales |
| `taxonomy` | filas | `{rank, name, italic}`: Orden, Suborden/Subfamilia si aplica, Familia, Género *(itálica)*, Especie *(itálica)*, Autoridad, Combinación original *(itálica)*, Nombre común, Variedades, Estado: `En cultivo` |
| `facts` | label 60, value 120 | 7–10 datos rápidos; sin fila `Dificultad` (el sitio la pone sola desde `difficulty`) |
| `morphology` | label 60, text 1000 | Adulto, juvenil, rasgos de la familia, cada variedad, identificación |
| `habitat` | 2000 | Dónde vive en la naturaleza (no el terrario) |
| `tags` | máx. 12 | 6–8 etiquetas cortas |
| `basics` | lista | 6 líneas: contenedor, sustrato, temperatura, humedad, comida, el aviso clave |
| `body` | Markdown | Ver abajo |
| `references` | text 600 | `{text, url}`; la url con `https://` o `null` |
| `photos`, `video` | | Opcional: links de Cloudinary con `alt`. Cada foto puede llevar `section` con el título exacto de una sección del cuerpo («Alimentación») para salir ahí; sin `section` el sitio las reparte solo |

### El cuerpo (`body`)

Markdown; cada `## ` es una sección. Admite `**negritas**`, `*itálicas*`, listas y
tablas. Orden habitual (se omite lo que no aplique):

1. `## Sobre esta especie`: solo si no está identificada.
2. `## Lo esencial`: la regla de oro y 2–3 viñetas.
3. `## Terrario y sustrato` o `## Cultivo`: tabla `| | Recomendación |`.
4. `## Temperatura y humedad`: tabla de rangos si aporta.
5. `## Alimentación`: viñetas con **Base**, verdura, proteína, calcio.
6. `## Reproducción`.
7. `## Variedades`: tabla, y el aviso de criarlas separadas si se cruzan.
8. `## Usos` o `## Uso en terrarios` / `## Problemas comunes` (tabla Problema · Causa · Solución).
9. `## Datos curiosos`: 2–4 viñetas con datos verificables.

### Cargarlas

```
poetry run python scripts/import_care_sheets.py fichas/lote-N.json --email <correo> --publicar
poetry run python scripts/import_care_sheets.py fichas/lote-N.json --email <correo> --aplicar --publicar
```

El primero solo revisa; el segundo escribe y las deja visibles. Si la especie ya tiene
guía, se reemplaza completa (se pierde lo editado a mano en el dashboard). Si la especie
pudo darse de alta con otra ortografía, `"tambien_como": ["..."]` la encuentra.

Las fichas de especie y variedades de Animales van en `fichas/especies-lote-N.json`
y se cargan **antes** que las guías (crean las especies que falten; de las que ya
existen solo llenan lo vacío y reportan lo distinto):

```
poetry run python scripts/import_animals.py fichas/especies-lote-N.json --email <correo>
poetry run python scripts/import_animals.py fichas/especies-lote-N.json --email <correo> --aplicar
```
