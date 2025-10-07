{% for sensor in co2_sensors %}
### CO2 Monitoring: {{ sensor }} - Red Alert ###
- alias: "CO2 Monitoring: {{ sensor }} - Red Alert"
  mode: single
  trigger:
    - platform: state
      entity_id: sensor.{{ sensor }}_co2
  condition:
    - condition: numeric_state
      entity_id: sensor.{{ sensor }}_co2
      above: "input_number.co2_red_threshold"
  action:
    - service: light.turn_on
      target:
        entity_id: light.{{ sensor }}_rgb_light
      data:
        color_name: red
        brightness_pct: 100
        effect: "Slow Pulse"

### CO2 Monitoring: {{ sensor }} - Yellow Warning ###
- alias: "CO2 Monitoring: {{ sensor }} - Yellow Warning"
  mode: single
  trigger:
    - platform: state
      entity_id: sensor.{{ sensor }}_co2
  condition:
    - condition: numeric_state
      entity_id: sensor.{{ sensor }}_co2
      above: "input_number.co2_yellow_threshold"
      below: "input_number.co2_red_threshold"
  action:
    - service: light.turn_on
      target:
        entity_id: light.{{ sensor }}_rgb_light
      data:
        color_name: yellow
        brightness_pct: 100
        effect: "Slow Pulse"
### CO2 Monitoring: {{ sensor }} - Normal ###
- alias: "CO2 Monitoring: {{ sensor }} - Normal"
  mode: single
  trigger:
    - platform: state
      entity_id: sensor.{{ sensor }}_co2
  condition:
    - condition: numeric_state
      entity_id: sensor.{{ sensor }}_co2
      below: "input_number.co2_yellow_threshold"
  action:
    - service: light.turn_off
      target:
        entity_id: light.{{ sensor }}_rgb_light
{% endfor %}
