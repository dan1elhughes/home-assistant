{% for room in rooms %}
{% if room.motion_sensor %}
### {{ room.name }} ###
- alias: "{{ room.name }}: Motion"
  mode: single
  trigger:
    - platform: state
      entity_id: "{{ room.motion_sensor }}"
      from: null
  actions:
    - choose:
      - conditions:
          - condition: state
            entity_id: {{ room.motion_sensor }}
            state: "on"
        sequence:
          - action: light.turn_on
            entity_id:
            {% for light_id in room.ceiling %}
              - {{ light_id }}
            {% endfor %}
            data:
                brightness_pct: 5
      - conditions:
          - condition: state
            entity_id: {{ room.motion_sensor }}
            state: "off"
        sequence:
          - action: light.turn_off
            entity_id:
            {% for light_id in room.ceiling %}
              - {{ light_id }}
            {% endfor %}
{% endif %}
{% endfor %}
