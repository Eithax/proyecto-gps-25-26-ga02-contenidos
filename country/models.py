from django.db import models
import uuid


class Country(models.Model):
    # ID único
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Campos básicos para tabla diccionario
    name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        unique=True,
        help_text="Nombre completo del país"
    )

    # Códigos estándar
    iso_code = models.CharField(
        max_length=2,
        blank=False,
        null=False,
        unique=True,
        verbose_name="Código ISO",
        help_text="Código ISO 3166-1 alpha-2 (2 letras)"
    )

    iso_code_3 = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Código ISO-3",
        help_text="Código ISO 3166-1 alpha-3 (3 letras)"
    )

    # Información adicional útil
    continent = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('AF', 'África'),
            ('AS', 'Asia'),
            ('EU', 'Europa'),
            ('NA', 'América del Norte'),
            ('SA', 'América del Sur'),
            ('OC', 'Oceanía'),
            ('AN', 'Antártida'),
        ],
        help_text="Continente del país"
    )

    phone_code = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="Código telefónico internacional (ej: +34)"
    )

    currency_code = models.CharField(
        max_length=3,
        blank=True,
        null=True,
        help_text="Código de moneda ISO 4217 (ej: EUR, USD)"
    )

    currency_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Nombre de la moneda local"
    )

    # Bandera (opcional)
    flag_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de la bandera del país"
    )

    # Campos de estado
    is_active = models.BooleanField(
        default=True,
        help_text="Indica si el país está activo en el sistema"
    )

    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'countries'
        ordering = ['name']
        verbose_name = 'País'
        verbose_name_plural = 'Países'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['iso_code']),
            models.Index(fields=['continent']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.iso_code})"

    @property
    def artists_count(self):
        """Número total de artistas de este país"""
        return self.artists.count()

    @property
    def record_labels_count(self):
        """Número total de sellos discográficos de este país"""
        return self.record_labels.count()

    @property
    def full_info(self):
        """Información completa formateada"""
        info_parts = [self.name]
        if self.continent:
            continent_display = dict(self._meta.get_field('continent').choices).get(self.continent, '')
            info_parts.append(continent_display)
        if self.currency_code:
            info_parts.append(f"Moneda: {self.currency_code}")
        return " - ".join(info_parts)

    def save(self, *args, **kwargs):
        # Asegurar que el código ISO esté en mayúsculas
        if self.iso_code:
            self.iso_code = self.iso_code.upper()
        if self.iso_code_3:
            self.iso_code_3 = self.iso_code_3.upper()
        if self.currency_code:
            self.currency_code = self.currency_code.upper()

        super().save(*args, **kwargs)