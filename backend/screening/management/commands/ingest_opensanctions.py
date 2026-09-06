"""Ingest an OpenSanctions FollowTheMoney JSON-lines dump into the screening tables.

The dump is streamed one line at a time; nothing larger than a single batch is
ever held in memory.
"""

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from screening.models import (
    EntityAddress,
    EntityAlias,
    EntityIdentifier,
    SanctionedEntity,
)


# FtM schemas we care about, mapped onto SanctionedEntity.entity_type.
SCHEMA_TO_ENTITY_TYPE = {
    "Person": "person",
    "Organization": "organization",
    "LegalEntity": "organization",
    "Company": "organization",
}

# FtM property key -> EntityIdentifier.id_type.
IDENTIFIER_PROPERTIES = {
    "passportNumber": "passport",
    "taxNumber": "tax_id",
    "innCode": "tax_id",
    "registrationNumber": "business_reg",
    "ogrnCode": "business_reg",
    "idNumber": "other",
    "npiCode": "other",
    "leiCode": "other",
}

DEFAULT_PATH = Path(settings.BASE_DIR) / "data" / "entities.ftm.json"


def parse_country_code(address_text, fallback):
    """Best-effort ISO-3166 alpha-2 for a free-text FtM address string.

    FtM addresses are unstructured, so we only trust a trailing two-letter
    segment ("... , RU"); otherwise we fall back to the entity's own country.
    """
    tail = address_text.rsplit(",", 1)[-1].strip()
    if len(tail) == 2 and tail.isalpha():
        return tail.lower()
    return fallback


class Command(BaseCommand):
    help = "Ingest OpenSanctions FtM entities from a JSON-lines dump."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Stop after N ingested entities (for testing).",
        )
        parser.add_argument(
            "--path",
            type=Path,
            default=DEFAULT_PATH,
            help=f"Path to the JSON-lines dump (default: {DEFAULT_PATH}).",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Rows per bulk_create call (default: 1000).",
        )

    def handle(self, *args, **options):
        path = options["path"]
        limit = options["limit"]
        self.batch_size = options["batch_size"]

        if not path.exists():
            raise CommandError(f"Dump not found: {path}")

        self.counts = {
            "entities": 0,
            "aliases": 0,
            "addresses": 0,
            "identifiers": 0,
            "skipped_schema": 0,
            "skipped_no_name": 0,
            "skipped_duplicate": 0,
            "bad_lines": 0,
        }

        batch = []
        processed = 0

        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue

                try:
                    entity = json.loads(line)
                except json.JSONDecodeError:
                    self.counts["bad_lines"] += 1
                    continue

                record = self.parse_entity(entity)
                if record is None:
                    continue

                batch.append(record)
                processed += 1

                if processed % 1000 == 0:
                    self.stdout.write(f"Processed {processed:,} entities...")

                if len(batch) >= self.batch_size:
                    self.flush(batch)
                    batch = []

                if limit is not None and processed >= limit:
                    break

        if batch:
            self.flush(batch)

        self.report()

    def parse_entity(self, entity):
        """Turn one FtM record into a plain dict, or None if it is not usable."""
        entity_type = SCHEMA_TO_ENTITY_TYPE.get(entity.get("schema"))
        if entity_type is None:
            self.counts["skipped_schema"] += 1
            return None

        source_id = entity.get("id")
        if not source_id:
            self.counts["skipped_no_name"] += 1
            return None

        properties = entity.get("properties") or {}

        names = properties.get("name") or []
        if not names or not str(names[0]).strip():
            self.counts["skipped_no_name"] += 1
            return None

        countries = properties.get("country") or []
        country = ""
        if countries and len(str(countries[0])) == 2:
            country = str(countries[0]).lower()

        aliases = []
        for alias in properties.get("alias") or []:
            alias = str(alias).strip()
            if alias:
                aliases.append(alias[:255])

        addresses = []
        for address in properties.get("address") or []:
            address = str(address).strip()
            if address:
                addresses.append((address, parse_country_code(address, country)))

        # Dedupe identifiers inside a single entity; the same number often
        # appears under several property keys.
        identifiers = {}
        for key, id_type in IDENTIFIER_PROPERTIES.items():
            for raw_value in properties.get(key) or []:
                raw_value = str(raw_value).strip()
                if raw_value:
                    identifiers[(id_type, EntityIdentifier.hash_value(raw_value))] = None

        return {
            "source_id": str(source_id)[:255],
            "name": str(names[0]).strip()[:255],
            "entity_type": entity_type,
            "aliases": aliases,
            "addresses": addresses,
            "identifiers": list(identifiers),
        }

    @transaction.atomic
    def flush(self, batch):
        """Write one batch: entities first, then their children by FK id."""
        # Dedupe by source_id within the batch (the dump can repeat an id).
        by_source_id = {}
        for record in batch:
            if record["source_id"] in by_source_id:
                self.counts["skipped_duplicate"] += 1
                continue
            by_source_id[record["source_id"]] = record

        # Entities already ingested are skipped wholesale, so a re-run does not
        # pile duplicate aliases/addresses onto them (those tables have no
        # unique constraint for ignore_conflicts to catch).
        existing = set(
            SanctionedEntity.objects.filter(
                source_id__in=list(by_source_id)
            ).values_list("source_id", flat=True)
        )
        new_records = [r for r in by_source_id.values() if r["source_id"] not in existing]
        self.counts["skipped_duplicate"] += len(existing)

        if not new_records:
            return

        SanctionedEntity.objects.bulk_create(
            [
                SanctionedEntity(
                    name=r["name"],
                    entity_type=r["entity_type"],
                    source_id=r["source_id"],
                )
                for r in new_records
            ],
            batch_size=self.batch_size,
            ignore_conflicts=True,
        )
        self.counts["entities"] += len(new_records)

        # bulk_create(ignore_conflicts=True) does not populate primary keys, so
        # read the ids back before building the child rows.
        id_map = dict(
            SanctionedEntity.objects.filter(
                source_id__in=[r["source_id"] for r in new_records]
            ).values_list("source_id", "id")
        )

        aliases = []
        addresses = []
        identifiers = []
        for record in new_records:
            entity_id = id_map.get(record["source_id"])
            if entity_id is None:
                continue

            for alias in record["aliases"]:
                aliases.append(EntityAlias(entity_id=entity_id, text=alias))

            for address_text, country_code in record["addresses"]:
                addresses.append(
                    EntityAddress(
                        entity_id=entity_id,
                        full_text=address_text,
                        country_code=country_code,
                    )
                )

            for id_type, value_hash in record["identifiers"]:
                identifiers.append(
                    EntityIdentifier(
                        entity_id=entity_id,
                        id_type=id_type,
                        value_hash=value_hash,
                    )
                )

        for model, rows, key in (
            (EntityAlias, aliases, "aliases"),
            (EntityAddress, addresses, "addresses"),
            (EntityIdentifier, identifiers, "identifiers"),
        ):
            if rows:
                model.objects.bulk_create(
                    rows, batch_size=self.batch_size, ignore_conflicts=True
                )
                self.counts[key] += len(rows)

    def report(self):
        self.stdout.write(self.style.SUCCESS("Ingestion complete."))
        for label, key in (
            ("Entities created", "entities"),
            ("Aliases created", "aliases"),
            ("Addresses created", "addresses"),
            ("Identifiers created", "identifiers"),
            ("Skipped (schema not screened)", "skipped_schema"),
            ("Skipped (no name)", "skipped_no_name"),
            ("Skipped (already ingested)", "skipped_duplicate"),
            ("Unparseable lines", "bad_lines"),
        ):
            self.stdout.write(f"  {label}: {self.counts[key]:,}")
