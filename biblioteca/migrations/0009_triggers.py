# En biblioteca/migrations/0007_triggers_completos.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('biblioteca', '0006_libro_status_alter_alumno_id_alumno_and_more'), 
    ]
    
    operations = [
        # ===== PRIMERO: Eliminar triggers existentes =====
        migrations.RunSQL(
            """
            DROP TRIGGER IF EXISTS trig_devolucion_completa;
            DROP TRIGGER IF EXISTS trig_prestamo_historial;
            DROP TRIGGER IF EXISTS trig_prestamo_libro;
            DROP TRIGGER IF EXISTS trig_historial_auto;
            DROP TRIGGER IF EXISTS trig_status_libro;
            """,
            """
            SELECT 1;
            """
        ),
        
        # ===== SEGUNDO: Trigger SIMPLE para cambiar status del libro al prestar =====
        migrations.RunSQL(
            """
            CREATE TRIGGER trig_prestamo_libro
            AFTER INSERT ON biblioteca_prestamo
            FOR EACH ROW
            UPDATE biblioteca_libro 
            SET status = 'PRESTADO'
            WHERE id_libro = NEW.libro_id
            """,
            "DROP TRIGGER IF EXISTS trig_prestamo_libro;"
        ),
        
        # ===== TERCERO: Trigger SIMPLE para crear historial =====
        migrations.RunSQL(
            """
            CREATE TRIGGER trig_prestamo_historial
            AFTER INSERT ON biblioteca_prestamo
            FOR EACH ROW
            INSERT INTO biblioteca_historial 
            (id_historial, alumno_id, libro_id, usuario_id, fecha_prestamo, fecha_devolucion)
            VALUES (
                CONCAT('H', NEW.id_prestamo, '_', DATE_FORMAT(NOW(), '%Y%m%d')),
                NEW.alumno_id,
                NEW.libro_id,
                NEW.usuario_id,
                NEW.fecha_prestamo,
                NULL
            )
            """,
            "DROP TRIGGER IF EXISTS trig_prestamo_historial;"
        ),
        
        # ===== CUARTO: Trigger SIMPLIFICADO para devolución (SIN BEGIN/END) =====
        migrations.RunSQL(
            """
            CREATE TRIGGER trig_devolucion_simple
            AFTER UPDATE ON biblioteca_prestamo
            FOR EACH ROW
            UPDATE biblioteca_libro 
            SET status = 'DISPONIBLE'
            WHERE id_libro = NEW.libro_id 
            AND OLD.fecha_devolucion IS NULL 
            AND NEW.fecha_devolucion IS NOT NULL
            """,
            "DROP TRIGGER IF EXISTS trig_devolucion_simple;"
        ),
        
        # ===== QUINTO: Trigger adicional para actualizar historial al devolver =====
        migrations.RunSQL(
            """
            CREATE TRIGGER trig_actualizar_historial
            AFTER UPDATE ON biblioteca_prestamo
            FOR EACH ROW
            UPDATE biblioteca_historial 
            SET fecha_devolucion = NEW.fecha_devolucion
            WHERE libro_id = NEW.libro_id 
            AND alumno_id = NEW.alumno_id
            AND DATE(fecha_prestamo) = DATE(NEW.fecha_prestamo)
            AND fecha_devolucion IS NULL
            AND OLD.fecha_devolucion IS NULL 
            AND NEW.fecha_devolucion IS NOT NULL
            LIMIT 1
            """,
            "DROP TRIGGER IF EXISTS trig_actualizar_historial;"
        ),
    ]