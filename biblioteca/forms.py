from django import forms
from .models import *

class LibroForm(forms.ModelForm):   
    class Meta:   
        model = Libro   
        fields = '__all__'

class AlumnoForm(forms.ModelForm):
    class Meta:
        model = Alumno
        fields = '__all__'

class AutorForm(forms.ModelForm):
    class Meta:
        model = Autor
        fields = '__all__'

class CarreraForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = '__all__'

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = '__all__'

class EditorialForm(forms.ModelForm):
    class Meta:
        model = Editorial
        fields = '__all__'

class HistorialForm(forms.ModelForm):
    class Meta:
        model = Historial
        fields = '__all__'

class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = '__all__'  

class PrestamoForm(forms.ModelForm):
    class Meta:
        model = Prestamo
        fields = '__all__'

class SancionForm(forms.ModelForm):
    class Meta:
        model = Sancion
        fields = '__all__'

