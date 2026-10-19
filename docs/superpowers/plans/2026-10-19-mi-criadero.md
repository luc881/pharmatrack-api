# Mi criadero Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give every animal a destination (`sale`, `breeder`, `growing`).

- Only `sale` animals can be sold or appear in the shop.
- Animals move between destinations individually or by quantity.
- The dashboard's «Ejemplares» tab becomes «Mi criadero», with counts by
  destination.

**Architecture:**

- **API:** a `purpose` column on `animals`. A small `utils/animal_records.py`
  module handles record creation, stock setting and the move logic, so the
  route and the move share one implementation. Every sale and shop path adds
  a `purpose == sale` filter.
- **Dashboard:** shared purpose helpers plus one `MoveAnimalDialog`, used by
  the rebuilt list, the form and the details view.

**Tech Stack:**

- **API:** FastAPI, SQLAlchemy 2 (sync session inside async routes), Alembic
  (`migrations/versions`), pytest against Postgres.
- **Dashboard:** React 19 + Vite + MUI, SWR, react-hook-form + zod, vitest +
  Testing Library + MSW.

**Spec:** `docs/superpowers/specs/2026-10-19-mi-criadero-design.md` (API repo).
Read it first; it carries the rules this plan argues from.

**Repos:**

- Tasks 1–3: `C:\Users\luc88\dev\pharmatrack-api`.
- Tasks 4–7: `C:\Users\luc88\dev\pharmatrack-frontend`.

## Global Constraints

- **Destination values and labels:** `sale` «En venta» (color `success`),
  `breeder` «Pie de cría» (`info`), `growing` «En crianza» (`warning`).
- **New column:** `animals.purpose String(20) NOT NULL server_default 'sale'`,
  indexed. Migration revision id `animals08_purpose`, down revision =
  current head (`caresheets02`). Check with `alembic heads`.
- **Valid status per destination:**
  - `breeder`/`growing`: only `available` (UI «Activo») or `deceased`.
  - `reserved`: only with `purpose == sale`.
  - The destination changes only when `status == available`.
- **Units:**
  - `individual`: always 1.
  - `colony`: «cepas», 1:1 in every destination.
  - `package`: stock is **packages** when `sale`, **individual animals** when
    `breeder`/`growing`.
  - Moving packages between `sale` and a non-sale destination converts by
    `species.package_size`.
- **Moving never sets `sold` or `deceased`:**
  - A record emptied by a move stays `available` with stock 0 («Vacío»).
  - Manually setting stock to 0 marks it `sold` **only** when `purpose == sale`.
- **Uniqueness:** for `package`/`colony` records, «species + set of morph ids
  + purpose» is unique among `available` records. Enforced in the API with a
  400 and Spanish detail.
- **Error messages:** API errors visible to the user are in Spanish. Code
  comments are in Spanish, matching the codebase.
- **Formatting:**
  - Run prettier only on files that were prettier-clean at HEAD (check with
    `git show HEAD:<f> | npx prettier --check --stdin-filepath <f>`).
  - Always run prettier on new files.
- **Commits and deploy:**
  - Commit after every task; never push from a task.
  - The coordinator pushes the API (Tasks 1–3) and waits for the Railway
    deploy before pushing the dashboard.
  - Push with `git -c http.postBuffer=65536 push`.
- **Old API:** the dashboard treats a missing `purpose` as `'sale'`.
- **Visible actions:** buttons and menu items always have text; no icon-only
  actions for new features.

## Review Focus

1. **Paths that could sell or announce a non-sale animal:**
   - the public catalog detail via a shared link;
   - a web order;
   - the POS;
   - a POS bundle that contains a breeder;
   - the death-replacement swap;
   - the delivery picker.

   Each one is pinned by a test in Task 2 or Task 7.
2. **A package move with a quantity that doesn't divide or doesn't fit:**
   asking for 3 packages of 6 with 17 animals in growing → 400 and nothing
   changes. Pinned in Task 3.
3. **A failure partway through a move:** the move commits once, so a failed
   sibling creation (for example, a duplicate code) leaves the source
   untouched. Pinned in Task 3.
4. **A non-sale colony set to stock 0 by hand,** for example after a die-off:
   it must stay `available`, not become «Vendido». Pinned in Task 1.
5. **The dashboard against the old API (no `purpose` field):**
   - the list renders everything as «En venta»;
   - the move menu still opens.

   Pinned in Task 4's helper test.

---

### Task 1: `purpose` column, schemas and the stock and uniqueness rules

**Files:**
- Modify: `src/pharmatrack/types/animals.py`: add `AnimalPurposeEnum(str, Enum)`
  with `SALE="sale"`, `BREEDER="breeder"`, `GROWING="growing"`.
- Modify: `src/pharmatrack/models/animals/orm.py`: `Animal.purpose`, as in
  Global Constraints.
- Create: `migrations/versions/animals08_purpose.py`: add the column with
  `server_default="sale"` and its index. Downgrade drops both.
- Modify: `src/pharmatrack/models/animals/schemas.py`:
  - `AnimalCreate.purpose: AnimalPurposeEnum = SALE`;
  - `AnimalResponse.purpose: AnimalPurposeEnum`;
  - `AnimalUpdate` does **not** get `purpose`. It stays `extra="forbid"`, so
    sending it returns 422; destinations change only through the move.
- Create: `src/pharmatrack/utils/animal_records.py`.
- Modify: `src/pharmatrack/api/routes/animals.py`:
  - `create_animal` and `update_animal` use the helpers;
  - `list_animals` gets `purpose: Optional[AnimalPurposeEnum] = None`, passed
    into `_animals_query(..., purpose=None)`.
- Test: `tests/test_animal_purpose.py`.

**Interfaces (produced, used by Task 3):**
- `new_animal(db, species: Species, morphs: list[Morph], *, purpose: str, stock: int, price, price_cost, compare_at_price=None, code: str | None = None, sex="unknown", birth_date=None, description=None, image=None, photos: list[str] = (), requires_legal_doc=False, legal_doc=None, legal_doc_url=None) -> Animal`
  - Creates the twin `Product` (category «Animales», `_animal_title`) and one
    `ProductBatch(quantity=stock)`.
  - Adds the animal and flushes. It does **not** commit.
  - Logic moved verbatim from `create_animal`.
- `set_animal_stock(db, animal: Animal, quantity: int) -> None`
  - The batch-rewrite block moved out of `update_animal`.
  - Status rule: quantity 0 → `sold` only if `purpose == sale` and the animal
    is not `deceased`; quantity > 0 on a `sold`/`deceased` record → `available`.
  - Does not commit.
- `find_bulk_sibling(db, animal_or_key, purpose: str, exclude_id: int | None = None) -> Animal | None`
  - Returns the `available` record with the same `species_id`, the same
    morph-id set and that purpose.
  - Takes either an `Animal` or a tuple `(species_id, frozenset(morph_ids))`.
- `_animals_category_id` and `_animal_title` move into `animal_records.py`, and
  `animals.py` imports them from there. Check
  `grep -rn "_animal_title\|_animals_category_id" src` and fix every import.

- [ ] **Step 1: Write failing tests in `tests/test_animal_purpose.py`**

  Reuse `_make_taxonomy` / `_create_animal` from `tests/test_animals.py`: import
  them, or copy the two helpers. Use a `package` species with
  `package_size=6` (species POST with `sale_format="package"`,
  `package_size=6`).

```python
def test_create_defaults_to_sale_and_accepts_breeder(auth_headers): ...
    # POST sin purpose → resp["purpose"] == "sale"; con purpose="breeder" → "breeder"
def test_list_filters_by_purpose(auth_headers): ...
    # 1 sale + 1 growing; GET /animals?purpose=growing → total == 1
def test_update_rejects_purpose_field(auth_headers): ...
    # PUT {"purpose": "breeder"} → 422
def test_reserve_only_for_sale(auth_headers): ...
    # breeder + PUT {"status": "reserved"} → 400, "venta" in detail
def test_non_sale_colony_to_zero_stays_available(auth_headers): ...
    # package species, purpose="growing", stock=10; PUT {"stock": 0} → status "available", stock 0
def test_sale_colony_to_zero_is_sold(auth_headers): ...
    # same with purpose sale → status "sold" (current behaviour kept)
def test_duplicate_bulk_record_rejected(auth_headers): ...
    # package species, two POSTs with the same morph_ids and purpose="growing" → second is 400
    # same morphs but purpose="sale" → 201
def test_editing_morphs_into_collision_rejected(auth_headers): ...
    # two growing records, morphs [] and [A]; PUT morph_ids=[] on the second → 400
```

- [ ] **Step 2: Run them and confirm they fail**

  Run: `PYTHONIOENCODING=utf-8 PYTHONPATH=src poetry run pytest -q tests/test_animal_purpose.py`

  Expected: FAIL (no `purpose` in the response; the 422 and 400 cases return
  200 or 201).

- [ ] **Step 3: Implement the enum, the column, the migration and the schemas**

- [ ] **Step 4: Implement `animal_records.py` and wire it into the routes**

  - **`create_animal`:**
    - returns 400 «Ya existe un registro de esa colonia para ese destino;
      ajusta su cantidad.» when the species is `package`/`colony` and
      `find_bulk_sibling` finds a match;
    - otherwise calls `new_animal(...)` and commits.
  - **`update_animal`:**
    - returns 400 «Solo un animal en venta se puede apartar.» on
      `status="reserved"` with `purpose != sale`;
    - runs the collision check after the morph change for bulk species;
    - replaces the inline stock block with `set_animal_stock`.

- [ ] **Step 5: Run the new tests and `tests/test_animals.py`, `tests/test_animal_stock.py`, `tests/test_animal_deceased.py`, `tests/test_animal_replacement.py`**

  Expected: all PASS. The extraction must not change the existing behavior.

- [ ] **Step 6: Run the migration locally**

  Run `alembic upgrade head` and then `alembic downgrade -1`, both against
  the local DB with `.env`.

  Expected: no errors. Leave it upgraded.

- [ ] **Step 7: Commit**

  `feat(animales): destino del animal (venta, pie de cría, crianza)`

---

### Task 2: Every selling and announcing path only sees `purpose == sale`

**Files:**
- Modify: `src/pharmatrack/api/routes/public_animals.py`: the list filter, and
  in the detail a 404 when `purpose != sale` (same as `deceased`).
- Modify: `src/pharmatrack/api/routes/shop.py`: `_listing_animals` adds
  `Animal.purpose == "sale"`.
- Modify: `src/pharmatrack/api/routes/sales.py` (`complete_sale`): a third
  guard after the deceased one. It queries `Animal.code` for
  `effective_ids` with `Animal.purpose != "sale"` and returns 400 with
  detail `f"Animal(es) que no están en venta: {codes}. Ponlos en venta o quítalos de la venta."`.
- Modify: `src/pharmatrack/utils/animal_replacement.py`: `validate_replacement`
  requires `repl.purpose == "sale"`, with message
  `f"{repl.code} no está en venta; ponlo en venta para usarlo de reemplazo."`.
- Modify: `src/pharmatrack/api/routes/care_sheets.py` (around line 125): the
  `available_count` query adds `Animal.purpose == "sale"`.
- Test: `tests/test_animal_purpose_selling.py`.

**Interfaces:** consumes `Animal.purpose` from Task 1. Produces nothing new.

- [ ] **Step 1: Write failing tests**

  Reuse `_draft_sale_for_animal` from `tests/test_animals.py` and the
  replacement setup from `tests/test_animal_replacement.py`.

```python
def test_public_list_and_detail_hide_breeder(auth_headers): ...
    # breeder + sale animal; GET /public/animals → solo el de venta; GET /public/animals/{breeder.id} → 404
def test_shop_listing_ignores_growing(...): ...
    # el endpoint de shop que usa _listing_animals no cuenta/ofrece el growing
def test_pos_rejects_breeder(auth_headers, db_session, test_user_with_role_permissions_branch_auth, test_branch): ...
    # draft sale con el producto del breeder → POST /sales/{id}/complete → 400, code in detail
def test_pos_rejects_breeder_inside_bundle(...): ...
    # paquete (bundle) cuyo componente es el producto del breeder → 400
def test_replacement_must_be_for_sale(...): ...
    # baja con replacement_animal_id = breeder → 400 "no está en venta"
def test_care_sheet_count_only_for_sale(...): ...
    # ficha publicada; 1 sale + 1 growing de la especie → available_count == 1
```

- [ ] **Step 2: Run them and confirm they fail**

  Run: `pytest -q tests/test_animal_purpose_selling.py`

  Expected: FAIL.

- [ ] **Step 3: Implement the five filters and guards listed under Files**

- [ ] **Step 4: Run them and confirm they pass**

  Run: `pytest -q tests/test_animal_purpose_selling.py tests/test_public_animals.py tests/test_shop.py tests/test_sales.py tests/test_bundles.py tests/test_animal_replacement.py tests/test_care_sheets.py`

  Expected: all PASS.

- [ ] **Step 5: Commit**

  `feat(animales): lo que no está en venta no se anuncia ni se cobra`

---

### Task 3: Move endpoint

**Files:**
- Modify: `src/pharmatrack/utils/animal_records.py`: add `move_animal`.
- Modify: `src/pharmatrack/models/animals/schemas.py`: add
  `AnimalMove(BaseModel)` with:
  - `purpose: AnimalPurposeEnum`;
  - `quantity: Optional[int] = Field(None, ge=1)`;
  - `price: Optional[float] = Field(None, gt=0)`;
  - `extra="forbid"`.
- Modify: `src/pharmatrack/api/routes/animals.py`: add
  `POST /{animal_id}/move` (`CAN_UPDATE_ANIMALS`). It returns
  `list[AnimalResponse]`: the source and, when one is touched, the target
  record, both reloaded via `_query_with_relations`. A single `db.commit()`,
  in the route.
- Test: `tests/test_animal_move.py`.

**Interfaces:**
- Consumes: `new_animal`, `set_animal_stock` and `find_bulk_sibling` from
  Task 1.
- Produces:
  - the function `move_animal(db, animal: Animal, purpose: str, quantity: int | None, price: float | None) -> list[Animal]`;
  - the endpoint `POST /api/v1/animals/{id}/move` with body
    `{purpose, quantity?, price?}`, returning `AnimalResponse[]`. Task 4
    calls it.

**`move_animal` rules** (in order; each failure raises `HTTPException(400)`
with a Spanish message and changes nothing):
1. `animal.status != available` → «Solo un animal activo (no apartado, vendido ni muerto) se puede mover.»
2. `purpose == animal.purpose` → «Ya está en ese destino.»
3. Individual species: flip `animal.purpose`. Then apply the price rule
   (below) and return `[animal]`.
4. Bulk: work out `units_out` (taken from the source, in the source's unit)
   and `units_in` (added to the target, in the target's unit):
   - `quantity=None` means all of the source stock;
   - for a package species, `quantity` is counted in **packages** when the
     source or the target is `sale`;
   - sale → non-sale: `units_out = q`, `units_in = q * package_size`;
   - non-sale → sale: `units_out = q * package_size`, `units_in = q`;
   - otherwise both equal `q`;
   - `units_out > source stock` → «No alcanzan: hay N.» (N in the source's
     unit).
5. Bulk, everything moves and `find_bulk_sibling(target)` is None: flip
   `animal.purpose` and convert the stock with `set_animal_stock(units_in)`.
   History stays with the record. Return `[animal]`.
6. Bulk, otherwise:
   - **Target exists:** `set_animal_stock(target, target.stock + units_in)`.
   - **Target missing:** create it with `new_animal(...)`. It copies
     `price_cost`, `description`, `image`, photos' URLs, `requires_legal_doc`,
     `legal_doc` and `legal_doc_url`. It copies the morphs, sets
     `sex="unknown"` and `stock=units_in`; its price comes from the price rule.
   - Then `set_animal_stock(source, source.stock - units_out)`. When it
     reaches 0 the source stays `available` because it is non-sale. A
     **sale** source that reaches 0 by a move must also stay `available`, so
     pass a flag: `set_animal_stock(..., closing=False)` skips the 0 → `sold`
     rule. Add that keyword to Task 1's signature as
     `closing: bool = True`.
   - Return `[source, target]`.
7. **Price rule** for the record that ends up as `sale`:
   - `price` from the body, if sent;
   - otherwise keep that record's own price (for a new target, the source's);
   - if the result is 0 → «Ponle precio para ponerlo en venta.»
   - Sync the twin `Product.price_retail`, as `update_animal` does.

- [ ] **Step 1: Write failing tests**

```python
def test_move_individual_flips_purpose(auth_headers): ...      # sale→breeder; GET → purpose breeder; product still exists
def test_move_reserved_rejected(auth_headers): ...             # reserved → 400
def test_move_to_sale_requires_price(auth_headers): ...        # growing price 0 → move sale sin price → 400; con price 350 → 200, price 350
def test_bulk_partial_creates_sibling(auth_headers): ...       # colony growing stock 10 → move sale quantity 4 price 200 → [src stock 6 growing, new stock 4 sale price 200], morphs copied
def test_bulk_partial_into_existing_sibling(auth_headers): ... # existing sale sibling stock 2 → move 3 → sibling 5, no new record
def test_bulk_all_without_sibling_flips(auth_headers, db_session): ... # husbandry log with animal_id = src stays pointing to same id, purpose changed
def test_bulk_all_into_sibling_leaves_source_empty(auth_headers): ... # src stock 0, status "available"
def test_package_growing_to_sale_converts(auth_headers): ...   # package_size 6, growing 40 → move sale quantity 3 → growing 22, sale 3
def test_package_sale_to_growing_converts(auth_headers): ...   # sale 5 packages → move growing quantity 2 → sale 3, growing +12
def test_package_not_enough_rejected(auth_headers): ...        # growing 17 → move sale quantity 3 → 400 "No alcanzan", stocks unchanged
def test_failed_move_changes_nothing(auth_headers, monkeypatch): ... # monkeypatch new_animal to raise → 500/400; source stock unchanged on reload
```

- [ ] **Step 2: Run them and confirm they fail**

  Run: `pytest -q tests/test_animal_move.py`

  Expected: FAIL (404 or 405 on the route).

- [ ] **Step 3: Implement `move_animal`, the schema and the route**

- [ ] **Step 4: Run the move tests, Task 1 and Task 2's tests, and then the full suite**

  Run: `pytest -q -x`, about 9 minutes; run it in the background.

  Expected: all PASS.

- [ ] **Step 5: Commit**

  `feat(animales): mover entre venta, pie de cría y crianza`

  The coordinator then pushes the API and waits for the Railway deploy:
  `GET /api/v1/animals?purpose=sale` with a token returns 200, not 422.

---

### Task 4: Dashboard foundations (purpose helpers, actions, MoveAnimalDialog)

**Files:**
- Modify: `src/sections/animal/utils.js`: add purpose constants and helpers.
- Modify: `src/lib/axios.js`: `endpoints.animal.move: (id) => \`/api/v1/animals/${id}/move\``.
- Modify: `src/actions/animal.js`:
  - `useGetAnimals({... purpose})` passes `purpose` as a query param when set;
  - `export const moveAnimal = (id, data) => axiosInstance.post(endpoints.animal.move(id), data).then((r) => r.data)`.
- Create: `src/sections/animal/move-animal-dialog.jsx`.
- Test: `src/test/animal/purpose.test.jsx`.

**Interfaces (produced, used by Tasks 5–7):**
- `PURPOSES = ['sale', 'breeder', 'growing']`.
- `PURPOSE_LABELS = { sale: 'En venta', breeder: 'Pie de cría', growing: 'En crianza' }`.
- `PURPOSE_COLORS = { sale: 'success', breeder: 'info', growing: 'warning' }`.
- `PURPOSE_HELP = { sale: 'Aparece en la tienda y en el POS.', breeder: 'Reproductores; no se venden.', growing: 'Crías o cultivo que todavía no salen a la venta.' }`.
- `purposeOf(animal) -> 'sale'|'breeder'|'growing'`: `animal.purpose ?? 'sale'`.
- `animalUnits(animal, species) -> number` (counted in animals):
  - 0 if the status is `sold` or `deceased`;
  - individual → 1;
  - colony → stock;
  - package → `stock * package_size` when `sale`, otherwise stock.
- `countByPurpose(animals, speciesById) -> { sale, breeder, growing, reserved, salePackages }`:
  - counts animals with `status === 'available'` or `'reserved'`;
  - `reserved` is the number of reserved;
  - `salePackages` is the sum of sale package stock.
- `statusLabel(animal)`: `available` + non-sale → 'Activo'; stock 0 +
  `available` + bulk → 'Vacío'; otherwise `STATUS_LABELS[status]`.
- `moveBlockReason(animal) -> string | null`:
  - not `available` → 'Primero libera el apartado' (reserved) or 'Ya no está
    en tu criadero' (sold or deceased);
  - otherwise null.
- `<MoveAnimalDialog animal species target open onClose onMoved />`:
  - `target` is the destination purpose; `onMoved(updatedRecords)`.
  - Shows «Mover a {PURPOSE_LABELS[target]}».
  - For bulk species, a quantity field:
    - label «¿Cuántos paquetes?» when the package species' source or target
      is sale; «¿Cuántos?» otherwise;
    - helper text «Hay N»;
    - an «Todos» checkbox sends `quantity: null`.
  - When `target === 'sale'` and `Number(animal.price) === 0`, a required
    price field «Precio de venta».
  - Calls `moveAnimal`, shows `toast.success('Movido a …')` or
    `toast.error(error.message)`.

- [ ] **Step 1: Write failing tests**

```jsx
it('purposeOf trata la falta de purpose como venta', ...)        // purposeOf({}) === 'sale'
it('animalUnits convierte paquetes en venta a animales', ...)    // package_size 6, sale stock 3 → 18; growing stock 17 → 17
it('countByPurpose ignora vendidos y muertos', ...)
it('MoveAnimalDialog pide precio al poner en venta uno sin precio y manda el payload', ...)
   // MSW captura POST /animals/5/move → { purpose: 'sale', quantity: 2, price: 300 }
it('MoveAnimalDialog en especie individual no pide cantidad', ...)
```

- [ ] **Step 2: Run them and confirm they fail**

  Run: `npx vitest run src/test/animal/purpose.test.jsx`

  Expected: FAIL.

- [ ] **Step 3: Implement the helpers, the actions and the dialog**

- [ ] **Step 4: Run them and confirm they pass**

  Run: `npx vitest run src/test/animal`

  Expected: PASS.

- [ ] **Step 5: Lint and format, then commit**

  Run `npx eslint src/sections/animal src/actions/animal.js` and prettier per
  Global Constraints, then commit
  `feat(animales): destino y diálogo «Mover a…» en el dashboard`.

---

### Task 5: «Mi criadero» list (rebuild of `animal-list-view.jsx`)

**Files:**
- Modify: `src/layouts/dashboard/section-tabs-config.js`: rename the label
  `'Ejemplares'` to `'Mi criadero'`; the path doesn't change. Update
  `src/test/layouts/section-tabs.test.js` if it asserts the label.
- Modify: `src/sections/animal/view/animal-list-view.jsx`. Keep its data
  loading, its group, genus and species filters, the species grouping and the
  QR dialog.
- Test: `src/test/animal/mi-criadero.test.jsx`.

**Interfaces:** consumes Task 4's helpers and `MoveAnimalDialog`.

**Behavior:**

- **Heading «Mi criadero».** Three clickable summary cards (they set the
  destination filter):
  - En venta: `{sale}`, with the subtitle `{available} disponibles · {reserved} apartados`;
  - Pie de cría: `{breeder}`;
  - En crianza: `{growing}`.
- **Destination filter** (MUI `Tabs` or `ToggleButtonGroup`), each option with
  a count: `Todo`, `En venta`, `Pie de cría`, `En crianza`, `Vendidos`,
  `Bajas`. «Vendidos» and «Bajas» filter by status; the others filter by
  `purposeOf` among the live ones.
- **Species row:** one `Label` chip per non-zero destination, for example
  `2 pie de cría` / `5 en crianza` / `3 en venta`. Package species in sale show
  `6 paquetes en venta (36)`.
- **Expanded specimens table:**
  - Columns: Código, Morph, Sexo, Destino (chip), Estado (`statusLabel`),
    Cantidad (bulk only), Precio (only when `purposeOf === 'sale'`).
  - Actions, a text button `Mover a…` that opens a menu with the two other
    destinations: `Poner en venta`, `Pasar a pie de cría`, `Pasar a crianza`.
    The item is disabled and shows `moveBlockReason` as secondary text when it
    isn't null.
  - Also the existing edit action, and a text link `Anotar` →
    `${paths.dashboard.animal.log}?species=${species.id}`.
  - Empty bulk records (stock 0, `available`) appear only under `Todo`, with
    gray row text.
- **Bulk delete:** replace `Promise.allSettled(deleteIds.map(...))` with a
  sequential pool of 5 concurrent deletes (a small local helper
  `runInBatches(items, size, fn)` that returns allSettled-style results). The
  toasts stay the same.

- [ ] **Step 1: Write failing tests (MSW: species and animals with mixed purposes)**

```jsx
it('muestra tarjetas con conteos por destino', ...)        // 'En venta' card shows 3, 'Pie de cría' 2
it('filtrar por Pie de cría deja solo esos ejemplares', ...)
it('Mover a… → Poner en venta abre el diálogo', ...)
it('Mover a… deshabilitado para un apartado con su razón', ...) // 'Primero libera el apartado'
it('borrado múltiple manda máximo 5 a la vez', ...)          // MSW handler counts in-flight DELETEs, max <= 5
```

- [ ] **Step 2: Run them and confirm they fail**

- [ ] **Step 3: Implement the rebuild**

- [ ] **Step 4: Run `npx vitest run src/test/animal src/test/layouts`**

  Expected: PASS.

- [ ] **Step 5: Lint, format, commit**

  `feat(animales): «Mi criadero» con conteos por destino`

---

### Task 6: Form and details view

**Files:**
- Modify: `src/sections/animal/animal-create-edit-form.jsx`.
- Modify: `src/sections/animal/view/animal-details-view.jsx` and
  `src/pages/dashboard/animal/details.jsx`. The page passes the hook's error
  or loading state so the view can tell «loading» from «not found»;
  `useGetAnimal` must expose `animalError`, so add it in `src/actions/animal.js`
  if it's missing.
- Test: `src/test/animal/animal-form-purpose.test.jsx`.

**Behavior:**

- **Create:**
  - The first card is «¿Para qué es?»: three selectable cards (radio
    semantics, `role="radio"`), each with its `PURPOSE_LABELS` text and its
    `PURPOSE_HELP` line.
  - The default comes from `?purpose=` in the URL, otherwise `sale`. Sent as
    `purpose`.
  - When not `sale`, hide price, offer (compare-at) and price tiers, and send
    `price: 0`.
  - Legal documents stay visible.
  - Bulk quantity label: `¿Cuántos paquetes en venta?` (package + sale),
    `¿Cuántos en crianza?` / `¿Cuántos de pie de cría?` (non-sale),
    `¿Cuántas cepas …?` (colony).
- **Edit:**
  - The purpose shows as a chip with a `Mover a…` button (the same menu and
    dialog as Task 5; extract the menu into a component in
    `move-animal-dialog.jsx` as `MoveAnimalMenu` and reuse it in Task 5).
  - `purpose` is never sent in the PUT.
  - Price fields are hidden when not `sale`.
- **Details view:**
  - The header shows the destination chip, the status chip (`statusLabel`)
    and `MoveAnimalMenu`.
  - When the API returns 404: an `EmptyContent` with title
    `Este ejemplar ya no existe` and a button `Ir a Mi criadero` →
    `paths.dashboard.animal.root`. Today the page stays blank.

- [ ] **Step 1: Write failing tests**

```jsx
it('al crear como Pie de cría no pide precio y manda purpose breeder, price 0', ...)
it('preselecciona el destino desde ?purpose=growing', ...)
it('al editar no manda purpose', ...)
it('ficha de un ejemplar que no existe muestra el mensaje y el enlace', ...)
```

- [ ] **Step 2: Run them and confirm they fail**

- [ ] **Step 3: Implement**

- [ ] **Step 4: Run `npx vitest run src/test/animal`**

  Expected: PASS.

- [ ] **Step 5: Lint, format, commit**

  `feat(animales): destino al dar de alta y en la ficha del ejemplar`

---

### Task 7: Touchpoints (bitácora, Cultivos, POS, Entregas, Hoja de inventario)

**Files:**
- `src/sections/animal/view/husbandry-log-view.jsx`: in `SpecimenPanel`'s
  table, add a column `Destino` with a `Label` (`PURPOSE_LABELS`/`COLORS`) per
  specimen. `specimensOf` already includes every non-sold specimen, so no
  filter changes.
- `src/sections/animal/view/cultivos-view.jsx`:
  - `availableUnits` and `availableBySpecies` count only
    `purposeOf(a) === 'sale'`, so the low-stock warning stays sale-only;
  - add per-species chips for breeder and growing counts (`animalUnits`).
- `src/sections/sale/sale-create-edit-form.jsx`: `useBlockedAnimalProducts`
  also loads `purpose: 'breeder'` and `'growing'` (status `available`) and maps
  their `product_id` to `'Pie de cría'` / `'En crianza'`. The existing disabled
  option and label then do the rest.
- `src/sections/delivery/view/delivery-list-view.jsx:277`:
  `useGetAnimals({ page: 1, pageSize: 500, status: 'available', purpose: 'sale' })`.
- `src/sections/animal/view/inventory-sheet-view.jsx`: request
  `purpose: 'sale'` in its `useGetAnimals` call (line ~83). The `forSale`
  computation (line ~130) then needs no change.
- Test: extend `src/test/animal/purpose.test.jsx` or add
  `src/test/animal/touchpoints.test.jsx`.

- [ ] **Step 1: Write failing tests**

```jsx
it('Cultivos: el bajo stock cuenta solo lo que está en venta', ...)  // availableUnits([...growing 50, sale 1]) === 1
it('POS: un pie de cría sale deshabilitado con su etiqueta', ...)     // option shows 'Pie de cría', aria-disabled
it('Entregas pide solo animales en venta', ...)                      // MSW asserts request has purpose=sale
```

- [ ] **Step 2: Run them and confirm they fail**

- [ ] **Step 3: Implement**

- [ ] **Step 4: Run the full suite with `npx vitest run`**

  Expected: all PASS. `src/test/care-sheet/care-sheet.test.jsx` has
  pre-existing local modifications; don't touch or commit that file.

- [ ] **Step 5: Lint, format, commit**

  `feat(animales): destino en bitácora, cultivos, POS, entregas y hoja`

  The coordinator then runs `npx vite build`, pushes the dashboard, and checks
  it in the browser against production.
