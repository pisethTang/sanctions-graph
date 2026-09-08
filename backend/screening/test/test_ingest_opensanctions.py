"""Tests for the ingest_opensanctions management command.

The command streams an OpenSanctions FollowTheMoney JSON-lines dump into the
screening tables. These tests verify:
  - parse_country_code extracts a trailing ISO alpha-2 segment
  - a missing dump file aborts with CommandError
  - a full run creates entities, aliases, addresses, and identifiers
  - malformed lines and unusable records are counted, not fatal
  - --limit and --batch-size control the streaming loop
  - flush() dedupes repeated source_ids and re-runs are idempotent
  - progress and summary counts are written to stdout
"""

import io
import json

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from screening.management.commands.ingest_opensanctions import parse_country_code
from screening.models import (
    EntityAddress,
    EntityAlias,
    EntityIdentifier,
    SanctionedEntity,
)


def write_dump(tmp_path, lines):
    """Write a JSON-lines dump; each line is a dict or a raw string."""
    path = tmp_path / "entities.ftm.json"
    with open(path, "w", encoding="utf-8") as handle:
        for line in lines:
            if isinstance(line, dict):
                line = json.dumps(line)
            handle.write(line + "\n")
    return path


def person_record(source_id, name, **properties):
    """A minimal valid FtM Person record."""
    return {
        "id": source_id,
        "schema": "Person",
        "properties": {"name": [name], **properties},
    }


class TestParseCountryCode:
    """Trailing two-letter segments are trusted; anything else falls back."""

    def test_trailing_two_letter_segment_is_used(self):
        assert parse_country_code("Tverskaya 1, Moscow, RU", "us") == "ru"

    def test_no_valid_tail_falls_back_to_entity_country(self):
        assert parse_country_code("Tverskaya 1, Moscow", "ru") == "ru"

    def test_numeric_tail_is_not_a_country_code(self):
        assert parse_country_code("Collyer Quay, Singapore 049320", "sg") == "sg"


class TestMissingDump:
    def test_missing_dump_file_raises_command_error(self, tmp_path, db):
        with pytest.raises(CommandError):
            call_command("ingest_opensanctions", path=tmp_path / "nope.json")


class TestFullRun:
    """A complete record lands in all four tables with parsed field values."""

    def test_creates_entity_alias_address_identifier(self, tmp_path, db):
        path = write_dump(tmp_path, [
            person_record(
                "NK-putin",
                "Vladimir Putin",
                alias=["Vladimir Vladimirovich Putin"],
                address=["Tverskaya 1, Moscow, RU"],
                country=["ru"],
                passportNumber=["75NO123456"],
            ),
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)

        entity = SanctionedEntity.objects.get(source_id="NK-putin")
        assert entity.name == "Vladimir Putin"
        assert entity.entity_type == "person"

        assert list(entity.aliases.values_list("text", flat=True)) == [
            "Vladimir Vladimirovich Putin"
        ]

        address = entity.addresses.get()
        assert address.full_text == "Tverskaya 1, Moscow, RU"
        assert address.country_code == "ru"

        identifier = entity.identifiers.get()
        assert identifier.id_type == "passport"
        assert identifier.value_hash == EntityIdentifier.hash_value("75NO123456")

        out = stdout.getvalue()
        assert "Ingestion complete." in out
        assert "Entities created: 1" in out
        assert "Aliases created: 1" in out
        assert "Addresses created: 1" in out
        assert "Identifiers created: 1" in out

    def test_organization_schema_maps_to_organization_type(self, tmp_path, db):
        path = write_dump(tmp_path, [{
            "id": "NK-company",
            "schema": "Company",
            "properties": {"name": ["Acme Trading"], "registrationNumber": ["REG-1"]},
        }])
        call_command("ingest_opensanctions", path=path, stdout=io.StringIO())
        entity = SanctionedEntity.objects.get(source_id="NK-company")
        assert entity.entity_type == "organization"
        assert entity.identifiers.get().id_type == "business_reg"

    def test_progress_is_reported_every_thousand_records(self, tmp_path, db):
        path = write_dump(tmp_path, [
            person_record(f"NK-bulk-{i}", f"Person {i}") for i in range(1001)
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)
        assert "Processed 1,000 entities..." in stdout.getvalue()
        assert SanctionedEntity.objects.count() == 1001


class TestSkippedRecords:
    """Unusable input is counted and skipped, never fatal."""

    def test_malformed_json_lines_are_counted(self, tmp_path, db):
        path = write_dump(tmp_path, [
            "{not valid json",
            person_record("NK-ok", "Good Person"),
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)
        assert "Unparseable lines: 1" in stdout.getvalue()
        assert SanctionedEntity.objects.count() == 1

    def test_unknown_schema_is_skipped(self, tmp_path, db):
        path = write_dump(tmp_path, [
            {"id": "NK-vessel", "schema": "Vessel",
             "properties": {"name": ["Boaty McBoatface"]}},
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)
        assert "Skipped (schema not screened): 1" in stdout.getvalue()
        assert SanctionedEntity.objects.count() == 0

    def test_record_without_name_is_skipped(self, tmp_path, db):
        path = write_dump(tmp_path, [
            {"id": "NK-noname", "schema": "Person", "properties": {}},
            {"id": "NK-blankname", "schema": "Person",
             "properties": {"name": ["   "]}},
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)
        assert "Skipped (no name): 2" in stdout.getvalue()
        assert SanctionedEntity.objects.count() == 0

    def test_record_without_id_is_skipped(self, tmp_path, db):
        path = write_dump(tmp_path, [
            {"schema": "Person", "properties": {"name": ["Nameless"]}},
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)
        assert "Skipped (no name): 1" in stdout.getvalue()
        assert SanctionedEntity.objects.count() == 0

    def test_blank_lines_are_ignored(self, tmp_path, db):
        path = write_dump(tmp_path, [
            person_record("NK-ok", "Good Person"),
            "",
            "   ",
        ])
        call_command("ingest_opensanctions", path=path, stdout=io.StringIO())
        assert SanctionedEntity.objects.count() == 1


class TestLimitsAndBatching:
    def test_limit_stops_early(self, tmp_path, db):
        path = write_dump(tmp_path, [
            person_record(f"NK-{i}", f"Person {i}") for i in range(3)
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, limit=2, stdout=stdout)
        assert SanctionedEntity.objects.count() == 2
        assert "Entities created: 2" in stdout.getvalue()

    def test_batch_size_one_forces_multiple_flushes(self, tmp_path, db):
        path = write_dump(tmp_path, [
            person_record(f"NK-{i}", f"Person {i}") for i in range(3)
        ])
        call_command(
            "ingest_opensanctions", path=path, batch_size=1, stdout=io.StringIO()
        )
        assert SanctionedEntity.objects.count() == 3


class TestFlushDeduplication:
    """Repeated source_ids never produce duplicate rows."""

    def test_duplicate_source_id_within_one_batch_is_deduped(self, tmp_path, db):
        path = write_dump(tmp_path, [
            person_record("NK-dup", "First Version"),
            person_record("NK-dup", "Second Version"),
        ])
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)
        assert SanctionedEntity.objects.filter(source_id="NK-dup").count() == 1
        assert "Skipped (already ingested): 1" in stdout.getvalue()

    def test_rerun_over_same_dump_creates_no_duplicates(self, tmp_path, db):
        path = write_dump(tmp_path, [
            person_record(
                "NK-putin",
                "Vladimir Putin",
                alias=["Vladimir Vladimirovich Putin"],
                address=["Moscow, RU"],
                passportNumber=["75NO123456"],
            ),
        ])
        call_command("ingest_opensanctions", path=path, stdout=io.StringIO())
        stdout = io.StringIO()
        call_command("ingest_opensanctions", path=path, stdout=stdout)

        assert SanctionedEntity.objects.count() == 1
        assert EntityAlias.objects.count() == 1
        assert EntityAddress.objects.count() == 1
        assert EntityIdentifier.objects.count() == 1

        out = stdout.getvalue()
        assert "Entities created: 0" in out
        assert "Skipped (already ingested): 1" in out

    def test_flush_tolerates_entity_lost_to_a_concurrent_insert(self, db, monkeypatch):
        # bulk_create(ignore_conflicts=True) silently drops rows that hit a
        # conflict, and does not populate primary keys. If another process
        # inserts the same source_id between the "already ingested" check and
        # the bulk_create, the id read-back finds nothing; flush must skip that
        # record's children instead of crashing on a None entity id.
        from screening.management.commands.ingest_opensanctions import Command

        monkeypatch.setattr(
            SanctionedEntity.objects, "bulk_create", lambda *args, **kwargs: []
        )

        cmd = Command()
        cmd.counts = {
            "entities": 0,
            "aliases": 0,
            "addresses": 0,
            "identifiers": 0,
            "skipped_schema": 0,
            "skipped_no_name": 0,
            "skipped_duplicate": 0,
            "bad_lines": 0,
        }
        cmd.batch_size = 1000

        record = cmd.parse_entity(person_record(
            "NK-raced",
            "Raced Person",
            alias=["Raced Alias"],
            address=["Moscow, RU"],
            passportNumber=["75NO123456"],
        ))
        cmd.flush([record])

        assert SanctionedEntity.objects.count() == 0
        assert EntityAlias.objects.count() == 0
        assert EntityAddress.objects.count() == 0
        assert EntityIdentifier.objects.count() == 0
