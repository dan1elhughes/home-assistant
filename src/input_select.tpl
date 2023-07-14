heating_mode:
  name: Heating mode
  options:
    - away
    - sleep
    - home
    - comfort
    - activity
  icon: mdi:home-thermometer
active_room:
  name: Active room
  icon: mdi:door-sliding
  options:
    {% for room in rooms -%}
    - {{ room.id }}
    {% endfor %}
