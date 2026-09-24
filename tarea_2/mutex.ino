#include <Arduino.h>

// Define a structured data type
struct SensorData {
  int id;
  float temperature;
};

// 1. Instancia global del struct
SensorData globalSensorData = {1, 24.5};

// 2. Handle global para el Mutex
SemaphoreHandle_t sensorMutex;

// Task Function Declarations
void SenderTask(void *pvParameters);
void ReceiverTask(void *pvParameters);

void setup() {
  Serial.begin(115200);
  
  // Wait for Serial to initialize
  delay(1000); 
  Serial.println("Initializing system...");

  // 3. Crear el Mutex
  sensorMutex = xSemaphoreCreateMutex();
  
  if (sensorMutex != NULL) {
    Serial.println("Mutex created successfully.");

    // Pinning SenderTask to Core 1, Priority 1
    xTaskCreatePinnedToCore(
      SenderTask,       // Task function
      "Sender",         // Task name text
      3000,             // Stack size (in words)
      NULL,             // Parameter passed to task
      1,                // Priority
      NULL,             // Task handle
      1                 // Core ID: 1 (APP_CPU)
    );

    // Pinning ReceiverTask to Core 1, Priority 2
    xTaskCreatePinnedToCore(
      ReceiverTask,     // Task function
      "Receiver",       // Task name text
      3000,             // Stack size (in words)
      NULL,             // Parameter passed to task
      2,                // Priority
      NULL,             // Task handle
      1                 // Core ID: 1 (APP_CPU)
    );
  } else {
    Serial.println("Error creating the Mutex!");
  }
}

void SenderTask(void *pvParameters) {
  Serial.printf("SenderTask started on Core %d\n", xPortGetCoreID());
  
  while(1) {
    // Intentar tomar el mutex para ESCRIBIR en la variable global (espera hasta 100ms)
    if (xSemaphoreTake(sensorMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
      
      // --- SECCIÓN CRÍTICA (ESCRITURA) ---
      globalSensorData.temperature += 0.1; // Actualizar estructura global
      Serial.printf("[Sender] Updated Temp to: %.2f\n", globalSensorData.temperature);
      // -----------------------------------

      // Liberar el mutex
      xSemaphoreGive(sensorMutex);
    } else {
      Serial.println("[Sender] Mutex busy, could not update data!");
    }
    
    // Delay for 1000ms (Yields CPU to other tasks)
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void ReceiverTask(void *pvParameters) {
  Serial.printf("ReceiverTask started on Core %d\n", xPortGetCoreID());
  
  SensorData localCopy; // Copia local para no mantener el mutex bloqueado mucho tiempo
  
  while(1) {
    // Intentar tomar el mutex para LEER la variable global
    if (xSemaphoreTake(sensorMutex, pdMS_TO_TICKS(100)) == pdTRUE) {
      
      // --- SECCIÓN CRÍTICA (LECTURA RÁPIDA) ---
      localCopy = globalSensorData; // Copiar datos a una variable local
      // ----------------------------------------

      // Liberar el mutex lo antes posible
      xSemaphoreGive(sensorMutex);

      // Procesar o imprimir los datos fuera de la sección crítica
      Serial.printf("[Receiver] Read ID: %d, Temp: %.2f (Core %d)\n", 
                    localCopy.id, 
                    localCopy.temperature, 
                    xPortGetCoreID());
    } else {
      Serial.println("[Receiver] Mutex busy, could not read data!");
    }

    // A diferencia de las colas (que bloquean la tarea automáticamente hasta recibir datos),
    // con un Mutex debes agregar un vTaskDelay() en el receptor para evitar un bucle infinito que sature el CPU.
    vTaskDelay(pdMS_TO_TICKS(1000));
  }
}

void loop() {
  vTaskDelete(NULL); 
}