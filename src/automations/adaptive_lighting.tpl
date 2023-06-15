- alias: "Adaptive lighting: interval"
  mode: single
  trigger:
    - platform: time_pattern
      minutes: "/10"
  action:
    - service: adaptive_lighting.apply
      data:
        entity_id: switch.adaptive_lighting_lighting
        adapt_color: true
        adapt_brightness: false
        turn_on_lights: false
        transition: 60
        lights:
        {% for light in lights -%}
        - {{ light }}
        {% endfor %}


- alias: "Adaptive lighting: boot"
  mode: single
  trigger:
    - platform: state
      to: "on"
      entity_id:
        {% for light in lights -%}
        - {{ light }}
        {% endfor %}
  action:
    - service: adaptive_lighting.apply
      data_template:
        entity_id: switch.adaptive_lighting_lighting
        adapt_color: true
        adapt_brightness: false
        turn_on_lights: false
        lights:
          - "{% raw %}{{ trigger.entity_id }}{% endraw %}"
