name: Lights off
icon: mdi:ceiling-light-multiple-outline
entities:
  group.ceiling_lights: off

  # TODO: Move this to a macro
  {% for room in rooms -%}
  {% if room.lights -%}
  {% for id in groups[room.lights].entities -%}
  {{ id }}: off
  {% endfor -%}
  {% endif -%}
  {% endfor -%}
