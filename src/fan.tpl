- platform: group
  name: "Fans"
  entities:
  {% for room in rooms -%}
  {% if room.fan -%}
    - {{ room.fan }}
  {% endif -%}
  {% endfor -%}
