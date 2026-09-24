# Cambios principales realizados

## Creación del Mutex (`xSemaphoreCreateMutex`)

Reemplazó a `xQueueCreate()`. Devuelve un `SemaphoreHandle_t`.

## Uso de `xSemaphoreTake()` y `xSemaphoreGive()`

Cualquier tarea que necesite leer o escribir en `globalSensorData` primero debe **tomar** el Mutex. Si otra tarea lo está usando, esperará hasta el tiempo límite especificado (en este caso `pdMS_TO_TICKS(100)`). Una vez terminada la operación, se llama a `xSemaphoreGive()` para liberarlo.

## Copia local en `ReceiverTask` (buena práctica)

Se copia la estructura a una variable local (`localCopy`) mientras se tiene el mutex y se libera inmediatamente. Imprimir por Serial dentro de la sección crítica es lento; de esta forma minimizamos el tiempo que el Mutex está retenido.

## Adición de `vTaskDelay()` en `ReceiverTask`

Las colas bloquean automáticamente a la tarea receptora hasta que llega un nuevo dato (`portMAX_DELAY`). Con variables globales y Mutex esto no sucede: si no pones un delay en el receptor, intentará leer en bucle rápido infinitamente, bloqueando el procesador o dejando sin tiempo a tareas con menor prioridad.
