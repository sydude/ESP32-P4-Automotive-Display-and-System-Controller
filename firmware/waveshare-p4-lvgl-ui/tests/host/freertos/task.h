#pragma once
int xTaskCreate(void (*task)(void *), const char *, unsigned, void *, unsigned, void *);
void vTaskDelay(unsigned);
void vTaskDelete(void *);
