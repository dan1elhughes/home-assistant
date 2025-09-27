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

battery_mode_v2:
  name: Battery mode V2
  icon: mdi:home-battery
  options:
    - Idle
    - Charge
    - Discharge

{% for x in multiLightDimmers %}
{{ x.id }}:
  name: {{ x.name }}
  icon: mdi:lightbulb-multiple
  options:
    - 1
    - 2
    - 3
    - 4
{% endfor %}
