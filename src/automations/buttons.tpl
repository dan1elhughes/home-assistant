{% for button in buttons %}
### {{ button.name }} ###
- alias: "{{ button.name }}: Short (day)"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
        command: on_short_release
  condition:
    - condition: state
      entity_id: sun.sun
      state: "above_horizon"
  action:
    - scene: {{ button.short_day }}
- alias: "{{ button.name }}: Short (night)"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
        command: on_short_release
  condition:
    - condition: state
      entity_id: sun.sun
      state: "below_horizon"
  action:
    - scene: {{ button.short_night }}
- alias: "{{ button.name }}: Long"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
        command: on_long_release
  action:
    - scene: {{ button.long }}

{% endfor %}
