- alias: "Negative electricity price"
  mode: single
  trigger:
    - platform: state
      entity_id: sensor.negative_electricity_price
      to: null
  variables:
    hvac_mode: |
      {% raw %}
      {{ 'heat' if states('sensor.negative_electricity_price') == 'True' else 'off' }}
      {% endraw %}
    preset_mode: |
      {% raw %}
      {{ 'comfort' if states('sensor.negative_electricity_price') == 'True' else 'sleep' }}
      {% endraw %}
  condition:
    - condition: state
      entity_id: input_boolean.automations
      state: "on"
    - condition: state
      entity_id: input_boolean.negative_electricity_price
      state: "on"
  action:
    - parallel:
      {%- for room in rooms %}
      {%- if room.heater %}
      - alias: "{{ room.name }}"
        if:
        - alias: "If currently active room is {{ room.name }}"
          condition: state
          entity_id: input_select.active_room
          state: "{{ room.id }}"
        then:
          - alias: "Then do nothing"
            delay:
              seconds: 0
        else:
          - alias: "Otherwise enable heating in {{ room.name }}"
            parallel:
              - service: climate.set_hvac_mode
                target:
                  entity_id: climate.{{ room.id }}
                data:
                  hvac_mode: {% raw %}"{{ hvac_mode }}"{% endraw %}
              - service: climate.set_preset_mode
                target:
                  entity_id: climate.{{ room.id }}
                data:
                  preset_mode: {% raw %}"{{ preset_mode }}"{% endraw %}
      {%- endif %}
      {%- endfor %}

