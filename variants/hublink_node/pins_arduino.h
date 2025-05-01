#ifndef Pins_Arduino_h
#define Pins_Arduino_h

#define BOARD_HUBLINK_NODE // Board variant identifier

#include <stdint.h>
#include "soc/soc_caps.h"

#define USB_VID 0x1209 // Test/Development VID
#define USB_PID 0x0001 // Custom PID for Hublink Node
#define USB_MANUFACTURER "Hublink"
#define USB_PRODUCT "Hublink Node"
#define USB_SERIAL "" // Empty string for MAC address

#define LED_BUILTIN 13

static const uint8_t TX = 39;
static const uint8_t RX = 38;
#define TX1 TX
#define RX1 RX

static const uint8_t I2C_EN = 7;
static const uint8_t AUX_IO0 = 1;
static const uint8_t AUX_IO = 2;
static const uint8_t MAG_OUT = 1;
static const uint8_t SD_EN = 45;
static const uint8_t SD_CS = 46;
static const uint8_t USB_SENSE = 34;
static const uint8_t LED_BLUE = 33;
static const uint8_t LED_RED = 13;
static const uint8_t RTC_POWER = 41;

static const uint8_t SDA = 3;
static const uint8_t SCL = 4;

static const uint8_t SS = 42;
static const uint8_t MOSI = 35;
static const uint8_t SCK = 36;
static const uint8_t MISO = 37;

static const uint8_t A0 = 18;
static const uint8_t A1 = 17;
static const uint8_t A2 = 16;
static const uint8_t A3 = 15;
static const uint8_t A4 = 14;
static const uint8_t A5 = 8;
static const uint8_t A6 = 3;
static const uint8_t A7 = 4;
static const uint8_t A8 = 5;
static const uint8_t A9 = 6;
static const uint8_t A10 = 9;
static const uint8_t A11 = 10;
static const uint8_t A12 = 11;
static const uint8_t A13 = 12;
static const uint8_t A14 = 13;

static const uint8_t T3 = 3;
static const uint8_t T4 = 4;
static const uint8_t T5 = 5;
static const uint8_t T6 = 6;
static const uint8_t T8 = 8;
static const uint8_t T9 = 9;
static const uint8_t T10 = 10;
static const uint8_t T11 = 11;
static const uint8_t T12 = 12;
static const uint8_t T13 = 13;
static const uint8_t T14 = 14;

#endif /* Pins_Arduino_h */
