active_room:
  name: Active room
  icon: mdi:door-sliding
  options:
    {% for room in rooms -%}
    - {{ room.id }}
    {% endfor %}
    - out

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
