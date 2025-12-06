# En biblioteca/procedimientos.py
from django.db import connection
from datetime import date, datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ProcedimientosBiblioteca:
    @staticmethod
    def generar_reporte_prestamos_carrera(fecha_inicio=None, fecha_fin=None):
        """Genera reporte de préstamos por carrera"""
        if not fecha_inicio:
            fecha_inicio = date(date.today().year, 1, 1)  # Inicio del año
        
        if not fecha_fin:
            fecha_fin = date.today()
        
        return ProcedimientosBiblioteca.ejecutar_procedimiento(
            'ReportePrestamosPorCarrera',
            [fecha_inicio, fecha_fin]
        )
    
    @staticmethod
    def obtener_libros_populares(limite=10):
        """Obtiene los libros más populares (más prestados)"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        l.id_libro,
                        l.titulo,
                        a.nombre as autor,
                        COUNT(p.id_prestamo) as total_prestamos,
                        c.nombre as categoria,
                        l.status
                    FROM biblioteca_libro l
                    LEFT JOIN biblioteca_autor a ON l.autor_id = a.id_autor
                    LEFT JOIN biblioteca_categoria c ON l.categoria_id = c.id_categoria
                    LEFT JOIN biblioteca_prestamo p ON l.id_libro = p.libro_id
                    GROUP BY l.id_libro, l.titulo, a.nombre, c.nombre, l.status
                    ORDER BY total_prestamos DESC
                    LIMIT %s
                """, [int(limite)])
                
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convertir Decimal a tipos serializables
                converted_rows = []
                for row in rows:
                    row_dict = {}
                    for idx, value in enumerate(row):
                        column_name = columns[idx]
                        if isinstance(value, Decimal):
                            if value % 1 == 0:
                                row_dict[column_name] = int(value)
                            else:
                                row_dict[column_name] = float(value)
                        elif value is None:
                            row_dict[column_name] = None
                        elif hasattr(value, 'isoformat'):
                            row_dict[column_name] = value.isoformat()
                        else:
                            row_dict[column_name] = value
                    converted_rows.append(row_dict)
                
                resultados = [converted_rows]
                
                return {
                    'success': True,
                    'resultados': resultados,
                    'mensaje': 'Libros populares obtenidos correctamente'
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo libros populares: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'resultados': None
            }
    
    @staticmethod
    def verificar_estado_procedimientos():
        """Verifica qué procedimientos existen en MySQL"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SHOW PROCEDURE STATUS 
                    WHERE Db = DATABASE()
                    AND Name LIKE '%biblioteca%' 
                    OR Name LIKE '%prestamo%'
                    OR Name LIKE '%carrera%'
                """)
                
                procedimientos = []
                for row in cursor.fetchall():
                    procedimientos.append({
                        'nombre': row[1],
                        'tipo': row[2],
                        'creado': row[4]
                    })
                
                return {
                    'success': True,
                    'procedimientos': procedimientos,
                    'total': len(procedimientos)
                }
                
        except Exception as e:
            logger.error(f"Error verificando procedimientos: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def crear_procedimientos_basicos():
        try:
            with connection.cursor() as cursor:
                # ===== PROCEDIMIENTO 1: ReportePrestamosPorCarrera =====
                cursor.execute("DROP PROCEDURE IF EXISTS ReportePrestamosPorCarrera")
                cursor.execute("""
                    CREATE PROCEDURE ReportePrestamosPorCarrera(
                        IN fecha_inicio DATE,
                        IN fecha_fin DATE
                    )
                    BEGIN
                        SELECT 
                            c.id_carrera,
                            c.nombre as carrera_nombre,
                            COUNT(DISTINCT a.id_alumno) as alumnos_activos,
                            COUNT(p.id_prestamo) as total_prestamos,
                            COUNT(DISTINCT p.libro_id) as libros_diferentes,
                            CAST(AVG(DATEDIFF(p.fecha_devolucion, p.fecha_prestamo)) AS DECIMAL(10,2)) as duracion_promedio
                        FROM biblioteca_carrera c
                        LEFT JOIN biblioteca_alumno a ON c.id_carrera = a.carrera_id
                        LEFT JOIN biblioteca_prestamo p ON a.id_alumno = p.alumno_id
                            AND p.fecha_prestamo BETWEEN fecha_inicio AND fecha_fin
                        GROUP BY c.id_carrera, c.nombre
                        ORDER BY total_prestamos DESC;
                    END
                """)
                logger.info("Procedimiento ReportePrestamosPorCarrera creado")
                
                return True
                
        except Exception as e:
            logger.error(f"Error creando procedimientos: {str(e)}")
            return False
    
    @staticmethod 
    def ejecutar_procedimiento(nombre_procedimiento, parametros=[]):
        """Ejecuta cualquier procedimiento almacenado"""
        try:
            with connection.cursor() as cursor:
                # Construir la llamada al procedimiento
                placeholders = ', '.join(['%s'] * len(parametros))
                sql = f"CALL {nombre_procedimiento}({placeholders})"
                
                cursor.execute(sql, parametros)
                
                # Obtener todos los resultados
                resultados = []
                while True:
                    if cursor.description:
                        columns = [col[0] for col in cursor.description]
                        rows = cursor.fetchall()
                        
                        # Convertir cada fila, manejando Decimal
                        converted_rows = []
                        for row in rows:
                            converted_row = {}
                            for i, value in enumerate(row):
                                column_name = columns[i]
                                if isinstance(value, Decimal):
                                    try:
                                        if value % 1 == 0:
                                            converted_row[column_name] = int(value)
                                        else:
                                            converted_row[column_name] = float(value)
                                    except:
                                        converted_row[column_name] = float(value)
                                elif hasattr(value, 'isoformat'):
                                    converted_row[column_name] = value.isoformat()
                                elif value is None:
                                    converted_row[column_name] = None
                                else:
                                    converted_row[column_name] = value
                            converted_rows.append(converted_row)
                        
                        resultados.append(converted_rows)
                    
                    if not cursor.nextset():
                        break
                
                return {
                    'success': True,
                    'resultados': resultados if resultados else None,
                    'mensaje': f'Procedimiento {nombre_procedimiento} ejecutado correctamente'
                }
                
        except Exception as e:
            logger.error(f"Error ejecutando procedimiento {nombre_procedimiento}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'resultados': None
            }