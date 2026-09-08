Now with 50,000 sanctioned entities in the database, it's inenvitable that I have to do some manual data creation and profiling.


I added 3 more entities into the database:

```bash
from screening.models import *

# Entity 1: A sanctioned company (the hub)
hub = SanctionedEntity.objects.create(
    name="Wong & Associates Pte Ltd",
    entity_type="organization",
    source_id="NK-demo-hub"
)
EntityAddress.objects.create(entity=hub, full_text="Suite 1201, 88 Collyer Quay, Singapore 049320", country_code="sg")
EntityAlias.objects.create(entity=hub, text="Wong Associates")

# Entity 2: A sanctioned person (shares address with hub)
person_a = SanctionedEntity.objects.create(
    name="Li Wei",
    entity_type="person",
    source_id="NK-demo-person-a"
)
EntityAddress.objects.create(entity=person_a, full_text="Suite 1201, 88 Collyer Quay, Singapore 049320", country_code="sg")
EntityAlias.objects.create(entity=person_a, text="David Li")

# Entity 3: Another sanctioned person (shares DIFFERENT address with person_a)
person_b = SanctionedEntity.objects.create(
    name="Zhang Min",
    entity_type="person",
    source_id="NK-demo-person-b"
)
EntityAddress.objects.create(entity=person_b, full_text="Tower A, Beijing Finance Center, Chaoyang", country_code="cn")
# ALSO give person_b the same address as person_a - this creates the 2nd-degree path
EntityAddress.objects.create(entity=person_b, full_text="Suite 1201, 88 Collyer Quay, Singapore 049320", country_code="sg")

# Entity 4: A PEP (politically exposed person) with a fuzzy name match
pep = SanctionedEntity.objects.create(
    name="Sergei Lavrov",
    entity_type="person",
    source_id="NK-demo-pep"
)
EntityAlias.objects.create(entity=pep, text="Sergey Lavrov")

print("Demo data created: 4 entities, 5 addresses, 3 aliases")

```


and submitted an the following agent with the details;

```bash
| Field           | Value                                                                                 |
| --------------- | ------------------------------------------------------------------------------------- |
| **Name**        | `Sergey Lavrov`                                                                       |
| **Nationality** | `ru`                                                                                  |
| **Aliases**     | `Sergei Lavrov, Lavrov Education`                                                     |
| **Addresses**   | `[{"full_text":"Suite 1201, 88 Collyer Quay, Singapore 049320","country_code":"sg"}]` |
| **Identifiers** | `[]`                                                                                  |
```



<img src="../assets/sergey_case3.png" alt="sergey case" width="1300" />


What we are seeing is the blue node in the middle with the name Sergey Lavrov. There is an edge between the blue node and 3 other nodes (created from above) where the connections are specified as:

| Match           | Why it matched                                                                                       | Confidence |
| --------------- | ---------------------------------------------------------------------------------------------------- | ---------- |
| `address_fuzzy` | Agent address matches **Wong & Associates**                                                          | 100%       |
| `address_fuzzy` | Agent address matches **Li Wei**                                                                     | 100%       |
| `address_fuzzy` | Agent address matches **Zhang Min**                                                                  | 100%       |
| `address_fuzzy` | Agent address matches a **real company** (NAYARA ENERGY) that was already in your OpenSanctions data | 100%       |
| `name_exact`    | Agent name `Sergey Lavrov` matches alias `Sergey Lavrov` on the **Sergei Lavrov** record             | 95%        |



---

## Later: the "Hong Kong" density problem and UI fix

I screened another test agent to see how the graph behaves with a very broad address:

| Field       | Value                                             |
| ----------- | ------------------------------------------------- |
| Name        | `Asia Power Consulting`                           |
| Nationality | `hk`                                              |
| Aliases     | `APC`                                             |
| Addresses   | `[{"full_text":"Hong Kong","country_code":"hk"}]` |
| Identifiers | `[]`                                              |

The result was **Case 6**, risk 100, with a huge hairball graph. Because "Hong Kong" is such a generic address string, it fuzzy-matches a large number of sanctioned entities and then draws all the `shared_address` edges between them. The left sidebar also looked broken: every match showed the same explanation text, so it looked like duplicates even though each row was a different entity.

### What I changed in `frontend/src/views/CaseDetail.vue`

1. **Grouped matches by entity.** The sidebar now shows one card per matched entity, with the entity name, type, source_id, and all the match reasons collapsed into chips. This removes the "duplicate" look and makes the strongest confidence obvious.
2. **Collapsible sidebar.** There is a toggle to hide the match list so the graph can use the full width.
3. **Better graph styling for dense networks:**
   - Node size is now proportional to degree.
   - Labels are hidden on low-degree nodes until hovered, which dramatically reduces visual noise.
   - Added color coding: agent = blue, person = red/orange, organization = green.
   - Edges are color-coded by relationship type (name, shared attribute, etc.).
   - Added a "Fit graph" button.
   - Tuned the `cose` layout parameters for tighter, more stable layouts on large graphs.
4. **Responsive layout.** The sidebar collapses below 800 px and the graph height is reduced on small screens.

### Verification

- `npm test` passed (12/12).
- `npm run build` passed (`vue-tsc` + Vite).

### Lesson

The matcher is doing what it is supposed to do, but broad addresses like "Hong Kong" or "Russia" produce noisy results. The UI should make it easy to see *which* entities matched and why, and it should give users control over how much of the graph they see at once. A future improvement could be an address-quality hint in the screening form ("this address is very broad — expect many matches").
