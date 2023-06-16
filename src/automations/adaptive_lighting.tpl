- alias: "Adaptive lighting: change"
  mode: single
  trigger:
    - platform: state
      entity_id:
        - switch.adaptive_lighting_lighting
      attribute: color_temp_kelvin
  action:
    - service: adaptive_lighting.apply
      data:
        entity_id: switch.adaptive_lighting_lighting
        adapt_color: true
        adapt_brightness: false
        turn_on_lights: false
        lights:
        {% for light in lights -%}
        - {{ light }}
        {% endfor %}

- alias: "Adaptive lighting: on"
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
      data:
        entity_id: switch.adaptive_lighting_lighting
        adapt_color: true
        adapt_brightness: false
        turn_on_lights: false
        lights:
          - "{% raw %}{{ trigger.entity_id }}{% endraw %}"
