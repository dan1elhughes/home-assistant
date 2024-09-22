# PRESENCE
presence_home:
  name: "People"
  entities:
    {% for person in people -%}
    - {{ person }}
    {% endfor %}
