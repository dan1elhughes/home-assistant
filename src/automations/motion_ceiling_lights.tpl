{% for room in rooms %}
{% if room.motion_sensor %}
### {{ room.name }} ###
- alias: "{{ room.name }}: Motion on"
  mode: single
  trigger:
    - platform: state
      entity_id: "{{ room.motion_sensor }}"
      to: "on"
  condition:
    - condition: state
      entity_id: input_boolean.motion_sensors_enabled
      state: "on"
  actions:
    - choose:
        - conditions:
            - condition: sun
              after: sunrise
              before: sunset
          sequence:
            - action: light.turn_on
              entity_id:
              {% for light_id in room.ceiling %}
                - {{ light_id }}
              {% endfor %}
              data:
                  brightness_pct: 100
      default:
        - action: light.turn_on
          entity_id:
          {% for light_id in room.ceiling %}
            - {{ light_id }}
          {% endfor %}
          data:
              brightness_pct: 5
- alias: "{{ room.name }}: Motion off"
  mode: single
  trigger:
    - platform: state
      entity_id: "{{ room.motion_sensor }}"
      to: "off"
      for:
        minutes: 1
  condition:
    - condition: state
      entity_id: input_boolean.motion_sensors_enabled
      state: "on"
  actions:
    - action: light.turn_off
      entity_id:
      {% for light_id in room.ceiling %}
        - {{ light_id }}
      {% endfor %}
{% endif %}
{% endfor %}
