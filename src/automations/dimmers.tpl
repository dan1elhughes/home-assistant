{% for room in rooms %}
{% if room.dimmer_ieee %}
### {{ room.name }} ###
- alias: "{{ room.name }} dimmer: Track active room"
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

- alias: "{{ room.name }} dimmer: Power (short)"
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
        brightness: 255

- alias: "{{ room.name }} dimmer: Power (long)"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
        command: on_hold
  action:
    - service: light.turn_off
      target:
        entity_id: "{{ room.lights }}"

- alias: "{{ room.name }} dimmer: Up"
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

- alias: "{{ room.name }} dimmer: Down"
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

{% if room.fan %}
- alias: "{{ room.name }} dimmer: Hue"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
        command: off_press
  action:
    - service: fan.toggle
      target:
        entity_id: "{{ room.fan }}"
{% endif %}
{% endif %}
{% endfor %}
