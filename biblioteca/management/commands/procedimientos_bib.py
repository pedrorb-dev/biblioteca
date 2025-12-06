# En tu_app/management/commands/procedimientos_bib.py
from django.core.management.base import BaseCommand
from biblioteca.procedimientos import ProcedimientosBiblioteca
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Gestiona procedimientos almacenados de la biblioteca'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'accion',
            type=str,
            choices=['crear', 'verificar', 'reporte', 'sanciones', 'estadisticas'],
            help='Acción a realizar'
        )
    
    def handle(self, *args, **options):
        accion = options['accion']
        
        if accion == 'crear':
            self.stdout.write("Creando procedimientos almacenados...")
            resultado = ProcedimientosBiblioteca.crear_procedimientos_basicos()
            if resultado:
                self.stdout.write(self.style.SUCCESS("Todos los procedimientos creados"))
            else:
                self.stdout.write(self.style.ERROR("Error creando procedimientos"))
        
        elif accion == 'verificar':
            self.stdout.write("Verificando procedimientos existentes...")
            resultado = ProcedimientosBiblioteca.verificar_estado_procedimientos()
            if resultado['success']:
                self.stdout.write(f"Total procedimientos: {resultado['total']}")
                for proc in resultado['procedimientos']:
                    self.stdout.write(f"  • {proc['nombre']} ({proc['creado']})")
            else:
                self.stdout.write(self.style.ERROR(f"✗ Error: {resultado['error']}"))
        
        elif accion == 'estadisticas':
            self.stdout.write("Obteniendo estadísticas de la biblioteca...")
            resultado = ProcedimientosBiblioteca.obtener_estadisticas_biblioteca()
            self.mostrar_resultados(resultado)
        
        elif accion == 'reporte':
            self.stdout.write("Generando reporte de préstamos por carrera...")
            
            # Parámetros por defecto: último mes
            fecha_fin = datetime.now().date()
            fecha_inicio = fecha_fin - timedelta(days=30)
            
            resultado = ProcedimientosBiblioteca.generar_reporte_prestamos_carrera(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            self.mostrar_resultados(resultado)
        
        elif accion == 'sanciones':
            self.stdout.write("Aplicando sanciones automáticas...")
            resultado = ProcedimientosBiblioteca.aplicar_sanciones_automaticas()
            self.mostrar_resultados(resultado)

    
    def mostrar_resultados(self, resultado):
        if resultado['success']:
            self.stdout.write(self.style.SUCCESS("Procedimiento ejecutado"))
            
            if resultado.get('resultados'):
                for i, conjunto in enumerate(resultado['resultados'], 1):
                    self.stdout.write(f"\n--- Resultado {i} ---")
                    for fila in conjunto:
                        self.stdout.write(str(fila))
        else:
            self.stdout.write(self.style.ERROR(f"✗ Error: {resultado.get('error', 'Desconocido')}"))