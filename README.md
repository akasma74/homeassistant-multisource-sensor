# homeassistant: multisource sensor  

## Intro  
This sensor is based on [`Min/Max`](https://www.home-assistant.io/integrations/min_max/) sensor,  
which is very useful to compute one value based on a number of related values.  
The main problem with the Min/Max sensor was that its state is always numerical as it keeps the  
last numerical (i.e not `unknown`/`unavailable`) state of its entities according to the docs.  
Therefore its state won't be `unknown` even if all of its entities' states are `unknown` and one needs  
to take their own measures to react to such situation as per this [discussion](https://github.com/home-assistant/home-assistant/pull/29863#issuecomment-566447859).  
This can be done using automations and additional entities, but it won't be as flexible as  
a custom component.  
On the other hand, there is always a risk when using custom component as if something changes in  
a way Home Assistant handles them, you're in troubles.  
So you've been warned.

## Description  
Definition of the sensor is similar to [`Min/Max`](https://www.home-assistant.io/integrations/min_max/) sensor.
It inherits its sources' `icon` and `unit_of_measurement` (which defaults to `ERR` if they mismatch across sources).

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
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; List of sensors to combine.  
&nbsp;  
<a id="sensors-name-selectable_sources"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **selectable_sources**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(boolean) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If `true`, each source will be considered only if a corresponding [`selector`](#sensors-name-selectors) is `on`.  
&nbsp;  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _Default value:_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; false  
&nbsp;  
<a id="sensors-name-selectors"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **selectors**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(list) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; List of `input_boolean`s.  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If present, number of items should be equal to `sources`' one.  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; Otherwise you should have configured `input_booleans` so  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; for each `source_x` there is an `input_boolean.source_x_selected`.  
&nbsp;  
<a id="sensors-name-round_digits"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **round_digits**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(number) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; Number of digits to round the value of sensor.  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; If omitted, state of the sensor will be a copy of the source's state (i.e no change).  
&nbsp;  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _Default value:_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; -1  
&nbsp;  
<a id="sensors-name-friendly_name"></a>
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; **friendly_name**  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; _(string) (Optional)_  
&nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; &nbsp;&nbsp;&nbsp; Human friendly name of sensor.  
&nbsp;  

## Installation  
Copy `custom_components/multisource` folder into your `<HA config>/custom_components/` folder.
You may need to restart Home Assistant.

## Use  
1. Simple case - one physical sensor and two receivers ([RFLink](http://www.rflink.nl/blog2/) and [OMG Pilight](https://github.com/1technophile/OpenMQTTGateway)).  
Each of them has its own sensor in Home Assistant. Wwe combine them to get the last arrived reading:   
```yaml
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

2. Using these sensors as sources, we can now create a combined sensor whose state represents  
the minimal value of its sources. We also use `round_digits` to set resulting precision:  
```yaml
- platform: multisource
  sensors:
    composite_temperature:
      friendly_name: composite temperature
      type: min
      round_digits: 1
```

3. Any `multisource` sensor can be configured to enable/disable its sources (which might be  
useful to exclude some of them either manually or by an automation)  
```yaml
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
```yaml
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
