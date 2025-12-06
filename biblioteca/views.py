from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Libro
from .forms import LibroForm
# Create your views here.

def home(request):
    return render(request, 'paginas/home.html')

def libros(request):
    libros = Libro.objects.all()
    return render(request, 'libros/index.html', {'libros': libros})

def crear_libro(request):
    formulario = LibroForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('libros')
    return render(request, 'libros/crear.html', {'formulario': formulario})


def editar_libro(request, id):
    libro = Libro.objects.get(id_libro=id)  
    formulario = LibroForm(request.POST or None, request.FILES or None, instance=libro)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('libros')
    return render(request, 'libros/editar.html', {'formulario': formulario})

def eliminar_libro(request, id):
    try:
        libro = Libro.objects.get(id_libro=id)
        libro.delete()
        return redirect('libros')
    except Libro.DoesNotExist:
        return HttpResponse("El libro no existe")

from .models import Alumno
from .forms import AlumnoForm

def alumnos(request):
    alumnos = Alumno.objects.all()
    return render(request, 'alumnos/index.html', {'alumnos': alumnos})

def crear_alumno(request):
    formulario = AlumnoForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('alumnos')
    return render(request, 'alumnos/crear.html', {'formulario': formulario})

def editar_alumno(request, id):
    alumno = Alumno.objects.get(id_alumno=id)  
    formulario = AlumnoForm(request.POST or None, request.FILES or None, instance=alumno)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('alumnos')
    return render(request, 'alumnos/editar.html', {'formulario': formulario})

def eliminar_alumno(request, id):
    alumno = Alumno.objects.get(id_alumno=id)
    alumno.delete()
    return redirect('alumnos')

from .models import Autor
from .forms import AutorForm

def autores(request):
    autores = Autor.objects.all()
    return render(request, 'autores/index.html', {'autores': autores})

def crear_autor(request):
    formulario = AutorForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('autores')
    return render(request, 'autores/crear.html', {'formulario': formulario})

def editar_autor(request, id):
    autor = Autor.objects.get(id_autor=id)  
    formulario = AutorForm(request.POST or None, request.FILES or None, instance=autor)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('autores')
    return render(request, 'autores/editar.html', {'formulario': formulario})

def eliminar_autor(request, id):
    autor = Autor.objects.get(id_autor=id)
    autor.delete()
    return redirect('autores')

from .models import Carrera
from .forms import CarreraForm

def carreras(request):
    carreras = Carrera.objects.all()
    return render(request, 'carreras/index.html', {'carreras': carreras})

def crear_carrera(request):
    formulario = CarreraForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('carreras')
    return render(request, 'carreras/crear.html', {'formulario': formulario})   

def editar_carrera(request, id):
    carrera = Carrera.objects.get(id_carrera=id)  
    formulario = CarreraForm(request.POST or None, request.FILES or None, instance=carrera)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('carreras')
    return render(request, 'carreras/editar.html', {'formulario': formulario})

def eliminar_carrera(request, id):
    carrera = Carrera.objects.get(id_carrera=id)
    carrera.delete()
    return redirect('carreras')

from .models import Categoria
from .forms import CategoriaForm    

def categorias(request):
    categorias = Categoria.objects.all()
    return render(request, 'categorias/index.html', {'categorias': categorias})

def crear_categoria(request):
    formulario = CategoriaForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('categorias')
    return render(request, 'categorias/crear.html', {'formulario': formulario})

def editar_categoria(request, id):
    categoria = Categoria.objects.get(id_categoria=id)  
    formulario = CategoriaForm(request.POST or None, request.FILES or None, instance=categoria)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('categorias')
    return render(request, 'categorias/editar.html', {'formulario': formulario})

def eliminar_categoria(request, id):
    categoria = Categoria.objects.get(id_categoria=id)
    categoria.delete()
    return redirect('categorias')

from .models import Editorial
from .forms import EditorialForm

def editoriales(request):
    editoriales = Editorial.objects.all()
    return render(request, 'editoriales/index.html', {'editoriales': editoriales})

def crear_editorial(request):
    formulario = EditorialForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('editoriales')
    return render(request, 'editoriales/crear.html', {'formulario': formulario})

def editar_editorial(request, id):
    editorial = Editorial.objects.get(id_editorial=id)  
    formulario = EditorialForm(request.POST or None, request.FILES or None, instance=editorial)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('editoriales')
    return render(request, 'editoriales/editar.html', {'formulario': formulario})

def eliminar_editorial(request, id):
    editorial = Editorial.objects.get(id_editorial=id)
    editorial.delete()
    return redirect('editoriales')

from .models import Historial
from .forms import HistorialForm

def historiales(request):
    historiales = Historial.objects.all()
    return render(request, 'historiales/index.html', {'historiales': historiales})  

def crear_historial(request):
    formulario = HistorialForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('historiales')
    return render(request, 'historiales/crear.html', {'formulario': formulario})

def editar_historial(request, id):
    historial = Historial.objects.get(id_historial=id)  
    formulario = HistorialForm(request.POST or None, request.FILES or None, instance=historial)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('historiales')
    return render(request, 'historiales/editar.html', {'formulario': formulario})

def eliminar_historial(request, id):
    historial = Historial.objects.get(id_historial=id)
    historial.delete()
    return redirect('historiales')

from .models import Usuario
from .forms import UsuarioForm

def usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios/index.html', {'usuarios': usuarios})

def crear_usuario(request):
    formulario = UsuarioForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('usuarios')
    return render(request, 'usuarios/crear.html', {'formulario': formulario})

def editar_usuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)  
    formulario = UsuarioForm(request.POST or None, request.FILES or None, instance=usuario)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('usuarios')
    return render(request, 'usuarios/editar.html', {'formulario': formulario})

def eliminar_usuario(request, id):
    usuario = Usuario.objects.get(id_usuario=id)
    usuario.delete()
    return redirect('usuarios')

from .models import Prestamo
from .forms import PrestamoForm     

def prestamos(request):
    prestamos = Prestamo.objects.all()
    return render(request, 'prestamos/index.html', {'prestamos': prestamos})    

def crear_prestamo(request):
    formulario = PrestamoForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('prestamos')
    return render(request, 'prestamos/crear.html', {'formulario': formulario})

def editar_prestamo(request, id):
    prestamo = Prestamo.objects.get(id_prestamo=id)  
    formulario = PrestamoForm(request.POST or None, request.FILES or None, instance=prestamo)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('prestamos')
    return render(request, 'prestamos/editar.html', {'formulario': formulario})

def eliminar_prestamo(request, id):
    prestamo = Prestamo.objects.get(id_prestamo=id)
    prestamo.delete()
    return redirect('prestamos')

from .models import Sancion
from .forms import SancionForm

def sanciones(request):
    sanciones = Sancion.objects.all()
    return render(request, 'sanciones/index.html', {'sanciones': sanciones})

def crear_sancion(request):
    formulario = SancionForm(request.POST or None, request.FILES or None)
    if formulario.is_valid():
        formulario.save()
        return redirect('sanciones')
    return render(request, 'sanciones/crear.html', {'formulario': formulario})

def editar_sancion(request, id):
    sancion = Sancion.objects.get(id_sancion=id)  
    formulario = SancionForm(request.POST or None, request.FILES or None, instance=sancion)
    if formulario.is_valid() and request.method == 'POST':
        formulario.save()
        return redirect('sanciones')
    return render(request, 'sanciones/editar.html', {'formulario': formulario})

def eliminar_sancion(request, id):
    sancion = Sancion.objects.get(id_sancion=id)
    sancion.delete()
    return redirect('sanciones')


from django.contrib.auth.models import User, Permission, Group

def crear_usuario():
    usuario, creado = User.objects.get_or_create(username='ususa')
    if creado:
        usuario.set_password('sistemas')
        usuario.is_staff = True
        usuario.save()
        asignar_grupo(usuario)
    return usuario

def crear_usuario_admin():
    usuario, creado = User.objects.get_or_create(username='admnistrador24')
    if creado:
        usuario.set_password('1234')
        usuario.is_staff = True
        usuario.save()
        asignar_grupo(usuario)
    return usuario
    

def asignar_grupo(usuario):
    if isinstance(usuario, str):
        usuario = User.objects.get(username=usuario)

    grupo = None
    grupo1, creado = Group.objects.get_or_create(name='Bibliotecarios')
    grupo2, creado = Group.objects.get_or_create(name='Bibliotecarios_Admin')

    if usuario.username.startswith('usu'):
        permisos = Permission.objects.filter(codename__in=[
            'view_libro', 'view_alumno', 'view_autor', 'view_carrera',
            'view_categoria', 'view_editorial', 'view_historial',
            'view_usuario', 'view_prestamo', 'view_sancion',
        ])
        grupo1.permissions.set(permisos)
        grupo = grupo1
    elif usuario.username.startswith('adm'):
        permisos = Permission.objects.all()
        grupo2.permissions.set(permisos)
        grupo = grupo2

    usuario.groups.add(grupo)
    usuario.save()

    return grupo
    
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .procedimientos import ProcedimientosBiblioteca
import json

@require_http_methods(["GET"])
def reporte_prestamos_view(request):
    """Vista que usa el procedimiento almacenado"""
    try:
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        resultado = ProcedimientosBiblioteca.generar_reporte_prestamos_carrera(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        return JsonResponse(resultado)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# En biblioteca/views.py
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from .procedimientos import ProcedimientosBiblioteca

@login_required
def panel_procedimientos(request):
    """Panel principal para ejecutar procedimientos"""
    context = {
        'procedimientos': [
            {
                'id': 'reporte_carreras',
                'nombre': 'Reporte de Préstamos por Carrera',
                'descripcion': 'Muestra estadísticas de préstamos agrupados por carrera',
                'icono': 'fas fa-chart-bar',
                'color': 'primary'
            },
            {
                'id': 'libros_populares',
                'nombre': 'Libros Más Populares',
                'descripcion': 'Lista los libros más prestados en la biblioteca',
                'icono': 'fas fa-book',
                'color': 'success'
            }
        ]
    }
    return render(request, 'biblioteca/panel_procedimientos.html', context)

@login_required
def ejecutar_procedimiento(request, procedimiento_id):
    """Ejecuta un procedimiento específico"""
    resultado = None
    fechas_form = None
    
    if request.method == 'POST':
        if procedimiento_id == 'reporte_carreras':
            # Obtener fechas del formulario
            fecha_inicio = request.POST.get('fecha_inicio')
            fecha_fin = request.POST.get('fecha_fin')
            
            if fecha_inicio and fecha_fin:
                resultado = ProcedimientosBiblioteca.obtener_reporte_carreras_visual(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )
            else:
                # Usar valores por defecto (últimos 30 días)
                fecha_fin = datetime.now().date()
                fecha_inicio = fecha_fin - timedelta(days=30)
                resultado = ProcedimientosBiblioteca.obtener_reporte_carreras_visual(
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin
                )
                
        elif procedimiento_id == 'libros_populares':
            limite = request.POST.get('limite', 10)
            resultado = ProcedimientosBiblioteca.obtener_libros_populares_visual(
                limite=int(limite)
            )
    
    context = {
        'procedimiento_id': procedimiento_id,
        'resultado': resultado,
        'fecha_actual': datetime.now().date()
    }
    
    return render(request, 'biblioteca/resultado_procedimiento.html', context)