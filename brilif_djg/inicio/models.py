from django.db import models
from django.urls import reverse
import re

# Modelo para tipos de combustibles
class Combustible(models.TextChoices):
    DIESEL = 'Diesel', 'Diesel'
    BENCINA = 'Bencina', 'Bencina'
    ELECTRICO = 'Eléctrico', 'Eléctrico'

# Modelo base para tipos
class TipoBase(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.nombre

# Tipos específicos para cada categoría
class TipoGruaHorquilla(TipoBase):
    class Meta:
        verbose_name = "Tipo de Grua Horquilla"
        verbose_name_plural = "Tipos de Gruas Horquillas"

class TipoAlzaHombre(TipoBase):
    class Meta:
        verbose_name = "Tipo de Alza Hombre"
        verbose_name_plural = "Tipos de Alza Hombres"

class TipoBrazoArticulado(TipoBase):
    class Meta:
        verbose_name = "Tipo de Brazo Articulado"
        verbose_name_plural = "Tipos de Brazos Articulados"

class TipoPlataformaDeElevacion(TipoBase):
    class Meta:
        verbose_name = "Tipo de Plataforma de Elevación"
        verbose_name_plural = "Tipos de Plataformas de Elevación"

# Modelo base para equipos
class EquipoBase(models.Model):
    producto = models.OneToOneField('Producto', on_delete=models.CASCADE)
    combustible = models.CharField(max_length=50, choices=Combustible.choices)
    modelo = models.CharField(max_length=50)
    notas = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Modelos específicos para cada equipo
class AlzaHombre(EquipoBase):
    tipo = models.ForeignKey(TipoAlzaHombre, on_delete=models.PROTECT)
    tamaño = models.CharField(max_length=50)
    potencia_compactacion = models.CharField(max_length=50)
    kilowatts = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

class BrazoArticulado(EquipoBase):
    tipo = models.ForeignKey(TipoBrazoArticulado, on_delete=models.PROTECT)
    capacidad = models.CharField(max_length=50)

class GruaHorquilla(EquipoBase):
    tipo = models.ForeignKey(TipoGruaHorquilla, on_delete=models.PROTECT)
    profundidad = models.DecimalField(max_digits=5, decimal_places=2)

class PlataformaDeElevacion(EquipoBase):
    tipo = models.ForeignKey(TipoPlataformaDeElevacion, on_delete=models.PROTECT)
    capacidad = models.CharField(max_length=50)
    tamaño = models.CharField(max_length=50)

# El modelo Producto permanece igual pero actualizado para reflejar las relaciones
class Producto(models.Model):
    DISPONIBLE = 'Disponible'
    NO_DISPONIBLE = 'No disponible'
    EN_ARRIENDO = 'En arriendo'
    PARA_IMPORTAR = 'Para Importar'
    ESTADO_CHOICES = [
        (DISPONIBLE, 'Disponible'),
        (NO_DISPONIBLE, 'No disponible'),
        (EN_ARRIENDO, 'En arriendo'),
        (PARA_IMPORTAR, 'Para Importar'),
    ]

    VENTA = 'Venta'
    ARRIENDO = 'Arriendo'
    CATEGORIA_CHOICES = [
        (VENTA, 'Venta'),
        (ARRIENDO, 'Arriendo'),
    ]
    COMBUSTIBLE_CHOICES = [
        ('Gasolina', 'Gasolina'),
        ('Diesel', 'Diesel'),
        ('Eléctrico', 'Eléctrico'),
    ]
    combustible = models.CharField(
        max_length=20,
        choices=COMBUSTIBLE_CHOICES,
        default='Gasolina'
    )
    PROCESOS_CHOICES = [
        ('GRUA_HORQUILLA', 'Grua Horquilla'),
        ('ALZA_HOMBRE', 'Alza Hombre'),
        ('BRAZO_ARTICULADO', 'Brazo Articulado'),
        ('PLATAFORMA_DE_ELEVACION', 'Plataforma de Elevación'),
    ]

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    imagen_1 = models.ImageField(upload_to='productos/')
    imagen_2 = models.ImageField(upload_to='productos/', null=True, blank=True)
    imagen_3 = models.ImageField(upload_to='productos/', null=True, blank=True)
    imagen_4 = models.ImageField(upload_to='productos/', null=True, blank=True)
    imagen_5 = models.ImageField(upload_to='productos/', null=True, blank=True)
    video_url = models.CharField(max_length=200)
    cantidad_me_gusta = models.PositiveIntegerField(default=0)
    precio = models.DecimalField(max_digits=10, decimal_places=0, null=True, blank=True)
    enlace_detalles = models.URLField(blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default=DISPONIBLE)
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, default=VENTA)
    procesos = models.CharField(max_length=50, choices=PROCESOS_CHOICES)

    def save(self, *args, **kwargs):
        youtube_regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
        match = re.search(youtube_regex, self.video_url)
        if match:
            self.video_url = match.group(1)

        if self.categoria == self.ARRIENDO:
            self.precio = None
        
        super().save(*args, **kwargs)

    def get_video_thumbnail(self):
        return f'https://img.youtube.com/vi/{self.video_url}/0.jpg'
    
    def __str__(self):
        return self.nombre