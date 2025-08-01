active_room:
  name: Active room
  icon: mdi:door-sliding
  options:
    {% for room in rooms -%}
    - {{ room.id }}
    {% endfor %}
    - out

battery_mode:
  name: Battery mode
  icon: mdi:home-battery
  options:
    - Idle
    - Charge
    - Discharge
