{% for room in rooms %}
{% if room.plants %}
{% for plant in room.plants %}
### {{ plant.entity }} ###
- alias: "Plant monitor: {{ plant.entity }}"
  mode: single
  trigger:
    - platform: state
      entity_id: "{{ plant.entity }}"
  action:
    - choose:
        - conditions:
            - condition: template
              value_template: '{% raw %}{{ state_attr("{% endraw %}{{ plant.entity }}{% raw %}","moisture_status") == "High" }}{% endraw %}'
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ plant.indicator }}"
              data:
                effect: "None"
                rgb_color: [0, 0, 255]
                brightness_pct: 100

        - conditions:
            - condition: state
              entity_id: "{{ plant.entity }}"
              state: "problem"
          sequence:
            - service: light.turn_on
              target:
                entity_id: "{{ plant.indicator }}"
              data:
                effect: "Slow Pulse"
                rgb_color: [255, 193, 141]
                brightness_pct: 100

        - conditions:
            - condition: state
              entity_id: "{{ plant.entity }}"
              state: "ok"
          sequence:
            - service: light.turn_off
              target:
                entity_id: "{{ plant.indicator }}"
{% endfor %}
{% endif %}
{% endfor %}
