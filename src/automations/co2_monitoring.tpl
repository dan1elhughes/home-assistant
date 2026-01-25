{% for room in rooms %}
{% if room.co2_sensor %}
### CO2 Monitoring: {{ room.name }} - Red Alert ###
- alias: "CO2 Monitoring: {{ room.name }} - Red Alert"
  mode: single
  trigger:
    - platform: state
      entity_id: sensor.{{ room.co2_sensor }}_co2
  condition:
    - condition: numeric_state
      entity_id: sensor.{{ room.co2_sensor }}_co2
      above: "input_number.co2_red_threshold"
  action:
    - service: light.turn_on
      target:
        entity_id: light.{{ room.co2_sensor }}_rgb_light
      data:
        color_name: red
        brightness_pct: 100

### CO2 Monitoring: {{ room.name }} - Yellow Warning ###
- alias: "CO2 Monitoring: {{ room.name }} - Yellow Warning"
  mode: single
  trigger:
    - platform: state
      entity_id: sensor.{{ room.co2_sensor }}_co2
  condition:
    - condition: numeric_state
      entity_id: sensor.{{ room.co2_sensor }}_co2
      above: "input_number.co2_yellow_threshold"
      below: "input_number.co2_red_threshold"
  action:
    - service: light.turn_on
      target:
        entity_id: light.{{ room.co2_sensor }}_rgb_light
      data:
        color_name: yellow
        brightness_pct: 100

### CO2 Monitoring: {{ room.name }} - Normal ###
- alias: "CO2 Monitoring: {{ room.name }} - Normal"
  mode: single
  trigger:
    - platform: state
      entity_id: sensor.{{ room.co2_sensor }}_co2
  condition:
    - condition: numeric_state
      entity_id: sensor.{{ room.co2_sensor }}_co2
      below: "input_number.co2_yellow_threshold"
  action:
    - service: light.turn_off
      target:
        entity_id: light.{{ room.co2_sensor }}_rgb_light
{% endif %}
{% endfor %}
