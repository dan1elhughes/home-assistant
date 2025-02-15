{% import './macros/lights.tpl' as lights with context %}

# PRESENCE
presence_home:
  name: "People"
  entities:
    {% for person in people -%}
    - {{ person }}
    {% endfor %}

# CEILING LIGHTS
ceiling_lights:
  name: "Ceiling lights"
  entities:
    {% for room in rooms -%}
    {% for light_id in room.ceiling -%}
    - {{ light_id }}
    {% endfor -%}
    {% endfor %}

room_lights:
  name: "Room lights"
  entities:
    {{- lights.ids() | indent(4) }}
