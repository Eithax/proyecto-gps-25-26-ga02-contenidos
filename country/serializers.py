from rest_framework import serializers
from .models import Country


class CountrySerializer(serializers.ModelSerializer):
    # Campos calculados
    artists_count = serializers.ReadOnlyField()
    record_labels_count = serializers.ReadOnlyField()
    full_info = serializers.ReadOnlyField()

    class Meta:
        model = Country
        fields = [
            'id', 'name', 'iso_code', 'iso_code_3', 'continent',
            'phone_code', 'currency_code', 'currency_name', 'flag_url',
            'is_active', 'artists_count', 'record_labels_count', 'full_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CountryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'name', 'iso_code', 'iso_code_3', 'continent',
            'phone_code', 'currency_code', 'currency_name', 'flag_url',
            'is_active'
        ]

    def validate_name(self, value):
        """Validar que el nombre no esté vacío"""
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        return value

    def validate_iso_code(self, value):
        """Validar formato del código ISO"""
        if not value or len(value) != 2:
            raise serializers.ValidationError("El código ISO debe tener exactamente 2 caracteres")
        return value.upper()

    def validate_iso_code_3(self, value):
        """Validar formato del código ISO-3"""
        if value and len(value) != 3:
            raise serializers.ValidationError("El código ISO-3 debe tener exactamente 3 caracteres")
        return value.upper() if value else value

    def validate_currency_code(self, value):
        """Validar formato del código de moneda"""
        if value and len(value) != 3:
            raise serializers.ValidationError("El código de moneda debe tener exactamente 3 caracteres")
        return value.upper() if value else value

    def create(self, validated_data):
        # Verificar duplicados
        iso_code = validated_data.get('iso_code')
        name = validated_data.get('name')

        if Country.objects.filter(iso_code=iso_code).exists():
            raise serializers.ValidationError(
                {"iso_code": "Ya existe un país con este código ISO"}
            )

        if Country.objects.filter(name=name).exists():
            raise serializers.ValidationError(
                {"name": "Ya existe un país con este nombre"}
            )

        # Crear el país
        country = Country.objects.create(**validated_data)
        return country


class CountryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'name', 'iso_code', 'iso_code_3', 'continent',
            'phone_code', 'currency_code', 'currency_name', 'flag_url',
            'is_active'
        ]

    def validate_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        return value

    def validate_iso_code(self, value):
        if value and len(value) != 2:
            raise serializers.ValidationError("El código ISO debe tener exactamente 2 caracteres")
        return value.upper()

    def validate_iso_code_3(self, value):
        if value and len(value) != 3:
            raise serializers.ValidationError("El código ISO-3 debe tener exactamente 3 caracteres")
        return value.upper() if value else value

    def validate_currency_code(self, value):
        if value and len(value) != 3:
            raise serializers.ValidationError("El código de moneda debe tener exactamente 3 caracteres")
        return value.upper() if value else value

    def update(self, instance, validated_data):
        # Verificar duplicados (excluyendo el actual)
        iso_code = validated_data.get('iso_code')
        name = validated_data.get('name')

        if iso_code and iso_code != instance.iso_code:
            if Country.objects.filter(iso_code=iso_code).exclude(id=instance.id).exists():
                raise serializers.ValidationError(
                    {"iso_code": "Ya existe un país con este código ISO"}
                )

        if name and name != instance.name:
            if Country.objects.filter(name=name).exclude(id=instance.id).exists():
                raise serializers.ValidationError(
                    {"name": "Ya existe un país con este nombre"}
                )

        # Actualizar los campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance