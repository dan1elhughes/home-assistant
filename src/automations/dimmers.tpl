{% for dimmer in dimmers %}
### {{ dimmer.name }} ###
- alias: "{{ dimmer.name }}: On"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ dimmer.ieee }}"
        command: on_short_release
  action:
    service: light.turn_on
    target:
      entity_id: "{{ dimmer.group }}"
    data:
      brightness_pct: 100
      color_temp: 500
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
