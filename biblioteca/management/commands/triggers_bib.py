from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        print("CONFIGURANDO TRIGGERS CORRECTOS...")
        
        with connection.cursor() as cursor:
            # 1. Eliminar TODOS los triggers anteriores
            cursor.execute("""
                SELECT CONCAT('DROP TRIGGER IF EXISTS ', TRIGGER_NAME, ';')
                FROM INFORMATION_SCHEMA.TRIGGERS 
                WHERE TRIGGER_SCHEMA = DATABASE()
            """)
            
            for cmd in cursor.fetchall():
                try:
                    cursor.execute(cmd[0])
                except:
                    pass
            
            print("Todos los triggers anteriores eliminados")
            print("\n" + "="*60)
            print("Creando NUEVOS triggers correctos...")
            print("="*60)
            
            # 2. SOLO 2 TRIGGERS ESENCIALES CORREGIDOS
            
            # Trigger 1: ANTES de INSERT (validación)
            try:
                cursor.execute("""
                    CREATE TRIGGER trigger_validar_antes_insert
                    BEFORE INSERT ON biblioteca_prestamo
                    FOR EACH ROW
                    BEGIN
                        DECLARE libro_status VARCHAR(12);
                        DECLARE prestamos_activos INT;
                        
                        -- 1. Verificar estado del libro
                        SELECT status INTO libro_status
                        FROM biblioteca_libro 
                        WHERE id_libro = NEW.libro_id;
                        
                        IF libro_status != 'DISPONIBLE' THEN
                            SIGNAL SQLSTATE '45000'
                            SET MESSAGE_TEXT = 'Libro no disponible';
                        END IF;
                        
                        -- 2. Verificar límite de préstamos (3 máximo)
                        SELECT COUNT(*) INTO prestamos_activos
                        FROM biblioteca_prestamo
                        WHERE alumno_id = NEW.alumno_id
                        AND status = 'ACTIVO';
                        
                        IF prestamos_activos >= 3 THEN
                            SIGNAL SQLSTATE '45000'
                            SET MESSAGE_TEXT = 'Límite de 3 préstamos activos alcanzado';
                        END IF;
                        
                        -- 3. Forzar status inicial
                        SET NEW.status = 'ACTIVO';
                    END
                """)
                print("✓ Trigger 1: Validación antes de INSERT")
            except Exception as e:
                print(f"✗ Error Trigger 1: {e}")
            
            # Trigger 2: DESPUÉS de INSERT (actualizar libro)
            try:
                cursor.execute("""
                    CREATE TRIGGER trigger_despues_insert
                    AFTER INSERT ON biblioteca_prestamo
                    FOR EACH ROW
                    BEGIN
                        DECLARE next_id VARCHAR(10);
                        DECLARE max_num INT;
                        
                        -- 1. Cambiar libro a PRESTADO
                        UPDATE biblioteca_libro 
                        SET status = 'PRESTADO'
                        WHERE id_libro = NEW.libro_id;
                        
                        -- 2. Generar nuevo ID para historial
                        -- Obtener el máximo número actual
                        SELECT MAX(CAST(SUBSTRING(id_historial, 2) AS UNSIGNED)) 
                        INTO max_num
                        FROM biblioteca_historial 
                        WHERE id_historial LIKE 'H%';
                        
                        -- Si no hay registros, empezar en 1
                        IF max_num IS NULL THEN
                            SET max_num = 0;
                        END IF;
                        
                        -- Crear nuevo ID (H001, H002, etc.)
                        SET next_id = CONCAT('H', LPAD(max_num + 1, 3, '0'));
                        
                        -- 3. Insertar en historial con ID generado
                        INSERT INTO biblioteca_historial 
                        (id_historial, alumno_id, libro_id, usuario_id, fecha_prestamo)
                        VALUES (
                            next_id,
                            NEW.alumno_id,
                            NEW.libro_id,
                            NEW.usuario_id,
                            NEW.fecha_prestamo
                        );
                    END
                """)
            except Exception as e:
                print(f"✗ Error Trigger 2: {e}")
            
            # Trigger 3: ANTES de UPDATE (manejar cambios de status)
            try:
                cursor.execute("""
                    CREATE TRIGGER trigger_antes_update_status
                    BEFORE UPDATE ON biblioteca_prestamo
                    FOR EACH ROW
                    BEGIN
                        -- Si cambia de ACTIVO a DEVUELTO
                        IF OLD.status = 'ACTIVO' AND NEW.status = 'DEVUELTO' THEN
                            -- Poner fecha de devolución si no tiene
                            IF NEW.fecha_devolucion IS NULL THEN
                                SET NEW.fecha_devolucion = CURDATE();
                            END IF;
                            
                            -- Cambiar libro a DISPONIBLE (esto lo hará otro trigger)
                            
                        -- Si cambia de DEVUELTO a ACTIVO
                        ELSEIF OLD.status = 'DEVUELTO' AND NEW.status = 'ACTIVO' THEN
                            -- Quitar fecha de devolución
                            SET NEW.fecha_devolucion = NULL;
                            
                            -- Cambiar libro a PRESTADO (esto lo hará otro trigger)
                        END IF;
                    END
                """)
                print("✓ Trigger 3: Manejo de status antes de UPDATE")
            except Exception as e:
                print(f"✗ Error Trigger 3: {e}")
            
            # Trigger 4: DESPUÉS de UPDATE (actualizar libro)
            try:
                cursor.execute("""
                    CREATE TRIGGER trigger_despues_update_libro
                    AFTER UPDATE ON biblioteca_prestamo
                    FOR EACH ROW
                    BEGIN
                        -- Si cambió de ACTIVO a DEVUELTO
                        IF OLD.status = 'ACTIVO' AND NEW.status = 'DEVUELTO' THEN
                            -- Cambiar libro a DISPONIBLE
                            UPDATE biblioteca_libro 
                            SET status = 'DISPONIBLE'
                            WHERE id_libro = NEW.libro_id;
                            
                            -- Actualizar historial
                            UPDATE biblioteca_historial 
                            SET fecha_devolucion = NEW.fecha_devolucion
                            WHERE libro_id = NEW.libro_id 
                              AND alumno_id = NEW.alumno_id
                              AND fecha_devolucion IS NULL
                            ORDER BY fecha_prestamo DESC
                            LIMIT 1;
                            
                        -- Si cambió de DEVUELTO a ACTIVO (raro, pero posible)
                        ELSEIF OLD.status = 'DEVUELTO' AND NEW.status = 'ACTIVO' THEN
                            -- Cambiar libro a PRESTADO
                            UPDATE biblioteca_libro 
                            SET status = 'PRESTADO'
                            WHERE id_libro = NEW.libro_id;
                            
                            -- Quitar fecha de devolución del historial
                            UPDATE biblioteca_historial 
                            SET fecha_devolucion = NULL
                            WHERE libro_id = NEW.libro_id 
                              AND alumno_id = NEW.alumno_id
                              AND fecha_devolucion = OLD.fecha_devolucion
                            LIMIT 1;
                        END IF;
                    END
                """)
                print("✓ Trigger 4: Actualizar libro después de UPDATE")
            except Exception as e:
                print(f"✗ Error Trigger 4: {e}")
            
            
          