{% for room in rooms %}
{% if room.lights %}
### {{ room.name }} ###
- alias: "{{ room.name }}: One-room mode (activate)"
  mode: single
  trigger:
    - platform: state
      entity_id: input_select.active_room
      to: "{{ room.id }}"
  action:
    - service: light.turn_on
      target:
        entity_id:
          - {{ room.lights }}

- alias: "{{ room.name }}: One-room mode (deactivate)"
  mode: single
  trigger:
    - platform: state
      entity_id: input_select.active_room
      not_to: "{{ room.id }}"
  condition:
    - condition: state
      entity_id: binary_sensor.one_room_mode
      state: "on"
  action:
    - service: light.turn_off
      target:
        entity_id:
          - {{ room.lights }}
{%- endif -%}
{% endfor %}
