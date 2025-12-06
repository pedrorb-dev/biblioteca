from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
import django.db.transaction as transaction
from django.core.exceptions import ValidationError

class Carrera(models.Model):
    id_carrera = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.id_carrera} - {self.nombre}"


class Alumno(models.Model):
    id_alumno = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=35)
    semestre = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    carrera = models.ForeignKey(Carrera, on_delete=models.CASCADE)

    @classmethod
    def changes(cls):
        try:
            with transaction.atomic():
                x = Alumno.objects.filter(
                    semestre__gt=9,
                    semestre__lte=12,
                )
                for alumno in x:
                    alumno.semestre = 9
                    alumno.save()
        except Exception as e:
            print(f"Error durante la actualización: {e}")
            


    def __str__(self):
        return f"{self.id_alumno} - {self.nombre}"


class Autor(models.Model):
    id_autor = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    nacionalidad = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.id_autor} - {self.nombre} - {self.nacionalidad}"


class Editorial(models.Model):
    id_editorial = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    pais = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.id_editorial} - {self.nombre}"


class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.id_categoria} - {self.nombre}"


class Libro(models.Model):
    id_libro = models.AutoField(primary_key=True)
    titulo = models.CharField(max_length=100)
    autor = models.ForeignKey(Autor, on_delete=models.SET_NULL, null=True)

    STATUS_DISPONIBLE = 'DISPONIBLE'
    STATUS_PRESTADO = 'PRESTADO'

    STATUS_CHOICES = [
        (STATUS_DISPONIBLE, 'Disponible'),
        (STATUS_PRESTADO, 'Prestado'),
    ]

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_DISPONIBLE)
    editorial = models.ForeignKey(Editorial, on_delete=models.SET_NULL, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    anio_publicacion = models.CharField(
        
        max_length=4,
        validators=[RegexValidator(r'^\d{4}$', 'Debe ser un año de 4 dígitos.')]
    )

    @classmethod
    def changes(cls):
        with transaction.atomic():
            x = Libro.objects.first()
            x.titulo = 'El principito - Editado'
            #y = 1/0  # Esto generará una excepción de división por cero
            try:
                x.save()
            except Exception as e:
                print(f"Error al guardar el libro: {e}")

    def __str__(self):
        return f"{self.id_libro} - {self.titulo}"


class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.id_usuario} - {self.nombre}"


class Historial(models.Model):
    id_historial = models.CharField(primary_key=True, max_length=25)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_prestamo = models.DateField()
    fecha_devolucion = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.id_historial} - Alumno: {self.alumno.nombre}"

class Prestamo(models.Model):
    id_prestamo = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    libro = models.ForeignKey(Libro, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    fecha_prestamo = models.DateField()
    fecha_devolucion = models.DateField(null=True, blank=True)
    STATUS_ACTIVO = 'ACTIVO'
    STATUS_DEVUELTO = 'DEVUELTO'
    STATUS_CHOICES = [
        (STATUS_ACTIVO, 'Activo'),
        (STATUS_DEVUELTO, 'Devuelto'),
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_ACTIVO)
    
    def __str__(self):
        return f"{self.id_prestamo} - Alumno: {self.alumno.nombre} - Libro: {self.libro.titulo} - Usuario: {self.usuario.nombre if self.usuario else 'Desconocido'} - Prestamo: {self.fecha_prestamo} - Devolución: {self.fecha_devolucion}"


class Sancion(models.Model):
    id_sancion = models.AutoField(primary_key=True)
    alumno = models.ForeignKey(Alumno, on_delete=models.CASCADE)
    motivo = models.CharField(max_length=100)
    fecha = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.id_sancion} - Alumno: {self.alumno.nombre}"
