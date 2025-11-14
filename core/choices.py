from django.db import models

class ReleaseStatus(models.TextChoices):
    DRAFT = 'draft', 'Borrador'
    PUBLISHED = 'published', 'Publicado'
    RETIRED = 'retired', 'Retirado'

class Language(models.TextChoices):
    # ISO 639-1 codes
    SPANISH = 'es', 'Español'
    ENGLISH = 'en', 'Inglés'
    FRENCH = 'fr', 'Francés'
    GERMAN = 'de', 'Alemán'
    ITALIAN = 'it', 'Italiano'
    PORTUGUESE = 'pt', 'Portugués'
    JAPANESE = 'ja', 'Japonés'
    KOREAN = 'ko', 'Coreano'
    CHINESE = 'zh', 'Chino'
    RUSSIAN = 'ru', 'Ruso'
    ARABIC = 'ar', 'Árabe'
    HINDI = 'hi', 'Hindi'

    @classmethod
    def get_by_region(cls, region):
        region_map = {
            'europa': [cls.SPANISH, cls.ENGLISH, cls.FRENCH, cls.GERMAN, cls.ITALIAN],
            'asia': [cls.JAPANESE, cls.KOREAN, cls.CHINESE],
            'south_america': [cls.SPANISH, cls.PORTUGUESE],
        }
        return region_map.get(region, [])