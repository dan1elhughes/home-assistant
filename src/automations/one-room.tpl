{% for room in rooms %}
### {{ room.name }} ###
- alias: "{{ room.name }}: One-room mode (activate)"
  mode: single
  trigger:
    - platform: state
      entity_id: input_select.active_room
      to: "{{ room.id }}"
  condition:
    - condition: state
      entity_id: sensor.one_room_mode
      state: "True"
  action:
    {% if room.lights -%}
    - service: light.turn_on
      target:
        entity_id:
          - {{ room.lights }}
    {%- endif -%}
    {%- if room.fan %}
    - alias: "Automate fans"
      if:
      - condition: state
        entity_id: input_boolean.automatic_fans
        state: "on"
      then:
        - service: fan.turn_on
          target:
            entity_id: {{ room.fan }}
    {%- endif %}

- alias: "{{ room.name }}: One-room mode (deactivate)"
  mode: single
  trigger:
    - platform: state
      entity_id: input_select.active_room
      not_to: "{{ room.id }}"
  condition:
    - condition: state
      entity_id: sensor.one_room_mode
      state: "True"
  action:
    {% if room.lights -%}
    - service: light.turn_off
      target:
        entity_id:
          - {{ room.lights }}
    {%- endif -%}
    {%- if room.fan %}
    - service: fan.turn_off
      target:
        entity_id: {{ room.fan }}
    {%- endif %}
{% endfor %}
