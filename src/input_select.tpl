active_room:
  name: Active room
  icon: mdi:door-sliding
  options:
    {% for room in rooms|sort(attribute='id') -%}
    - {{ room.id }}
    {% endfor %}
    - out

charger_mode:
  name: Charger mode
  icon: mdi:car-electric
  options:
    - Fast
    - ID3
    - Zoe
    - "Off"

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
