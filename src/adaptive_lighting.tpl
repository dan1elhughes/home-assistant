{% import './macros/lights.tpl' as lights with context %}

- name: "default"
  lights:
    {{- lights.ids() | indent(4) }}
