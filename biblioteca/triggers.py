from django.db import connection
import logging

logger = logging.getLogger(__name__)

class TriggersBiblioteca:
    
    @staticmethod
    def crear_triggers():
        """SOLO para emergencias - Usar limpiar_todo.py mejor"""
        print("⚠️  ADVERTENCIA: Usa 'python manage.py limpiar_todo' en lugar de esto")
        print("Este archivo mantiene solo funciones de consulta")
        return False
    
    @staticmethod
    def listar_triggers():
        """Lista todos los triggers existentes"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW TRIGGERS")
                
                triggers = []
                for row in cursor.fetchall():
                    triggers.append({
                        'nombre': row[0],
                        'evento': row[1],
                        'tabla': row[2],
                        'sentencia': row[3],
                        'timing': row[4],
                        'creado': row[5]
                    })
                
                return {
                    'success': True,
                    'triggers': triggers,
                    'total': len(triggers)
                }
                
        except Exception as e:
            logger.error(f"Error listando triggers: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def eliminar_trigger(nombre):
        """Elimina un trigger específico"""
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TRIGGER IF EXISTS {nombre}")
                return {'success': True, 'mensaje': f'Trigger {nombre} eliminado'}
        except Exception as e:
            return {'success': False, 'error': str(e)}