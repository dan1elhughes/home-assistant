{% for dimmer in dimmers %}
### {{ dimmer.name }} ###
- alias: "{{ dimmer.name }}: On"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ dimmer.ieee }}"
        command: on_press

  action:
    - choose:
        - conditions:
            - condition: state
              entity_id: sun.sun
              state: "above_horizon"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ dimmer.group }}"
              data:
                brightness_pct: 100
                color_temp: 300
        - conditions:
            - condition: state
              entity_id: sun.sun
              state: "below_horizon"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ dimmer.group }}"
              data:
                brightness_pct: 100
                color_temp: 500

- alias: "{{ dimmer.name }}: Long-press"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ dimmer.ieee }}"
        command: on_hold
  action:
    - scene: {{ dimmer.scene }}

{% if dimmer.fan %}
- alias: "{{ dimmer.name }}: Double-tap"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ dimmer.ieee }}"
        command: on_double_press
  action:
    service: fan.toggle
    target:
      entity_id: "{{ dimmer.fan }}"
{% endif %}

- alias: "{{ dimmer.name }}: Up"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ dimmer.ieee }}"
        command: up_press
  action:
    service: light.turn_on
    target:
      entity_id: "{{ dimmer.group }}"
    data:
      brightness_step_pct: 20

- alias: "{{ dimmer.name }}: Down"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ dimmer.ieee }}"
        command: down_press
  action:
    service: light.turn_on
    target:
      entity_id: "{{ dimmer.group }}"
    data:
      brightness_step_pct: -20

- alias: "{{ dimmer.name }}: Off"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ dimmer.ieee }}"
        command: off_press
  action:
    service: light.turn_off
    target:
      entity_id: "{{ dimmer.group }}"

{% endfor %}
