{% for room in rooms %}
{% if room.button_ieee %}
### {{ room.name }} ###
- alias: "{{ room.name }}: Button"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: {{ room.button_ieee }}
        command: toggle
  action:
    - service: input_select.select_option
      target:
        entity_id: input_select.active_room
      data:
        option: "{{ room.id }}"
{% endif %}
{% endfor %}
