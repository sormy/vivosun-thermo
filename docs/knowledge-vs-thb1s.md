# Knowledge for VS-THB1S

## Model

VIVOSUN AeroLab Hygrometer Thermometer

MODEL: VS-THB1S

## Authentication

1. Only one simultaneous connection.
2. Connection during pairing period authenticates for later access.

## Commands

There are two characteristics used to send commands and retrieve results:

1. 0000fff5-0000-1000-8000-00805f9b34fb - command UUID (write only)
2. 0000fff3-0000-1000-8000-00805f9b34fb - result UUID (notify only)

Every result reply is prefixed with single or two byte command code. Some commands assume one reply,
some (like history) can send a lot of replies.

## Command 0D

This command retrieves current status and includes temperature in Celcius, humidity and some other
values.

Example response:

```
00000000: 0D 81 01 A8 02 AC 00 5E  01 BF 02 93 00 00 00 00  .......^........
00000010: 00 00 00 00                                       ....
```

C-struct definition of response format:

```c
#pragma pack(push, 1)
typedef struct {
    uint8_t command_code;           // Command Code = 0D
    int16_t temp_c;                 // Main sensor temperature in °C, scaled up x16
    int16_t humidity;               // Main sensor humidity, scaled up x16
    int16_t unknown1;
    int16_t ext_probe_temp;         // External probe temperature in °C, scaled up x16
    int16_t ext_probe_humidity;     // External probe humidity, scaled up x16
    int16_t unknown2;
    uint8_t reserved[8];
} SensorData;
#pragma pack(pop)
```

## Command 25

Designation is unknown.

Example response:

```
00000000: 25 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  %...............
00000010: 00 00 00 00
```

## Command 1000

Designation is unknown.

Example response:

```
00000000: 10 00 02 77 06 00 00 00  00 00 00 00 00 00 00 00  ...w............
00000010: 00 00 00 00
```

## Command 1100

Seems like this command requests history for main sensor with optional range.

This command has some arguments, for example, "1100 2300 D002", but just "1100" also works.

Example response (every 20 byte packet is padded to 32 bytes):

```
00000000: 11 00 BC 05 5C 01 94 02  00 03 00 05 00 03 01 00  ....\...........
00000010: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000020: 11 00 C3 05 5D 01 9F 02  00 FF 00 02 00 01 00 00  ....]...........
00000030: 00 00 01 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000040: 11 00 CA 05 5D 01 A1 02  00 01 00 01 00 00 00 02  ....]...........
00000050: 00 00 00 01 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000060: 11 00 D1 05 5D 01 A7 02  00 01 00 01 00 FF 00 01  ....]...........
00000070: 00 FE 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000080: 11 00 D8 05 5D 01 AA 02  00 00 00 01 FF 03 01 00  ....]...........
00000090: 00 00 FF 02 00 00 00 00  00 00 00 00 00 00 00 00  ................
000000A0: 11 00 DF 05 5C 01 B2 02  00 03 00 01 00 00 00 03  ....\...........
000000B0: 00 00 FF 02 00 00 00 00  00 00 00 00 00 00 00 00  ................
000000C0: 11 00 E6 05 5C 01 BC 02  00 01 FF 01 00 01 00 01  ....\...........
000000D0: 00 00 00 01 00 00 00 00  00 00 00 00 00 00 00 00  ................
000000E0: 11 00 ED 05 5B 01 C2 02  00 02 FF 01 00 01 00 03  ....[...........
000000F0: 00 03 00 03 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000100: 11 00 F4 05 5A 01 D2 02  00 01 01 01 FF 02 00 01  ....Z...........
00000110: 00 00 00 02 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000120: 11 00 FB 05 5A 01 DA 02  00 FF 00 01 00 00 00 00  ....Z...........
00000130: 01 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000140: 11 00 02 06 5B 01 DA 02  00 01 00 00 FF 00 01 00  ....[...........
00000150: FF 00 01 04 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000160: 11 00 09 06 5C 01 DB 02  00 FF 00 FE FF 00 00 01  ....\...........
00000170: 00 FD 00 FF 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000180: 11 00 10 06 5B 01 D5 02  00 FF FF 00 01 02 FF FF  ....[...........
00000190: 01 FF FF 01 00 00 00 00  00 00 00 00 00 00 00 00  ................
000001A0: 11 00 17 06 5A 01 D3 02  01 00 FF 00 01 01 FF FE  ....Z...........
000001B0: 00 01 00 FF 00 00 00 00  00 00 00 00 00 00 00 00  ................
000001C0: 11 00 1E 06 5A 01 D2 02  00 FE 00 01 00 02 02 4E  ....Z..........N
000001D0: 04 FC 02 C4 00 00 00 00  00 00 00 00 00 00 00 00  ................
000001E0: 11 00 25 06 63 01 D2 02  02 14 05 D8 01 F5 00 00  ..%.c...........
000001F0: FF FE 00 FC 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000200: 11 00 2C 06 6A 01 B2 02  00 FF 03 5E 09 9A FD 03  ..,.j......^....
00000210: FE FD FF 03 00 00 00 00  00 00 00 00 00 00 00 00  ................
00000220: 11 00 33 06 6E 01 AD 02  00 00 00 00 00 00 00 00  ..3.n...........
00000230: 00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  ................
```

C-struct definition of response format:

```c
#pragma pack(push, 1)
typedef struct {
    uint16_t command_code;          // Command Code = 1100
    uint16_t unknown1;              // Some kind of ID of record in log
    int16_t temp_c;                 // Temperature in °C, scaled up x16
    int16_t humidity;               // Humidity, scaled up x16
    uint8_t unknown2[12];
} SensorData;
#pragma pack(pop)
```

## Command 1101

Seems like this command requests history for external probe with optional range.

Format is similar to command 1100.
