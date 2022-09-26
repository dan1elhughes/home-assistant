{% for button in buttons %}
### {{ button.name }} ###
- alias: "{{ button.name }}: Short"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
        command: on_short_release
  action:
    - scene: {{ button.short }}
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
