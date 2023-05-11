{% for room in rooms %}
{% if room.lights %}
### {{ room.name }} ###
- alias: "{{ room.name }}: Sunset"
  mode: single
  trigger:
    - platform: sun
      event: sunset
  condition:
    - condition: state
      entity_id: {{ room.lights }}
      state: "on"
  action:
    - service: light.turn_on
      data:
        color_temp: 500
      target:
        entity_id: {{ room.lights }}
{% endif %}
{% endfor %}
