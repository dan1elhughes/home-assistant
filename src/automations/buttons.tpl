{% for button in buttons %}
- alias: "{{ button.name }}: Toggle"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
        command: on_short_release
  action:
    service: light.toggle
    target:
      entity_id: {{ button.toggle }}
- alias: "Bedroom: Long-hold scene"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ button.ieee }}
        command: on_long_release
  action:
    - scene: {{ button.scene }}
{% endfor %}
