{% for room in rooms %}
### {{ room.name }} ###
- alias: "{{ room.name }}: One-room mode (activate)"
  mode: single
  trigger:
    - platform: state
      entity_id: input_select.active_room
      to: "{{room.id}}"
  condition:
    - condition: state
      entity_id: input_boolean.one_room_mode
      state: "on"
  action:
    {% if room.lights -%}
    - service: light.turn_on
      target:
        entity_id:
          - {{ room.lights }}
    {%- endif -%}
    {%- if room.heater %}
    - service: climate.set_hvac_mode
      target:
        entity_id: climate.{{room.id}}
      data:
        hvac_mode: "heat"
    {%- endif %}

- alias: "{{ room.name }}: One-room mode (deactivate)"
  mode: single
  trigger:
    - platform: state
      entity_id: input_select.active_room
      not_to: "{{room.id}}"
  condition:
    - condition: state
      entity_id: input_boolean.one_room_mode
      state: "on"
  action:
    {% if room.lights -%}
    - service: light.turn_off
      target:
        entity_id:
          - {{ room.lights }}
    {%- endif -%}
    {%- if room.heater %}
    - service: climate.set_hvac_mode
      target:
        entity_id: climate.{{room.id}}
      data:
        hvac_mode: "off"
    {%- endif %}
{% endfor %}
