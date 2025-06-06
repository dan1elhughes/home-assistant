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
      value_template: "{% raw %}{{ trigger.event.data.command in ['on_press', 'on_hold', 'up_hold', 'down_hold', 'off_press'] }}{% endraw %}"
  action:
    - service: input_select.select_option
      target:
        entity_id: input_select.active_room
      data:
        option: "{{ room.id }}"
    - choose:
        - conditions: "{% raw %}{{ trigger.event.data.command == 'on_press' }}{% endraw %}"
          alias: "On (press)"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ room.lights }}"
              data:
                brightness: 255

        {% if room.custom_scene %}
        - conditions: "{% raw %}{{ trigger.event.data.command == 'on_hold' }}{% endraw %}"
          alias: "Scene"
          sequence:
            - service: scene.turn_on
              target:
                entity_id: "{{ room.custom_scene }}"
        {% endif %}

        - conditions: "{% raw %}{{ trigger.event.data.command == 'up_hold' }}{% endraw %}"
          alias: "Up"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ room.lights }}"
              data:
                brightness_step_pct: 20

        - conditions: "{% raw %}{{ trigger.event.data.command == 'down_hold' }}{% endraw %}"
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
