from rest_framework import serializers
from .models import RecordLabel


class RecordLabelSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para representación
    country = serializers.SerializerMethodField()

    # Campos calculados
    artists_count = serializers.ReadOnlyField()
    albums_count = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    # Campos para escritura
    country_id = serializers.UUIDField(write_only=True, required=True)

    class Meta:
        model = RecordLabel
        fields = [
            'id', 'name', 'country', 'contact', 'web',
            'artists_count', 'albums_count', 'is_active',
            'created_at', 'updated_at', 'country_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_country(self, obj):
        """Importación diferida para country"""
        from country.serializers import CountrySerializer
        return CountrySerializer(obj.country).data


class RecordLabelCreateSerializer(serializers.ModelSerializer):
    country_id = serializers.UUIDField(required=True)

    class Meta:
        model = RecordLabel
        fields = [
            'id', 'name', 'country_id', 'contact', 'web'
        ]

    def validate_name(self, value):
        """Validar que el nombre no esté vacío"""
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        return value

    def validate_contact(self, value):
        """Validar formato de email si se proporciona"""
        if value and '@' not in value:
            raise serializers.ValidationError("Formato de email inválido")
        return value

    def validate_web(self, value):
        """Validar formato de URL si se proporciona"""
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("La URL debe comenzar con http:// o https://")
        return value

    def create(self, validated_data):
        # Extraer country_id
        country_id = validated_data.pop('country_id')

        # Obtener instancia del país
        try:
            from country.models import Country
            country = Country.objects.get(id=country_id)
            validated_data['country'] = country
        except Country.DoesNotExist:
            raise serializers.ValidationError({"country_id": "País no encontrado"})

        # Verificar duplicados (mismo nombre)
        name = validated_data.get('name')
        if RecordLabel.objects.filter(name=name).exists():
            raise serializers.ValidationError(
                {"name": "Ya existe un sello discográfico con este nombre"}
            )

        # Crear el sello discográfico
        record_label = RecordLabel.objects.create(**validated_data)
        return record_label


class RecordLabelUpdateSerializer(serializers.ModelSerializer):
    country_id = serializers.UUIDField(required=False)

    class Meta:
        model = RecordLabel
        fields = [
            'name', 'country_id', 'contact', 'web'
        ]

    def validate_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        return value

    def validate_contact(self, value):
        if value and '@' not in value:
            raise serializers.ValidationError("Formato de email inválido")
        return value

    def validate_web(self, value):
        if value and not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("La URL debe comenzar con http:// o https://")
        return value

    def update(self, instance, validated_data):
        # Manejar actualización del país si se proporciona
        country_id = validated_data.pop('country_id', None)

        if country_id is not None:
            try:
                from country.models import Country
                country = Country.objects.get(id=country_id)
                instance.country = country
            except Country.DoesNotExist:
                raise serializers.ValidationError({"country_id": "País no encontrado"})

        # Verificar duplicados de nombre (excluyendo el actual)
        name = validated_data.get('name')
        if name and name != instance.name:
            if RecordLabel.objects.filter(name=name).exclude(label_id=instance.label_id).exists():
                raise serializers.ValidationError(
                    {"name": "Ya existe un sello discográfico con este nombre"}
                )

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance