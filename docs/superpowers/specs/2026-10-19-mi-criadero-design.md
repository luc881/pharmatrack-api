# Mi criadero: animales en venta, pie de cría y en crianza

Fecha: 2026-10-19
Estado: listo para aprobación del dueño
Repos: `pharmatrack-api` (modelo, reglas) y `pharmatrack-frontend` (dashboard).
El sitio público (`pharmatrack-web`) no cambia: obedece lo que filtre el API.

## Por qué

El dueño quiere **un solo lugar para todo lo vivo que tiene**, se venda o no,
y poder decir por especie: «tengo X para venta, Y de pie de cría y Z
creciendo».

Hoy el dashboard asume que todo ejemplar está a la venta. Al darlo de alta nace
su producto gemelo del POS y aparece en la tienda. El campo `status`
(disponible, apartado, vendido, murió) describe solo el ciclo de venta. No hay
forma de registrar un reproductor o una cría que todavía no se vende sin que se
anuncie. Tampoco se puede llevar la bitácora por ejemplar de esos animales,
porque no existen en el sistema.

En palabras del dueño: «que haya una sección para poder manejar mis animales o
todo lo que tengo criando o en cultivo y lo que está en venta».

## Qué es el éxito

- **Abrir «Mi criadero» y leer por especie,** sin hacer cuentas, cuántos hay en
  venta, cuántos son pie de cría y cuántos están en crianza.
- **Pasar un animal de un destino a otro con un botón:** una cría lista se pone
  en venta, y una hembra en venta pasa a pie de cría. En colonias (isópodos,
  fásmidos) se mueve una cantidad: «pasa 6 a venta».
- **Llevar la bitácora por ejemplar de cualquier animal.** Ningún animal fuera
  de venta se ve en la tienda ni se puede cobrar en el POS.

## Metas

1. **Destino por animal:** `En venta`, `Pie de cría` o `En crianza`. Se elige al
   darlo de alta y se cambia después.
2. **Vista «Mi criadero»:** reemplaza la pestaña «Ejemplares». Muestra conteos
   por destino y por especie, filtros por destino, y acciones visibles con
   texto.
3. **Mover entre destinos,** por ejemplar o por cantidad (colonias y paquetes).
4. **Fuera de venta = invisible para vender:**
   - no aparece en el catálogo público, ni en el listado ni en el detalle;
   - no se puede pedir en la tienda;
   - no aparece en el selector del POS;
   - el API rechaza cobrarlo, incluso dentro de un paquete.
5. **La bitácora, Cultivos y la ficha del ejemplar muestran el destino.** La
   bitácora incluye a todos los ejemplares vivos, se vendan o no.
6. **«Quitar del plan» en la bitácora:** ya hecho y desplegado (2026-10-19,
   commit `7af4073`).

## No metas (por ahora)

- Genealogía: padre y madre, camadas, posturas, parejas. Se puede agregar
  después sobre este modelo.
- Nombre o apodo por ejemplar, gráficas de peso.
- Cambios en el sitio público, más allá de lo que deje de mandarle el API.
- Rehacer la bitácora, la taxonomía o el POS. Solo se ajustan los puntos de
  contacto descritos aquí.

## Anti-metas (sería un fracaso aunque funcione)

- Que un animal de pie de cría o en crianza **aparezca en la tienda o se pueda
  cobrar**, por cualquier camino: catálogo, detalle con link compartido,
  pedido web, POS o paquete.
- Que **vender se vuelva más lento**. El flujo del POS no cambia para lo que sí
  está en venta.
- **Perder historial de la bitácora** al mover un animal o una cantidad.
- Acciones escondidas en íconos sin texto. Regla del dueño: botones con texto y
  todo a la vista (memoria `feedback_ux-visible-a-la-vista`).

## Modelo (decidido)

### `animals.purpose`

- Columna nueva `purpose String(20) NOT NULL server_default 'sale'`, con índice.
- Valores: `sale` (En venta), `breeder` (Pie de cría), `growing` (En crianza).
- Migración Alembic. Las filas existentes quedan en `sale`, que es lo que son
  hoy.
- Enum `AnimalPurposeEnum` en `types/animals.py`, al lado de
  `AnimalStatusEnum`, con el mismo patrón: String más validación Pydantic.

### Relación con `status`

`status` sigue siendo el ciclo de venta y vida. `purpose` dice para qué es el
animal. Combinaciones válidas:

| purpose | status permitidos |
|---|---|
| sale | available, reserved, sold, deceased |
| breeder, growing | available (en la UI: «Activo»), deceased |

Reglas:

- **Cambiar de destino** solo si `status == available`.
  - Un apartado se libera primero.
  - Un vendido o uno que murió no se mueve.
  - Si no se cumple, el API responde 400 con mensaje en español.
- **Apartar** (`reserved`) solo con `purpose == sale`.
- **Una baja** en la bitácora sigue funcionando igual para cualquier destino.
  Borrar la baja regresa el ejemplar a como estaba; `prev_status` no cambia.

### Precio

- `price` sigue siendo obligatorio en la columna.
- Para `breeder`/`growing`, el formulario no lo pide y manda 0.
- Al pasar a `sale` con precio 0, el diálogo de mover pide el precio antes de
  confirmar. El API exige `price > 0` cuando el destino final es `sale`.

### Colonias y paquetes (`sale_format` package o colony)

- Hoy un solo registro `Animal` guarda N unidades en los lotes de su producto
  gemelo (`stock`).
- Con destinos, cada combinación de **especie + conjunto de morphs + destino**
  es un registro aparte con su cantidad. Ejemplo: Isópodos «Cultivo» en venta
  (6) y en crianza (50).
- **Mover N unidades:**
  - resta N del registro origen y suma N al registro hermano del destino;
  - si el hermano no existe, se crea, con el mismo patrón de alta que hoy (código
    nuevo y producto gemelo nuevo);
  - el registro origen puede quedar en 0: no se borra, para conservar su
    historial.
- **Ajuste de stock:** reusar la lógica que ya existe (`AnimalUpdate.stock`,
  «resurtir cepa») en lugar de escribir otra manipulación de lotes. **Ojo:**
  esa lógica hoy pone `sold` al llegar a 0. Mover **nunca** cambia `status`;
  ver abajo.

**Unidades en especies por paquete (decidido por el dueño, 2026-10-19):**
fuera de venta se cuenta en **animales sueltos**, y en venta sigue en
**paquetes**.

- **De crianza o pie de cría a venta:** el diálogo pide **cuántos paquetes**.
  - Resta paquetes × `package_size` animales del origen.
  - Si no alcanzan, responde 400.
  - Lo que sobra se queda donde estaba.
- **De venta a crianza o pie de cría:** se mueven N paquetes y llegan
  N × `package_size` animales.
- **Tarjetas y chips** cuentan animales. Por ejemplo, los isópodos dicen «6
  paquetes en venta (36)».
- **Decisión del diseñador:**
  - el formato `colony` (cepa sin cantidad definida) cuenta en **cepas** en
    todos los destinos, a razón de 1:1, porque la cepa es la unidad de venta y
    de crianza a la vez;
  - `individual` siempre cuenta 1.

**Decisiones del diseñador (no las tomó el dueño):**

- **Un registro que se vacía por mover** queda `available` con stock 0
  («vacío»).
  - No entra en los conteos.
  - En la lista solo se ve con el filtro «Todo», en gris y con la etiqueta
    «Vacío».
  - `sold` sigue reservado a la venta y `deceased` a las bajas.
- **Al buscar el registro destino** solo cuentan los `available`, aunque estén
  en 0; esos se reactivan al recibir unidades. Un registro `sold` o `deceased`
  nunca se reusa: se crea uno nuevo.
- **Mover todo** (`quantity` null o igual al stock):
  - sin registro destino, cambia el `purpose` del mismo registro, y su
    historial viaja con los animales;
  - con registro destino, las unidades pasan a ese registro y el origen queda
    vacío. No se fusionan historiales: la bitácora de colonias es casi toda
    por especie, así que nada se pierde de vista.
- **Unicidad:** «especie + conjunto de morphs + destino» es único entre los
  registros `available` de colonias y paquetes. Lo hace cumplir el API, no la
  base de datos:
  - dar de alta una colonia que ya existe para ese destino → 400, «Ya existe;
    ajusta su cantidad»;
  - editar los morphs de modo que choquen con otro registro → 400.
- **El registro destino nuevo copia del origen:** costo, descripción, foto
  principal y fotos, documentación legal y morphs. El sexo queda «unknown».
- **Precio:**
  - el del request, si viene;
  - si no viene, el del registro destino si existe;
  - si tampoco, el del origen;
  - si al final el destino es `sale` con precio 0 → 400 pidiendo precio.
- **Otras salidas que también filtran `purpose == sale`,** por la anti-meta de
  no vender lo que no está en venta:
  - el cambio por otro ejemplar (`validate_replacement` en
    `utils/animal_replacement.py`);
  - el selector de ejemplares en Entregas;
  - el conteo de «en venta» en el índice público de fichas (`care_sheets.py`).

  Para usar un pie de cría ahí, primero se pone en venta.

### Endpoint de mover

```
POST /api/v1/animals/{id}/move
{ "purpose": "sale" | "breeder" | "growing",
  "quantity": int | null,   # solo colonias/paquetes; null = todo
  "price": float | null }   # requerido si el destino es sale y el precio es 0
→ 200 con los registros afectados (origen y, si aplica, hermano)
```

- Individual: cambia `purpose` del mismo registro; `quantity` se ignora.
- Permiso: `animals.update`.
- Transacción única: o se mueve todo o nada.

### Dónde se aplica «solo en venta» (API)

- `public_animals.py`, listado y detalle: `purpose == sale`. Un link compartido
  a un pie de cría responde 404, igual que hoy uno que murió.
- `shop.py`, disponibilidad para pedidos web (consulta de `status ==
  "available"`, alrededor de la línea 174): agregar `purpose == sale`.
- `sales.py`, `complete_sale`: igual que la guarda de reservados y muertos
  (líneas ~332–350). Si algún producto efectivo, con paquetes ya expandidos,
  pertenece a un animal con `purpose != sale`, responde 400 y lista los
  códigos.
- `GET /animals` (admin): acepta el filtro `purpose`, opcional. La respuesta
  incluye `purpose`.

## Dashboard (decidido)

### Navegación

- La pestaña «Ejemplares» se llama **«Mi criadero»**. Misma ruta,
  `/dashboard/animal`; solo cambia la etiqueta en `section-tabs-config.js`.

### Vista «Mi criadero» (reconstrucción de `animal-list-view.jsx`)

1. **Arriba, tres tarjetas de conteo:**
   - En venta, con «N disponibles · M apartados».
   - Pie de cría.
   - En crianza.

   Cuentan unidades: un individual cuenta 1 y una colonia cuenta su stock. Al
   tocar una tarjeta se filtra por ese destino.
2. **Filtro por destino,** con conteo en cada opción: Todo · En venta · Pie de
   cría · En crianza · Vendidos · Bajas. Se mantienen los filtros actuales de
   grupo, género y especie.
3. **Renglón por especie** (como hoy, expandible), con chips de conteo por
   destino. Por ejemplo: «2 pie de cría · 5 en crianza · 3 en venta».
4. **Al expandir, los ejemplares de esa especie:**
   - Columnas: Código, Morph, Sexo, Destino (chip), Estado, Cantidad (solo
     colonias o paquetes), Precio (solo en venta).
   - Acciones con texto: **«Mover a…»** (menú: Poner en venta, Pasar a pie de
     cría, Pasar a crianza; las opciones que no aplican se ven deshabilitadas
     con su razón), **Editar**, **Anotar** (abre la bitácora en ese ejemplar).
5. **Borrado múltiple:** se conserva. Las peticiones se mandan de pocas en pocas
   (unas 5 a la vez), no todas juntas.
6. **Botón «+ Nuevo animal»** arriba, como hoy.

### Formulario de alta y edición (`animal-create-edit-form.jsx`)

- **La primera sección pregunta «¿Para qué es?»** con tres opciones grandes,
  cada una con su explicación en una línea:
  - **En venta:** aparece en la tienda y en el POS.
  - **Pie de cría:** reproductores; no se venden.
  - **En crianza:** crías o cultivo que todavía no salen a la venta.
- **Precio, oferta y precio anterior:** solo con «En venta». Documentación
  legal: siempre visible.
- **Colonias o paquetes:** la cantidad se pide con su etiqueta. Por ejemplo,
  «¿Cuántos en crianza?».
- **Al editar,** el destino se muestra pero se cambia con «Mover a…», para que
  pasen las mismas reglas que en la lista.
- **Venir de un enlace** con `?purpose=` lo preselecciona; sin él, se
  preselecciona `sale`, que es el comportamiento actual.

### Ficha del ejemplar (`animal-details-view.jsx`)

- Arriba: chip de destino, chip de estado y botón **«Mover a…»**.
- Si el ejemplar no existe (404): mensaje «Este ejemplar ya no existe» con
  enlace a Mi criadero. Hoy queda en blanco.

### Bitácora (`husbandry-log-view.jsx`)

- El panel de ejemplares de cada especie incluye a todos los vivos, de
  cualquier destino, con una columna o chip **Destino**.
- No cambia nada más.

### Cultivos (`cultivos-view.jsx`)

- **Por especie:** mostrar cantidades por destino, en lugar de solo
  «disponibles».
- **El aviso de «bajo stock»** sigue contando solo lo que está en venta.

### POS y Hoja de inventario

- **Selector de productos del POS:** excluye gemelos de animales con
  `purpose != sale`. La guarda del API es la red de seguridad.
- **Hoja de inventario:** solo animales en venta, porque es la lista de precios
  de la convención.

## Restricciones

- **Orden de despliegue:** API con su migración primero, después el dashboard.
  El dashboard nuevo no debe romperse si el API todavía no manda `purpose`;
  tratar la ausencia como `sale`.
- **Modo convención (stack local sin internet):** el arranque local corre
  `alembic upgrade head`. Los scripts `sync-down`/`sync-up` copian la base
  completa, así que la columna nueva viaja sola. Verificarlo.
- **Base de datos:** las rutas son `async` con SQLAlchemy síncrono. Ver el fix
  `1c3f58d`, en el que `get_db` toma la conexión en el hilo. No meter `await`
  entre consultas de una misma transacción.
- **Pruebas:**
  - API: `pytest` (suite completa; hoy 548 pruebas, ~9 min). Una prueba por
    regla: catálogo, tienda, POS, mover individual, mover cantidad y precio
    requerido.
  - Dashboard: `vitest` + MSW para la vista y el diálogo de mover.
- **Estilo:**
  - Comentarios y textos en español, como el resto del código.
  - Prettier solo en archivos que ya estaban formateados.
  - Push con `git -c http.postBuffer=65536 push`.
  - No subir el API y el dashboard al mismo tiempo.
- **Datos actuales:** la base de producción tiene 0 ejemplares (2026-10-19),
  así que la migración no tiene casos raros. Aun así, debe funcionar con datos.

## Queda a criterio de quien construye

- Nombres internos de componentes y la división en archivos de la vista nueva.
  Preferir reusar `SpeciesRow`/`AnimalRow` y helpers de `utils.js`.
- Iconos y colores de los chips de destino, dentro de la paleta del tema:
  - En venta: `success`.
  - Pie de cría: `info`.
  - En crianza: `warning`.
- Si el conteo por destino se calcula en el cliente (la lista ya trae hasta 500
  ejemplares) o en un endpoint de resumen. Preferir el cliente mientras quepa.
- El código del registro hermano que se crea al mover una cantidad: el patrón
  actual de `AN-xxxx`.
