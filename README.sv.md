# BFOUR BLE

Home Assistant-integration för BFOUR:s trådlösa stektermometrar (BF-70, BF-80).

Proberna läses **passivt** från annonseringarna. Ingen anslutning, ingen dedikerad
ESP32, inget moln. Alla Bluetooth-proxies i hemmet matar samma integration, så
täckningen är lika god som din BLE-täckning i övrigt — och basstationen kan
användas parallellt, eller ligga kvar i lådan.

## Installation

Lägg till repot som custom repository i HACS, eller kopiera
`custom_components/bfour_ble/` till din `config/custom_components/`. Starta om
Home Assistant.

Ta proberna ur basstationen så att de vaknar. De dyker upp som upptäckta enheter
inom någon minut. En config entry per probe.

## Entiteter

Per probe:

| Entitet | Typ | Beskrivning |
|---|---|---|
| Kärntemperatur | sensor | Sensorn i spetsen |
| Omgivningstemperatur | sensor | Sensorn vid handtaget |
| Batterispänning | sensor | Diagnostik |
| Aktiv | binary_sensor | Statusflagga, se nedan |

## Protokoll

Proben annonserar connectable legacy-adverts med service-UUID `0xFFA0` och
manufacturer data under company-ID `0x1002`. Payloaden är 14 bytes:

```
83 CE ED AC 4E C3 A4  F3 00  04 01  63 0E  80
|  \_______________/  \___/  \___/  \___/  |
|   MAC, omvänd        24.3   26.0   3.683  status
header
```

Alla tre värdena är little-endian uint16. Temperaturerna i tiondels grader,
batteriet i millivolt.

`0x1002` är en **reserverad, ej tilldelad** company-ID som används av många
billiga BLE-moduler. Integrationen validerar därför att byte 1–6 speglar
avsändarens MAC-adress innan paketet accepteras. Utan den kontrollen plockar
matchningen upp orelaterade enheter.

Konsekvensen är att andra enheter som sänder under samma company-ID kan dyka
upp som upptäckter och sedan avbrytas med *"Enheten är inte en BFOUR-probe"*.
Det är väntat beteende, inte ett fel: matchningen i `manifest.json` sker på
company-ID, och valideringen sker först på paketets innehåll. Alternativet vore
att även kräva namnet `Probe`, men det ligger i scan response och kommer inte
med vid passiv skanning — då hade inga probes hittats alls.

## Kända egenheter

**Omgivningssensorn har en undre tröskel** runt 20 °C. Basstationen visar `Loo`
under den; integrationen publicerar `None` så att historiken får ett hål
istället för en falsk linje. Sensorn är byggd för grill- och ugnstemperaturer
och bör inte användas som rumstermometer.

**Statusflaggan** är bit 7 i sista byten. Den växlade på båda proberna samtidigt
när en tillagningssession startades i appen, men tolkningen är inte bekräftad —
den kan lika gärna betyda "ur laddaren" eller "vaken". Lägg en probe i
basstationen och se om biten nollställs.

**Batterispänningen** är rå cellspänning, inte procent. Kyla sänker den
tillfälligt, så en probe som legat i kylskåpet visar lägre värde än den
egentligen står för. Mappning till procent kräver en urladdningskurva som ingen
har mätt upp än.

## Tester

```
python3 tests/test_parser.py
```

Parsertesterna kör mot verkliga paket från en BF-80, verifierade mot både
displayen och tillverkarens app. 
Måltemperaturer, förvarningar och hålltid ligger i en separat integration,
[ha-cooking](https://github.com/danielholm/ha-cooking), som fungerar på vilken
temperatursensor som helst.

## Tack

Protokollstrukturen för den äldre, anslutningsbaserade generationen (BF-60,
service `0xFFB0`) är kartlagd i
[wizbowes/BFour-ESPHome](https://github.com/wizbowes/BFour-ESPHome).
BF-70/BF-80-proberna annonserar istället passivt under `0xFFA0`, vilket gör dem
enklare att läsa.
