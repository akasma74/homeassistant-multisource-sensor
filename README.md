# homeassistant: multisource sensor  

## Intro  
This sensor is based on [`Min/Max`](https://www.home-assistant.io/integrations/min_max/) sensor.  
The main reason to create it was that Min/Max sensor's value is always numerical - it stores the  
last valid (i.e not `unknown`/`unavailable` state of its entities.  
Therefore it won't become `unknown` even if all of its entities become `unknown` and one needs  
to take their own measures to react to such situation.  
This can be done using automations and additional entities, but it won't be as flexible as  
a custom component.  
On the other hand, it's always a risk when using custom component as if something changes in  
a way Home Assistant handles them, you're screwed.  
So you've been warned.

## Description  
Definition of the sensor is similar to [`Min/Max`](https://www.home-assistant.io/integrations/min_max/) sensor:

<a id="sensors"></a>
**sensors**  
&nbsp;&nbsp;&nbsp; _(list) (Required)_  
&nbsp;&nbsp;&nbsp; Configurations for individual sensors.  
&nbsp;  
<a id="sensors-name"></a>
&nbsp;&nbsp;&nbsp; **name**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(string) (Required)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; Name of sensor.  
&nbsp;  
<a id="sensors-name-type"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **type**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(string) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; The type of sensor (same as for [`Min/Max sensor`](https://www.home-assistant.io/integrations/min_max/#type)). Supported values are `min`, `last`.  
&nbsp;  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _Default value:_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; `last`  
&nbsp;  
<a id="sensors-name-sources"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **sources**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(list) (Required)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; List of sensors to combine (sources).  
&nbsp;  
<a id="sensors-name-selectable_sources"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **selectable_sources**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(boolean) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If `True`, each source will be considered only if a corresponding selector  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; is `on` (see [`selectors`](#sensors-name-selectors) for details).  
&nbsp;  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _Default value:_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; False  
&nbsp;  
<a id="sensors-name-selectors"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **selectors**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(list) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; List of selectors (`input_booleans`).  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If present, number of items should be equal to `sources`.  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; Otherwise you should have configured `input_booleans` so  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; for each `source_x` there is `input_boolean.source_x_selected`.  
&nbsp;  
<a id="sensors-name-round_digits"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **round_digits**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(number) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; Number of digits to round the value of sensor.  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If omitted (or -1), state of the sensor will be a copy of the source's state (i.e no change).  
&nbsp;  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _Default value:_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; -1  
&nbsp;  
<a id="sensors-name-friendly_name"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **friendly_name**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(string) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; Human friendly name of the sensor.  
&nbsp;  

## Use  
1. Simple case - one physical sensor and two receivers (RFLink and OMG Pilight).
Each of them has its own sensor in homeassistant. Then we combine them using last arrived reading.   
```
# these sensors reflect appropriate protocol's values
# and behave like 'last' filter but change to 'unknown' if all of the entity_id are unknown
- platform: multisource
  sensors:
    ground_floor_reception_reliable_temperature:
      friendly_name: !secret ground_floor_reception_name
      sources:
        - sensor.pilight_ground_floor_reception_temperature
        - sensor.rflink_ground_floor_reception_temperature

    ground_floor_lounge_reliable_temperature:
      friendly_name: !secret ground_floor_lounge_name
      sources:
        - sensor.pilight_ground_floor_lounge_temperature
        - sensor.rflink_ground_floor_lounge_temperature

```

2. Using these sensors (sources), we can now create a combined sensor whose value represent the minimal value of its sources  
We also use `round_digits` to set resulting precision.
```
- platform: multisource
  sensors:
    composite_temperature:
      friendly_name: composite temperature
      type: min
      round_digits: 1
```

3. Any `multisource` sensor can be configured to enable/disable its sources (which might be useful to exclude some of then either manually or by an automation):  
```
- platform: multisource
  sensors:
    composite_temperature:
      friendly_name: composite temperature
      type: min
      round_digits: 1
      selectable_sources: true
      sources:
        - sensor.ground_floor_reception_reliable_temperature
        - sensor.ground_floor_lounge_reliable_temperature

```
or
```
- platform: multisource
  sensors:
    ground_floor_reception_reliable_temperature:
      friendly_name: !secret ground_floor_reception_name
      selectable_sources: true
      sources:
        - sensor.pilight_ground_floor_reception_temperature
        - sensor.rflink_ground_floor_reception_temperature
      selectors:
        - input_boolean.pilight_ground_floor_reception
        - input_boolean.rflink_ground_floor_reception
```
