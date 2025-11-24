from rest_framework import serializers
from .models import Artist


class ArtistSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para representación
    label = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()

    # Campos calculados
    is_signed = serializers.ReadOnlyField()
    public_social_media = serializers.ReadOnlyField()

    # Campos para escritura
    label_id = serializers.IntegerField(write_only=True)
    country_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Artist
        fields = [
            'id', 'name', 'bio', 'image_url', 'country', 'label',
            'socials', 'public_social_media', 'is_signed', 'created_at',
            'updated_at', 'label_id', 'country_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_label(self, obj):
        """Importación diferida para label"""
        if obj.label:
            from record_label.serializers import RecordLabelSerializer
            return RecordLabelSerializer(obj.label).data
        return None

    def get_country(self, obj):
        """Importación diferida para country"""
        if obj.country:
            from country.serializers import CountrySerializer
            return CountrySerializer(obj.country).data
        return None


class ArtistCreateSerializer(serializers.ModelSerializer):
    # label_id = serializers.UUIDField(required=False, allow_null=True)
    # country_id = serializers.UUIDField(required=False, allow_null=True)
    label_id = serializers.IntegerField(write_only=True)
    country_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Artist
        fields = [
            'id', 'name', 'bio', 'image_url', 'label_id',
            'country_id', 'socials'
        ]

    def validate_name(self, value):
        """Validar que el nombre no esté vacío"""
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        return value

    def validate_socials(self, value):
        """Validar que socials sea un diccionario"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Las redes sociales deben ser un diccionario")
        return value

    def create(self, validated_data):
        # Extraer IDs de relaciones
        label_id = validated_data.pop('label_id', None)
        country_id = validated_data.pop('country_id', None)

        # Obtener instancias de relaciones
        if label_id:
            try:
                from record_label.models import RecordLabel
                print(label_id)
                label = RecordLabel.objects.get(id=label_id)
                validated_data['label_id'] = label_id
            except RecordLabel.DoesNotExist:
                raise serializers.ValidationError({"label_id": "Sello discográfico no encontrado"})
        else:
            validated_data['label_id'] = None

        if country_id:
            try:
                from country.models import Country
                country = Country.objects.get(id=country_id)
                validated_data['country_id'] = country_id
            except Country.DoesNotExist:
                raise serializers.ValidationError({"country_id": "País no encontrado"})
        else:
            validated_data['country'] = None

        # Crear el artista
        artist = Artist.objects.create(**validated_data)
        return artist


class ArtistUpdateSerializer(serializers.ModelSerializer):
    # label_id = serializers.UUIDField(required=False, allow_null=True)
    # country_id = serializers.UUIDField(required=False, allow_null=True)
    label_id = serializers.IntegerField(write_only=True)
    country_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Artist
        fields = [
            'name', 'bio', 'image_url', 'label_id', 'country_id', 'socials'
        ]

    def validate_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        return value

    def validate_socials(self, value):
        if value and not isinstance(value, dict):
            raise serializers.ValidationError("Las redes sociales deben ser un diccionario")
        return value

    def update(self, instance, validated_data):
        # Manejar actualización de relaciones
        label_id = validated_data.pop('label_id', None)
        country_id = validated_data.pop('country_id', None)

        if label_id is not None:
            if label_id:
                try:
                    from record_label.models import RecordLabel
                    label = RecordLabel.objects.get(id=label_id)
                    instance.label_id = label_id
                except RecordLabel.DoesNotExist:
                    raise serializers.ValidationError({"label_id": "Sello discográfico no encontrado"})
            else:
                instance.label_id = None

        if country_id is not None:
            if country_id:
                try:
                    from country.models import Country
                    country = Country.objects.get(id=country_id)
                    instance.country = country
                except Country.DoesNotExist:
                    raise serializers.ValidationError({"country_id": "País no encontrado"})
            else:
                instance.country = None

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance