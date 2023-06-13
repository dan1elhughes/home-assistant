{% for room in rooms %}
{% if room.dimmer_ieee %}
### {{ room.name }} ###
- alias: "{{ room.name }}: Track active room"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
  action:
    - service: input_select.select_option
      target:
        entity_id: input_select.active_room
      data:
        option: "{{ room.id }}"

- alias: "{{ room.name }}: On"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
        command: on_press
  action:
    - service: light.turn_on
      target:
        entity_id: "{{ room.lights }}"
      data:
        brightness_pct: 100

{% if room.fan %}
- alias: "{{ room.name }}: Double-tap"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
        command: on_double_press
  action:
    - service: fan.toggle
      target:
        entity_id: "{{ room.fan }}"
{% endif %}

- alias: "{{ room.name }}: Up"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
        command: up_press
  action:
    - service: light.turn_on
      target:
        entity_id: "{{ room.lights }}"
      data:
        brightness_step_pct: 20

- alias: "{{ room.name }}: Down"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
        command: down_press
  action:
    - service: light.turn_on
      target:
        entity_id: "{{ room.lights }}"
      data:
        brightness_step_pct: -20

- alias: "{{ room.name }}: Off"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
        command: off_press
  action:
    - service: light.turn_off
      target:
        entity_id: "{{ room.lights }}"
{% endif %}
{% endfor %}
