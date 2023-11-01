- alias: "Heating: Morning"
  mode: single
  trigger:
    - platform: state
      entity_id: schedule.heating
      to: "on"
  condition:
    - condition: state
      entity_id: input_boolean.automations
      state: "on"
    - condition: state
      entity_id: group.presence_home
      state: home
  action:
    {%- for room in rooms %}
    {%- if room.heater %}
    - alias: "Set {{ room.name }} to Home"
      service: climate.set_preset_mode
      data:
        preset_mode: home
      target:
        entity_id: climate.{{ room.id }}
    {%- endif %}
    {%- endfor %}

- alias: "Heating: Overnight"
  mode: single
  trigger:
    - platform: state
      entity_id: schedule.heating
      to: "off"
  condition:
    - condition: state
      entity_id: input_boolean.automations
      state: "on"
  action:
    {%- for room in rooms %}
    {%- if room.heater %}
    - alias: "Set {{ room.name }} to Sleep"
      service: climate.set_preset_mode
      data:
        preset_mode: sleep
      target:
        entity_id: climate.{{ room.id }}
    {%- endif %}
    {%- endfor %}
