from rest_framework import serializers
from .models import Genre

ERROR_MESSAGE = "Género padre no encontrado"


class GenreSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para representación
    parent_genre_name = serializers.CharField(source='parent_genre.name', read_only=True)

    # Campos calculados
    is_subgenre = serializers.ReadOnlyField()
    full_hierarchy = serializers.ReadOnlyField()
    tracks_count = serializers.ReadOnlyField()
    albums_count = serializers.ReadOnlyField()

    # Campos para escritura
    parent_genre_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Genre
        fields = [
            'genre_id', 'name', 'description', 'parent_genre', 'parent_genre_name',
            'is_subgenre', 'full_hierarchy', 'tracks_count', 'albums_count',
            'created_at', 'updated_at', 'parent_genre_id'
        ]
        read_only_fields = ['genre_id', 'created_at', 'updated_at']
        depth = 1  # Para incluir datos del parent_genre


class GenreCreateSerializer(serializers.ModelSerializer):
    parent_genre_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Genre
        fields = [
            'genre_id', 'name', 'description', 'parent_genre_id'
        ]

    def validate_name(self, value):
        """Validar que el nombre no esté vacío y sea único"""
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")

        # Verificar unicidad (excluyendo el actual en updates)
        if self.instance:
            if Genre.objects.filter(name=value).exclude(genre_id=self.instance.genre_id).exists():
                raise serializers.ValidationError("Ya existe un género con este nombre")
        else:
            if Genre.objects.filter(name=value).exists():
                raise serializers.ValidationError("Ya existe un género con este nombre")

        return value

    def validate_parent_genre_id(self, value):
        """Validar que el género padre existe y no crea ciclos"""
        if value:
            try:
                parent_genre = Genre.objects.get(genre_id=value)

                # Prevenir ciclos (un género no puede ser padre de sí mismo)
                if self.instance and self.instance.genre_id == value:
                    raise serializers.ValidationError("Un género no puede ser padre de sí mismo")

                # Prevenir jerarquías demasiado profundas (opcional)
                current = parent_genre
                depth = 1
                while current.parent_genre:
                    current = current.parent_genre
                    depth += 1
                    if depth >= 5:  # Límite de profundidad
                        raise serializers.ValidationError("La jerarquía de géneros es demasiado profunda")

            except Genre.DoesNotExist:
                raise serializers.ValidationError(ERROR_MESSAGE)

        return value

    def create(self, validated_data):
        # Extraer parent_genre_id
        parent_genre_id = validated_data.pop('parent_genre_id', None)

        # Obtener instancia del género padre
        if parent_genre_id:
            try:
                parent_genre = Genre.objects.get(genre_id=parent_genre_id)
                validated_data['parent_genre'] = parent_genre
            except Genre.DoesNotExist:
                raise serializers.ValidationError({"parent_genre_id": ERROR_MESSAGE})
        else:
            validated_data['parent_genre'] = None

        # Crear el género
        genre = Genre.objects.create(**validated_data)
        return genre


class GenreUpdateSerializer(serializers.ModelSerializer):
    parent_genre_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Genre
        fields = [
            'name', 'description', 'parent_genre_id'
        ]

    def validate_name(self, value):
        if value and not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")
        return value

    def validate_parent_genre_id(self, value):
        """Validar que el género padre existe y no crea ciclos"""
        if value is not None:  # Incluye None (para eliminar parent)
            if value:  # Si se proporciona un UUID
                try:
                    parent_genre = Genre.objects.get(genre_id=value)

                    # Prevenir ciclos
                    if self.instance.genre_id == value:
                        raise serializers.ValidationError("Un género no puede ser padre de sí mismo")

                    # Prevenir que un género sea padre de sus propios descendientes
                    def is_descendant(genre, potential_parent):
                        """Verifica si un género es descendiente de otro"""
                        current = genre.parent_genre
                        while current:
                            if current.genre_id == potential_parent.genre_id:
                                return True
                            current = current.parent_genre
                        return False

                    if is_descendant(parent_genre, self.instance):
                        raise serializers.ValidationError("No se puede crear un ciclo en la jerarquía de géneros")

                except Genre.DoesNotExist:
                    raise serializers.ValidationError(ERROR_MESSAGE)

        return value

    def update(self, instance, validated_data):
        # Manejar actualización del parent_genre
        parent_genre_id = validated_data.pop('parent_genre_id', None)

        if parent_genre_id is not None:
            if parent_genre_id:
                try:
                    parent_genre = Genre.objects.get(genre_id=parent_genre_id)
                    instance.parent_genre = parent_genre
                except Genre.DoesNotExist:
                    raise serializers.ValidationError({"parent_genre_id": ERROR_MESSAGE})
            else:
                instance.parent_genre = None

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
