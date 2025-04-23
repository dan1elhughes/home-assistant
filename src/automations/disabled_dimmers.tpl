{% for light_id in disabled_dimmers %}
- alias: "{{ light_id }}: Set 100% brightness"
  mode: single
  trigger:
    - platform: state
      entity_id: "{{ light_id }}"
      to: "on"
  actions:
    - action: light.turn_on
      entity_id:
        - {{ light_id }}
      data:
          brightness_pct: 100
{% endfor %}
