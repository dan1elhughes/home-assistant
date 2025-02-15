{% import '../macros/lights.tpl' as lights with context %}

name: Lights off
icon: mdi:ceiling-light-multiple-outline
entities:
  - group.ceiling_lights
  {{- lights.ids() | indent(2) }}
