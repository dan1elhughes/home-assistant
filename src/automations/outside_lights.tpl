- alias: "Front lights at sunset"
  mode: single
  trigger:
    - platform: sun
      event: sunset
  condition:
{%- for person in people if person != 'person.guest' %}
    - condition: state
      entity_id: {{ person }}
      state: home
{%- endfor %}
  action:
    - service: light.turn_on
      target:
        entity_id: light.front_lights
      data:
        brightness_pct: 100

- alias: "Front lights off"
  mode: single
  trigger:
    - platform: time
      at: "23:30:00"
    - platform: state
      entity_id:
{%- for person in people %}
        - {{ person }}
{%- endfor %}
      from: not_home
      to: home
      for:
        minutes: 5
  condition:
    - condition: state
      entity_id: light.front_lights
      state: "on"
  action:
    - service: light.turn_off
      target:
        entity_id: light.front_lights
