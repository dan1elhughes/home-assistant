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
    - choose:
        - conditions:
            - condition: state
              entity_id: sun.sun
              state: "above_horizon"
          sequence:
            - scene: {{ button.short_day }}
        - conditions:
            - condition: state
              entity_id: sun.sun
              state: "below_horizon"
          sequence:
            - scene: {{ button.short_night }}

{% if button.long %}
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
{% endif %}

{% endfor %}
