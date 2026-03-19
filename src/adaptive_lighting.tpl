{% import './macros/lights.tpl' as lights with context %}

- name: "default"
  lights:
    {{- lights.ids() | indent(4) }}
    - light.garden_lighting
    - light.front_lights
  autoreset_control_seconds: 5
  transition: 5
