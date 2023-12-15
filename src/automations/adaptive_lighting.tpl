{% import '../macros/lights.tpl' as lights with context %}

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
        {{- lights.ids() | indent(10) }}

- alias: "Adaptive lighting: on"
  mode: queued
  trigger:
    - platform: state
      to: "on"
      entity_id:
        {{- lights.ids() | indent(8) }}
  action:
    - service: adaptive_lighting.apply
      data:
        entity_id: switch.adaptive_lighting_lighting
        adapt_color: true
        adapt_brightness: false
        turn_on_lights: false
        lights:
          - "{% raw %}{{ trigger.entity_id }}{% endraw %}"
