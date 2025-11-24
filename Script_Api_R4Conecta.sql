


/*
=============================================================================
                    SISTEMA R4 CONECTA - BASE DE DATOS
=============================================================================

¿QUÉ ES ESTE ARCHIVO?
- Este archivo crea la tabla y procedimiento para recibir notificaciones de pagos
- Cuando alguien hace un pago móvil a Lysto por la plataforma R4, el banco envía una notificación
- Esta notificación se guarda automáticamente en la base de datos

¿CÓMO FUNCIONA?
1. Cliente hace pago móvil desde su teléfono
2. Banco procesa el pago
3. Banco envía notificación a R4Conecta (API)
4. La API guarda la información en la base de datos
5. Puedes consultar todos los pagos recibidos

¿QUÉ INFORMACIÓN SE GUARDA?
- Cédula del comercio que recibió el pago
- Teléfono del comercio
- Teléfono de quien hizo el pago
- Monto del pago
- Fecha y hora exacta
- Referencia única del pago
- Banco desde donde se hizo el pago

CREADO POR: Alicson Rubio
FECHA: Noviembre 2025
VERSIÓN: 1.0
*/

-- =====================================================
-- TABLA: r4_notifications
-- PROPÓSITO: Guardar todas las notificaciones de pagos que envían los bancos
-- =====================================================
CREATE TABLE IF NOT EXISTS r4_notifications (
    -- Cédula o RIF del comercio (8 dígitos máximo)
    IdComercio VARCHAR(8) NOT NULL COMMENT 'Cédula o RIF del comercio',
    -- Teléfono del comercio (11 dígitos: 04121234567)
    TelefonoComercio VARCHAR(11) NOT NULL COMMENT 'Teléfono del comercio',
    -- Teléfono de quien hizo el pago (11 dígitos)
    TelefonoEmisor VARCHAR(11) NOT NULL COMMENT 'Teléfono de quien pagó',
    -- Descripción del pago (opcional, hasta 30 caracteres)
    Concepto VARCHAR(30) COMMENT 'Descripción del pago',
    -- Código del banco (3 dígitos: 102=Venezuela, 134=Banesco, etc.)
    BancoEmisor VARCHAR(3) NOT NULL COMMENT 'Código del banco',
    -- Monto del pago (ejemplo: "150.50")
    Monto VARCHAR(20) NOT NULL COMMENT 'Monto del pago',
    -- Fecha y hora del pago (formato: 2024-12-05T16:50:48.421Z)
    FechaHora VARCHAR(25) NOT NULL COMMENT 'Fecha y hora del pago',
    -- Número de referencia único del pago
    Referencia VARCHAR(20) NOT NULL COMMENT 'Referencia única del pago',
    -- Código de respuesta (00=exitoso, otros=error)
    CodigoRed VARCHAR(2) NOT NULL COMMENT 'Código de respuesta',
    -- Índices para búsquedas rápidas
    INDEX idx_referencia (Referencia),
    INDEX idx_comercio (IdComercio),
    INDEX idx_fecha (FechaHora)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Notificaciones de pagos R4Notifica';

-- =====================================================
-- PROCEDIMIENTO: sp_guardar_notificacion_r4
-- DESCRIPCIÓN: Guarda notificaciones de pagos R4
-- =====================================================

-- Cambiar delimitadores
DELIMITER //

-- Eliminar el procedimiento si ya existe
DROP PROCEDURE IF EXISTS `sp_guardar_notificacion_r4`//

-- Crear el procedimiento
CREATE PROCEDURE `sp_guardar_notificacion_r4`(
    -- Variables de entrada según el JSON de R4 (todo en string)
    IN p_IdComercio VARCHAR(8),
    IN p_TelefonoComercio VARCHAR(11),
    IN p_TelefonoEmisor VARCHAR(11),
    IN p_Concepto VARCHAR(30),
    IN p_BancoEmisor VARCHAR(3),
    IN p_Monto VARCHAR(20),
    IN p_FechaHora VARCHAR(25),
    IN p_Referencia VARCHAR(20),
    IN p_CodigoRed VARCHAR(2),
    
    -- Variables de salida
    OUT p_mensaje VARCHAR(500),
    OUT p_codigo INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        GET DIAGNOSTICS CONDITION 1
            p_mensaje = MESSAGE_TEXT;
        SET p_codigo = -1;
    END;

    -- Iniciar transacción
    START TRANSACTION;

    -- Validar parámetros obligatorios
    IF p_IdComercio IS NULL OR p_TelefonoComercio IS NULL OR p_TelefonoEmisor IS NULL OR
       p_BancoEmisor IS NULL OR p_Monto IS NULL OR p_FechaHora IS NULL OR
       p_Referencia IS NULL OR p_CodigoRed IS NULL
    THEN
        SET p_mensaje = 'Error: Faltan datos obligatorios';
        SET p_codigo = -1;
        ROLLBACK;
    ELSEIF p_CodigoRed != '00' THEN
        -- Gestión detallada de códigos de respuesta según documento del banco
        CASE p_CodigoRed
            WHEN '01' THEN
                SET p_mensaje = 'Referirse al cliente - Código: 01';
                SET p_codigo = -2;
            WHEN '12' THEN
                SET p_mensaje = 'Transacción inválida - Código: 12';
                SET p_codigo = -3;
            WHEN '13' THEN
                SET p_mensaje = 'Monto inválido - Código: 13';
                SET p_codigo = -4;
            WHEN '14' THEN
                SET p_mensaje = 'Número de teléfono receptor errado - Código: 14';
                SET p_codigo = -5;
            WHEN '05' THEN
                SET p_mensaje = 'Tiempo de respuesta excedido - Código: 05';
                SET p_codigo = -6;
            WHEN '30' THEN
                SET p_mensaje = 'Error de formato - Código: 30';
                SET p_codigo = -7;
            WHEN '41' THEN
                SET p_mensaje = 'Servicio no activo - Código: 41';
                SET p_codigo = -8;
            WHEN '43' THEN
                SET p_mensaje = 'Servicio no activo - Código: 43';
                SET p_codigo = -9;
            WHEN '55' THEN
                SET p_mensaje = 'Token inválido - Código: 55';
                SET p_codigo = -10;
            WHEN '56' THEN
                SET p_mensaje = 'Celular no coincide - Código: 56';
                SET p_codigo = -11;
            WHEN '57' THEN
                SET p_mensaje = 'Negada por el receptor - Código: 57';
                SET p_codigo = -12;
            WHEN '62' THEN
                SET p_mensaje = 'Cuenta restringida - Código: 62';
                SET p_codigo = -13;
            WHEN '68' THEN
                SET p_mensaje = 'Respuesta tardía, procede reverso - Código: 68';
                SET p_codigo = -14;
            WHEN '80' THEN
                SET p_mensaje = 'Cédula o pasaporte errado - Código: 80';
                SET p_codigo = -15;
            WHEN '87' THEN
                SET p_mensaje = 'Time out - Código: 87';
                SET p_codigo = -16;
            WHEN '90' THEN
                SET p_mensaje = 'Cierre bancario en proceso - Código: 90';
                SET p_codigo = -17;
            WHEN '91' THEN
                SET p_mensaje = 'Institución no disponible - Código: 91';
                SET p_codigo = -18;
            WHEN '92' THEN
                SET p_mensaje = 'Banco receptor no afiliado - Código: 92';
                SET p_codigo = -19;
            WHEN '99' THEN
                SET p_mensaje = 'Error en notificación - Código: 99';
                SET p_codigo = -20;
            ELSE
                -- Código no reconocido
                SET p_mensaje = CONCAT('Transacción no aprobada - Código no reconocido: ', p_CodigoRed);
                SET p_codigo = -100;
        END CASE;
        ROLLBACK;
    ELSE
        -- Verificar si ya existe la referencia (evitar duplicados)
        IF EXISTS (SELECT 1 FROM r4_notifications WHERE Referencia = p_Referencia) THEN
            SET p_mensaje = concat('Notificación num: ',p_Referencia ,' ya procesada');
            SET p_codigo = 0;
        ELSE
            -- Insertar la notificación (todo como string, sin conversiones)
            INSERT INTO r4_notifications (
                IdComercio,
                TelefonoComercio,
                TelefonoEmisor,
                Concepto,
                BancoEmisor,
                Monto,
                FechaHora,
                Referencia,
                CodigoRed
            ) VALUES (
                p_IdComercio,
                p_TelefonoComercio,
                p_TelefonoEmisor,
                p_Concepto,
                p_BancoEmisor,
                p_Monto,
                p_FechaHora,
                p_Referencia,
                p_CodigoRed
            );
            
            SET p_mensaje = concat('Notificación num: ',p_Referencia,' guardada exitosamente');
            SET p_codigo = 1;
        END IF;
        
        -- Confirmar transacción (guardar los datos permanentemente)
        COMMIT;
    END IF;

END//

-- Restaurar delimitador original
DELIMITER ;