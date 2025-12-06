import io
import os
import zipfile
import tempfile
from datetime import datetime
from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.core.management import call_command
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.urls import path, reverse
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from .models import *
from django.conf import settings
import subprocess    
from import_export.admin import ImportExportModelAdmin  
from django.template.response import TemplateResponse
from django.shortcuts import redirect

# Register your models here.

admin.site.site_header="Sistema ITCG"
admin.site.site_title="Sistema Gestor de Biblioteca"
admin.site.index_title="Administración Biblioteca"
ADMIN_GROUP_NAME = 'Bibliotecarios_Admin' 

class MyAdminSite(AdminSite):
    site_header = 'Administración - Biblioteca'
    site_title = 'Administración Biblioteca'
    index_title = 'Panel de Administración Biblioteca'
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('backup-db/', self.admin_view(self.backup_db_view), name='backup-db'),
            path('restore-db/', self.admin_view(self.restore_db_view), name='restore-db'),
            path('procedimientos/', self.admin_view(self.procedimientos_view), name='procedimientos'),
            path('procedimientos/ejecutar/<str:procedimiento_id>/', self.admin_view(self.ejecutar_procedimiento_view), name='ejecutar_procedimiento'),
            path('procedimientos/resultado/', self.admin_view(self.resultado_procedimiento_view), name='resultado_procedimiento'),
        ]
        return my_urls + urls

    def _get_mysql_settings(self):
        db = settings.DATABASES.get('default', {})
        engine = db.get('ENGINE', '')
        if 'mysql' not in engine:
            raise RuntimeError("La base de datos configurada no es MySQL.")
        host = db.get('HOST') or 'localhost'
        port = str(db.get('PORT') or 3306)
        user = db.get('USER') or ''
        password = db.get('PASSWORD') or ''
        name = db.get('NAME') or ''
        return host, port, user, password, name

    def backup_db_view(self, request):
        user = request.user
        # Obtener conexión MySQL desde settings
        try:
            host, port, dbuser, dbpass, dbname = self._get_mysql_settings()
        except RuntimeError as e:
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse(f'{self.name}:index'))

        mysqldump_cmd = [
            'mysqldump',
            '-h', host,
            '-P', port,
            '-u', dbuser,
            f'--password={dbpass}',
            '--single-transaction',
            '--quick',
            dbname,
        ]

        # Ejecutar comando y capturar stdout
        try:
            proc = subprocess.Popen(mysqldump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            if proc.returncode != 0:
                err_text = err.decode('utf-8', errors='ignore')
                messages.error(request, f"mysqldump falló: {err_text}")
                return HttpResponseRedirect(reverse(f'{self.name}:index'))
        except FileNotFoundError:
            messages.error(request, "mysqldump no encontrado. Instala el cliente MySQL y asegúrate de que 'mysqldump' esté en PATH.")
            return HttpResponseRedirect(reverse(f'{self.name}:index'))
        except Exception as e:
            messages.error(request, f"Error ejecutando mysqldump: {e}")
            return HttpResponseRedirect(reverse(f'{self.name}:index'))

        # Preparar respuesta como descarga (posible zip)
        filename_sql = f'backup-{dbname}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.sql'
        # crear zip en memoria
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(filename_sql, out)
        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="backup-{dbname}-{datetime.now().strftime("%Y%m%d-%H%M%S")}.zip"'
        return response

    def restore_db_view(self, request):
        user = request.user
        if not (user.is_authenticated and (user.is_superuser or user.groups.filter(name=ADMIN_GROUP_NAME).exists())):
            return HttpResponseForbidden("No tienes permiso para restaurar respaldos.")

        if request.method != 'POST':
            return HttpResponseRedirect(reverse(f'{self.name}:index'))

        # archivo subido
        uploaded = request.FILES.get('backup_file')
        if not uploaded:
            messages.error(request, "No se envió ningún archivo.")
            return HttpResponseRedirect(reverse(f'{self.name}:index'))

        # validar extensión
        filename = uploaded.name.lower()
        if not (filename.endswith('.sql') or filename.endswith('.zip')):
            messages.error(request, "Formato no soportado. Sube .sql o .zip que contenga .sql.")
            return HttpResponseRedirect(reverse(f'{self.name}:index'))

        try:
            host, port, dbuser, dbpass, dbname = self._get_mysql_settings()
        except RuntimeError as e:
            messages.error(request, str(e))
            return HttpResponseRedirect(reverse(f'{self.name}:index'))

        # Guardar archivo temporal
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded.name)[1]) as tf:
                for chunk in uploaded.chunks():
                    tf.write(chunk)
                tmp_path = tf.name

            sql_files = []

            # Si es zip, extraer archivos .sql
            if zipfile.is_zipfile(tmp_path) or filename.endswith('.zip'):
                with zipfile.ZipFile(tmp_path, 'r') as zf:
                    for member in zf.namelist():
                        if member.lower().endswith('.sql'):
                            with tempfile.NamedTemporaryFile(delete=False, suffix='.sql') as ef:
                                ef.write(zf.read(member))
                                sql_files.append(ef.name)
                if not sql_files:
                    raise ValueError("El ZIP no contiene archivos .sql")
            else:
                sql_files = [tmp_path]

            # Ejecutar mysql < archivo.sql para cada sql
            for sql in sql_files:
                # comando sin shell: pasamos el archivo como stdin
                mysql_cmd = [
                    'mysql',
                    '-h', host,
                    '-P', port,
                    '-u', dbuser,
                    f'--password={dbpass}',
                    dbname,
                ]
                try:
                    with open(sql, 'rb') as infile:
                        proc = subprocess.Popen(mysql_cmd, stdin=infile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        out, err = proc.communicate()
                        if proc.returncode != 0:
                            err_text = err.decode('utf-8', errors='ignore')
                            raise RuntimeError(f"mysql falló al importar {os.path.basename(sql)}: {err_text}")
                except FileNotFoundError:
                    raise RuntimeError("El cliente 'mysql' no se encontró. Instala MySQL client y añade 'mysql' al PATH.")
            messages.success(request, "Restauración completada correctamente.")
        except Exception as e:
            messages.error(request, f"Error durante la restauración: {e}")
        finally:
            # limpiar archivos temporales
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except:
                pass
            # borrar extraídos
            # (si los sql_files no están en tmp_path y existen, eliminarlos)
            try:
                for f in sql_files:
                    if os.path.exists(f):
                        os.remove(f)
            except:
                pass

        return HttpResponseRedirect(reverse(f'{self.name}:index'))

    def procedimientos_view(self, request):
            """Vista principal de procedimientos - Solo 2 procedimientos"""
            user = request.user
            if not user.is_authenticated:
                return redirect(f'{self.name}:index')
            
            from biblioteca.procedimientos import ProcedimientosBiblioteca
            
            # Verificar si los procedimientos existen
            estado = ProcedimientosBiblioteca.verificar_estado_procedimientos()
            
            context = {
                'title': 'Procedimientos de Biblioteca',
                'opts': self._build_common_context(request),
                'procedimientos': [
                    {
                        'id': 'reporte_carreras',
                        'nombre': '📊 Reporte de Préstamos por Carrera',
                        'descripcion': 'Muestra estadísticas de préstamos agrupados por carrera profesional',
                        'icono': 'chart-bar',
                        'color': 'primary',
                        'url': reverse(f'{self.name}:ejecutar_procedimiento', args=['reporte_carreras']),
                        'disponible': any('ReportePrestamosPorCarrera' in p.get('nombre', '') for p in estado.get('procedimientos', []))
                    },
                    {
                        'id': 'libros_populares',
                        'nombre': '📚 Libros Más Populares',
                        'descripcion': 'Lista los libros más prestados en la biblioteca',
                        'icono': 'book',
                        'color': 'success',
                        'url': reverse(f'{self.name}:ejecutar_procedimiento', args=['libros_populares']),
                        'disponible': True  # Siempre disponible (no usa procedimiento almacenado)
                    }
                ],
                'estado': estado,
                'is_popup': False,
                'has_permission': True,
            }
            
            return TemplateResponse(request, 'admin/procedimientos_panel.html', context)
    
    def crear_procedimientos_view(self, request):
        """Vista para crear los procedimientos almacenados"""
        from biblioteca.procedimientos import ProcedimientosBiblioteca
        
        try:
            resultado = ProcedimientosBiblioteca.crear_procedimientos_basicos()
            if resultado:
                messages.success(request, "✅ Procedimientos creados correctamente")
            else:
                messages.error(request, "❌ Error al crear procedimientos")
        except Exception as e:
            messages.error(request, f"❌ Error: {str(e)}")
        
        return redirect(f'{self.name}:procedimientos')
    
    def ejecutar_procedimiento_view(self, request, procedimiento_id):
        """Ejecuta un procedimiento específico"""
        user = request.user
        if not user.is_authenticated:
            return redirect(f'{self.name}:index')
        
        from datetime import datetime, timedelta
        from biblioteca.procedimientos import ProcedimientosBiblioteca
        
        resultado = None
        
        try:
            if procedimiento_id == 'reporte_carreras':
                fecha_actual = datetime.now().date()
                
                if request.method == 'POST':
                    fecha_inicio = request.POST.get('fecha_inicio')
                    fecha_fin = request.POST.get('fecha_fin')
                    
                    if fecha_inicio and fecha_fin:
                        resultado = ProcedimientosBiblioteca.generar_reporte_prestamos_carrera(
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_fin
                        )
                    else:
                        # Últimos 30 días por defecto
                        fecha_fin = fecha_actual
                        fecha_inicio = fecha_fin - timedelta(days=30)
                        resultado = ProcedimientosBiblioteca.generar_reporte_prestamos_carrera(
                            fecha_inicio=fecha_inicio,
                            fecha_fin=fecha_fin
                        )
                else:
                    # Datos iniciales
                    fecha_fin = fecha_actual
                    fecha_inicio = fecha_fin - timedelta(days=30)
                    resultado = ProcedimientosBiblioteca.generar_reporte_prestamos_carrera(
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin
                    )
                    
            elif procedimiento_id == 'libros_populares':
                # Solo maneja el límite
                if request.method == 'POST':
                    limite_actual = request.POST.get('limite', '10')
                else:
                    limite_actual = '10'
                
                # Guardar en sesión
                request.session['limite_seleccionado'] = limite_actual
                
                # Ejecutar procedimiento
                resultado = ProcedimientosBiblioteca.obtener_libros_populares(int(limite_actual))
                
        except Exception as e:
            resultado = {
                'success': False,
                'error': str(e),
                'resultados': None
            }
        
        # Almacenar resultado en sesión
        if resultado:
            request.session['procedimiento_resultado'] = {
                'success': resultado.get('success', False),
                'resultados': resultado.get('resultados'),
                'error': resultado.get('error'),
                'procedimiento_id': procedimiento_id,
                'timestamp': datetime.now().isoformat()
            }
        
        return redirect(f'{self.name}:resultado_procedimiento')
    
    
    def resultado_procedimiento_view(self, request):
        """Muestra los resultados del procedimiento"""
        user = request.user
        if not user.is_authenticated:
            return redirect(f'{self.name}:index')
        
        resultado_data = request.session.pop('procedimiento_resultado', None)
        
        if not resultado_data:
            messages.warning(request, "No hay resultados para mostrar. Ejecuta un procedimiento primero.")
            return redirect(f'{self.name}:procedimientos')
        
        # Determinar título y columnas según el procedimiento
        procedimiento_id = resultado_data.get('procedimiento_id')
        titulo = "Resultados del Procedimiento"
        columnas = []
        
        # Inicializar selected_limite
        selected_limite = "10"  # Valor por defecto
        
        if procedimiento_id == 'reporte_carreras':
            titulo = "📊 Reporte de Préstamos por Carrera"
            columnas = ['Carrera', 'Alumnos Activos', 'Total Préstamos', 'Libros Diferentes', 'Duración Promedio (días)']
            
        elif procedimiento_id == 'libros_populares':
            titulo = "📚 Libros Más Populares"
            columnas = ['Libro', 'Autor', 'Total Préstamos', 'Categoría', 'Estado']
            
            # Obtener el límite seleccionado
            # Primero de la sesión
            selected_limite = request.session.get('limite_seleccionado', '10')
            # Si hay un POST reciente, usar ese valor
            if request.method == 'POST' and 'limite' in request.POST:
                selected_limite = request.POST.get('limite', '10')
        
        context = {
            'title': titulo,
            'opts': self._build_common_context(request),
            'resultado': resultado_data,
            'procedimiento_id': procedimiento_id,
            'columnas': columnas,
            'selected_limite': selected_limite,  # <-- PASAR AL TEMPLATE
            'is_popup': False,
            'has_permission': True,
        }
        
        return TemplateResponse(request, 'admin/procedimientos_resultado.html', context)
    
    def _build_common_context(self, request):
        """Construye contexto común para las vistas"""
        return {
            'admin_site': self,
            'has_permission': True,
            'opts': type('FakeOpts', (), {'app_label': 'biblioteca'})(),
        }
    
    def index(self, request, extra_context=None):
        """Sobrescribir el índice para agregar botones personalizados"""
        extra = extra_context or {}
        
        # Agregar botones personalizados al contexto
        custom_actions = [
            {
                'name': 'procedimientos',
                'label': '📊 Procedimientos Visuales',
                'url': reverse(f'{self.name}:procedimientos'),
                'description': 'Ejecutar reportes y análisis visuales',
                'icon': 'chart-line',
                'color': 'info'
            },
            {
                'name': 'backup',
                'label': '💾 Respaldar Base de Datos',
                'url': reverse(f'{self.name}:backup-db'),
                'description': 'Crear copia de seguridad de la base de datos',
                'icon': 'save',
                'color': 'success'
            },
            {
                'name': 'restore',
                'label': '🔄 Restaurar Base de Datos',
                'url': reverse(f'{self.name}:restore-db'),
                'description': 'Restaurar desde un respaldo',
                'icon': 'history',
                'color': 'warning'
            }
        ]
        
        extra.update({
            'mysql_restore_help': 'Sube un .sql (o .zip con .sql) para restaurar la BD.',
            'custom_actions': custom_actions,
            'show_custom_dashboard': True
        })
        
        return super().index(request, extra_context=extra)
    
    def index(self, request, extra_context=None):
        extra = extra_context or {}
        extra.update({'mysql_restore_help': 'Sube un .sql (o .zip con .sql) para restaurar la BD.'})
        return super().index(request, extra_context=extra)

# instancia del admin
custom_admin_site = MyAdminSite(name='custom_admin')

# registrar User/Group en custom_admin_site si usas admin personalizado
from django.contrib.auth.admin import UserAdmin, GroupAdmin
try:
    custom_admin_site.register(User, UserAdmin)
except admin.sites.AlreadyRegistered:
    pass
try:
    custom_admin_site.register(Group, GroupAdmin)
except admin.sites.AlreadyRegistered:
    pass

#admin.site.register(Carrera)
class CarreraAdmin(ImportExportModelAdmin):
    list_display = ('id_carrera', 'nombre')
    list_filter = ('id_carrera', 'nombre')
    search_fields = ('id_carrera', 'nombre')
    ordering = ('id_carrera', 'nombre')
custom_admin_site.register(Carrera, CarreraAdmin)

#admin.site.register(Alumno)
class AlumnoAdmin(ImportExportModelAdmin):
    list_display = ('id_alumno', 'nombre', 'semestre', 'carrera')
    list_filter = ('semestre', 'carrera')
    search_fields = ('id_alumno', 'nombre', 'carrera__nombre')
    raw_id_fields = ('carrera',)
    ordering = ('id_alumno', 'nombre') 
custom_admin_site.register(Alumno, AlumnoAdmin)


#admin.site.register(Autor)
class AutorAdmin(ImportExportModelAdmin):
    list_display = ('id_autor', 'nombre', 'nacionalidad')
    list_filter = ('nombre', 'nacionalidad')
    search_fields = ('id_autor', 'nombre', 'nacionalidad')
    ordering = ('id_autor', 'nombre')
custom_admin_site.register(Autor, AutorAdmin)

#admin.site.register(Editorial)
class EditorialAdmin(ImportExportModelAdmin):
    list_display = ('id_editorial', 'nombre', 'pais')
    list_filter = ('nombre', 'pais')
    search_fields = ('id_editorial', 'nombre', 'pais')
    ordering = ('id_editorial', 'nombre')
custom_admin_site.register(Editorial, EditorialAdmin)

#admin.site.register(Categoria)
class CategoriaAdmin(ImportExportModelAdmin):
    list_display = ('id_categoria', 'nombre')
    list_filter = ('nombre',)
    search_fields = ('id_categoria', 'nombre')
    ordering = ('id_categoria', 'nombre')
custom_admin_site.register(Categoria, CategoriaAdmin)

#admin.site.register(Libro)
class LibroAdmin(ImportExportModelAdmin):
    list_display = ('id_libro', 'titulo', 'autor', 'categoria', 'editorial', 'anio_publicacion')
    list_filter = ('categoria', 'autor', 'editorial', 'anio_publicacion')
    search_fields = ('id_libro', 'titulo', 'autor__nombre', 'categoria__nombre', 'editorial__nombre')
    raw_id_fields = ('autor', 'categoria', 'editorial')
    ordering = ('id_libro', 'titulo', 'autor', 'categoria', 'editorial')
custom_admin_site.register(Libro, LibroAdmin)

from django.db import transaction
from django.http import JsonResponse

#admin.site.register(Prestamo)
class PrestamoAdmin(ImportExportModelAdmin):
    list_display = ('id_prestamo', 'libro', 'alumno', 'fecha_prestamo', 'fecha_devolucion', 'estado_display')
    list_filter = ('libro', 'fecha_prestamo', 'fecha_devolucion')
    search_fields = ('id_prestamo', 'libro__titulo', 'alumno__nombre')
    raw_id_fields = ('libro', 'alumno')
    ordering = ('id_prestamo', 'fecha_prestamo')
    
    # AGREGAR ESTOS CAMPOS
    readonly_fields = ('estado_display', 'validacion_disponibilidad')
    fieldsets = (
        ('Información del Préstamo', {
            'fields': ('libro', 'alumno', 'fecha_prestamo', 'fecha_devolucion')
        }),
        ('Validación', {
            'fields': ('validacion_disponibilidad', 'estado_display'),
            'classes': ('collapse',),
            'description': 'Validación automática de disponibilidad'
        }),
    )
    
    # NUEVO: Método para validar disponibilidad en tiempo real
    def validacion_disponibilidad(self, obj):
        if obj and obj.libro:
            from .models import Prestamo
            # Verificar si el libro ya está prestado
            prestado = Prestamo.objects.filter(
                libro=obj.libro,
                fecha_devolucion__isnull=True
            ).exclude(pk=obj.pk if obj.pk else None).exists()
            
            if prestado:
                return '<span style="color:red;font-weight:bold;">LIBRO PRESTADO - No disponible</span>'
            else:
                return '<span style="color:green;font-weight:bold;">DISPONIBLE para préstamo</span>'
        return 'Seleccione un libro para validar'
    validacion_disponibilidad.short_description = 'Estado de Disponibilidad'
    validacion_disponibilidad.allow_tags = True
    
    # NUEVO: Método para mostrar estado
    def estado_display(self, obj):
        if obj and obj.pk:
            if obj.fecha_devolucion:
                return '<span style="color:green;">DEVUELTO</span>'
            else:
                return '<span style="color:orange;">PRESTADO</span>'
        return 'Nuevo préstamo'
    estado_display.short_description = 'Estado'
    estado_display.allow_tags = True
    
    # NUEVO: Cambiar template para agregar validación AJAX
    change_form_template = 'admin/biblioteca/prestamo_change_form.html'
    
    # NUEVO: Sobrescribir get_urls para agregar endpoint de validación
    def get_urls(self):
        urls = super().get_urls()
        from django.urls import path
        custom_urls = [
            path('check-libro/<int:libro_id>/', self.admin_site.admin_view(self.check_libro_disponible), 
                 name='check_libro_disponible'),
        ]
        return custom_urls + urls
    
    #Endpoint para validación AJAX
    def check_libro_disponible(self, request, libro_id):
        from .models import Prestamo, Libro
        try:
            libro = Libro.objects.get(id_libro=libro_id)
            
            # Verificar si está prestado
            prestado = Prestamo.objects.filter(
                libro=libro,
                fecha_devolucion__isnull=True
            ).exists()
            
            data = {
                'disponible': not prestado,
                'libro': libro.titulo,
                'autor': libro.autor.nombre if libro.autor else 'Sin autor',
                'prestado': prestado,
                'mensaje': 'No disponible' if prestado else 'Disponible'
            }
            
            if prestado:
                # Obtener información del préstamo activo
                prestamo_activo = Prestamo.objects.filter(
                    libro=libro,
                    fecha_devolucion__isnull=True
                ).first()
                
                if prestamo_activo:
                    data.update({
                        'prestado_a': prestamo_activo.alumno.nombre,
                        'desde': prestamo_activo.fecha_prestamo.strftime('%d/%m/%Y'),
                        'id_prestamo': prestamo_activo.id_prestamo
                    })
            
            return JsonResponse(data)
            
        except Libro.DoesNotExist:
            return JsonResponse({'error': 'Libro no encontrado'}, status=404)
    
    # NUEVO: Sobrescribir save_model con transacción y validación visual
    def save_model(self, request, obj, form, change):
        try:
            # Iniciar transacción atómica
            with transaction.atomic():
                # Validar disponibilidad (solo para nuevos préstamos)
                if not change:  # Es un nuevo préstamo
                    from .models import Prestamo
                    
                    # Verificar si el libro ya está prestado
                    libro_prestado = Prestamo.objects.filter(
                        libro=obj.libro,
                        fecha_devolucion__isnull=True
                    ).exists()
                    
                    if libro_prestado:
                        # Lanzar excepción con mensaje amigable
                        raise Exception(
                            f'TRANSACCIÓN CANCELADA: El libro "{obj.libro.titulo}" '
                            f'ya se encuentra prestado y no ha sido devuelto.'
                        )
                
                # Si pasa la validación, guardar
                super().save_model(request, obj, form, change)
                
                # Éxito - mensaje visual
                messages.success(request, 
                    f'TRANSACCIÓN EXITOSA: Préstamo registrado correctamente. '
                    f'Libro: {obj.libro.titulo} → Alumno: {obj.alumno.nombre}'
                )
                
        except Exception as e:
            # Error - mostrar ventana emergente (simulada con mensaje Django)
            error_msg = str(e)
            if 'TRANSACCIÓN CANCELADA' in error_msg:
                messages.error(request, 
                    f'{error_msg} '
                    f'Por favor, registre la devolución primero o seleccione otro libro.'
                )
            else:
                messages.error(request, f'Error en transacción: {error_msg}')
            
            # Re-lanzar la excepción para hacer rollback
            raise
custom_admin_site.register(Prestamo, PrestamoAdmin)

#admin.site.register(Usuario)
class UsuarioAdmin(ImportExportModelAdmin):
    list_display = ('id_usuario', 'nombre')
    list_filter = ('nombre',)
    search_fields = ('id_usuario', 'nombre')
    ordering = ('id_usuario', 'nombre')
custom_admin_site.register(Usuario, UsuarioAdmin)

#admin.site.register(Historial)
class HistorialAdmin(ImportExportModelAdmin):
    list_display = ('id_historial', 'alumno', 'libro', 'fecha_prestamo', 'fecha_devolucion')
    list_filter = ('fecha_prestamo', 'fecha_devolucion')
    search_fields = ('id_historial', 'alumno__nombre', 'libro__titulo')
    raw_id_fields = ('alumno', 'libro')
    ordering = ('id_historial', 'fecha_prestamo')
custom_admin_site.register(Historial, HistorialAdmin)
