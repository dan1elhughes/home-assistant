{% for room in rooms %}
{% if room.dimmer_ieee %}
### {{ room.name }} ###
- alias: "{{ room.name }} dimmer"
  mode: single
  trigger:
    - platform: event
      event_type: zha_event
      event_data:
        device_ieee: "{{ room.dimmer_ieee }}"
  condition:
    - condition: template
      value_template: "{% raw %}{{ trigger.event.data.command in ['on_short_release', 'on_hold', 'up_press', 'down_press', 'off_press'] }}{% endraw %}"
  action:
    - service: input_select.select_option
      target:
        entity_id: input_select.active_room
      data:
        option: "{{ room.id }}"
    - choose:
        - conditions: "{% raw %}{{ trigger.event.data.command == 'on_short_release' }}{% endraw %}"
          alias: "On (press)"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ room.lights }}"
              data:
                brightness: 255

        - conditions: "{% raw %}{{ trigger.event.data.command == 'on_hold' }}{% endraw %}"
          alias: "On (hold)"
          sequence:
            - service: light.turn_off
              target:
                entity_id: "{{ room.lights }}"

        - conditions: "{% raw %}{{ trigger.event.data.command == 'up_press' }}{% endraw %}"
          alias: "Up"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ room.lights }}"
              data:
                brightness_step_pct: 20

        - conditions: "{% raw %}{{ trigger.event.data.command == 'down_press' }}{% endraw %}"
          alias: "Down"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ room.lights }}"
              data:
                brightness_step_pct: -20

        - conditions: "{% raw %}{{ trigger.event.data.command == 'off_press' }}{% endraw %}"
          alias: "Hue"
          sequence:
            - service: light.turn_off
              target:
                entity_id: "{{ room.lights }}"
{% endif %}
{% endfor %}
