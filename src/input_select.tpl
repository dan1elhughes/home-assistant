active_room:
  name: Active room
  icon: mdi:door-sliding
  options:
    {% for room in rooms -%}
    - {{ room.id }}
    {% endfor %}
