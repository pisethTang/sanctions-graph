from django.db import models

import hashlib 


class Agent(models.Model):
    """An education agent being screened."""
    name = models.CharField(max_length=255, db_index=True)
    aliases = models.JSONField(default=list, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name




class SanctionedEntity(models.Model):
    """A person or roganization"""
    ENTITY_TYPES = [
        ("person", "Person"),
        ("organization", "Organization"),
    ]
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, db_index=True)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    source_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["entity_type"]),
        ]
    def __str__(self) -> str:
        return f"{self.name} ({self.entity_type})"


class EntityAlias(models.Model):
    """An alias (name variation) for a sanctioned entity."""
    entity = models.ForeignKey(
        SanctionedEntity, on_delete=models.CASCADE, related_name="aliases"
    )

    text = models.CharField(max_length=255, db_index=True)
    language = models.CharField(max_length=10, blank=True)


    class Meta:
        indexes = [
            models.Index(fields=["text"])
        ]



class EntityAddress(models.Model):
    """An address linked to a sanctioned entity."""
    entity = models.ForeignKey(
        SanctionedEntity, on_delete=models.CASCADE, related_name="addresses"
    )


    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    full_text = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['country_code']),
        ]




class EntityIdentifier(models.Model):
    """A passport, tax ID, or business registration number."""
    ID_TYPES = [
        ("passport", "Passport"),
        ("tax_id", "Tax ID"),
        ("business_reg", "Business Registration"),
        ("other", "Other"),
    ]


    entity = models.ForeignKey(
        SanctionedEntity, on_delete=models.CASCADE, related_name="identifiers"
    )

    id_type = models.CharField(max_length=20, choices=ID_TYPES)
    value_hash = models.CharField(max_length=64, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["id_type", "value_hash"])
        ]

    @staticmethod
    def hash_value(raw_value: str) -> str:
        return hashlib.sha256(raw_value.strip().upper().encode()).hexdigest()


class ScreeningCase(models.Model):
    """A single screening run for an agent."""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('resolved', 'Resolved'),
    ]
    agent = models.ForeignKey(
        Agent, on_delete=models.CASCADE, related_name='cases'
    )
    risk_score = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    network_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Match(models.Model):
    """A single hit found during screening."""
    MATCH_TYPES = [
        ('identifier_exact', 'Identifier Exact'),
        ('name_exact', 'Name Exact'),
        ('name_fuzzy', 'Name Fuzzy'),
        ('address_fuzzy', 'Address Fuzzy'),
        ('network_2nd_degree', '2nd Degree Network'),
    ]
    case = models.ForeignKey(
        ScreeningCase, on_delete=models.CASCADE, related_name='matches'
    )
    entity = models.ForeignKey(
        SanctionedEntity, on_delete=models.CASCADE
    )
    match_type = models.CharField(max_length=20, choices=MATCH_TYPES)
    confidence = models.IntegerField()
    explanation = models.TextField(blank=True)
    resolved = models.BooleanField(default=False)
    resolution = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)




# | Model              | Purpose                                                                                         |
# | ------------------ | ----------------------------------------------------------------------------------------------- |
# | `Agent`            | The education agent being screened. Stores name, aliases, DOB, nationality.                     |
# | `SanctionedEntity` | A PEP or sanctioned person/org from OpenSanctions. `source_id` is the OpenSanctions UUID.       |
# | `EntityAlias`      | Name variations. We will fuzzy-match agent names against these.                                 |
# | `EntityAddress`    | Physical addresses. `full_text` is for `pg_trgm` fuzzy matching.                                |
# | `EntityIdentifier` | Hashed passport/tax IDs. Exact-match only.                                                      |
# | `ScreeningCase`    | One screening run. Stores the final risk score and a JSON snapshot of the graph for audit.      |
# | `Match`            | Each individual hit found during screening. Officers mark these as false positive or confirmed. |
