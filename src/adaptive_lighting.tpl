{% import './macros/lights.tpl' as lights with context %}

- name: "default"
  lights:
    {{- lights.ids() | indent(4) }}
  autoreset_control_seconds: 5
  transition: 5
