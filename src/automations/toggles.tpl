{% for toggle in toggles %}
### {{ toggle.name }} ###
- alias: "{{ toggle.name }}: Press"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ toggle.ieee }}
        command: toggle
  action:
    - service: homeassistant.toggle
      target:
        entity_id: {{ toggle.target }}
{% endfor %}
